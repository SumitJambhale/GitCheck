import os
import json
import re
import requests
from typing import List, Dict, Any, Optional
from .config import config
from .ast_analyzer import ASTAnalyzer

class LLMService:
    def __init__(self):
        self.provider = config.resolve_provider()

    def generate_verification_questions(self, diff: str, branch: str, ticket: str) -> List[Dict[str, Any]]:
        """
        Generates exactly 3 questions:
        1. Descriptive: Architectural rationale & trade-offs.
        2. Descriptive: Edge cases, failure modes, or side-effects.
        3. Counterfactual Trap (Yes/No type): A statement containing an intentional false premise
           designed to catch blind AI copy-pasting. Expected answer is False / No.
        """
        ast_facts = ASTAnalyzer.analyze_diff(diff)

        prompt = f"""
You are an expert Lead Software Architect and Code Gatekeeper evaluating a commit for ticket "{ticket}" on branch "{branch}".

Analyze this diff and the extracted AST facts:
DIFF:
\"\"\"
{diff[:6000]}
\"\"\"

EXTRACTED AST FACTS:
- Modified Functions: {ast_facts.get('functions', [])}
- Modified Classes: {ast_facts.get('classes', [])}
- Exceptions Raised: {ast_facts.get('exceptions_raised', [])}
- Imported Packages: {ast_facts.get('imports', [])}
- Null/Empty Checks Present: {ast_facts.get('null_or_empty_checks', False)}
- Error Handling Blocks Present: {ast_facts.get('has_error_handling', False)}

TASK:
Generate EXACTLY 3 questions in JSON:
- Question 1 (type: "descriptive"): Asks the developer to explain the architectural rationale, pattern choice, or abstraction trade-off.
- Question 2 (type: "descriptive"): Asks the developer to explain how edge cases, null boundaries, error handling, or concurrency are addressed.
- Question 3 (type: "counterfactual_trap"): A binary Yes/No (True/False) statement with an INTENTIONAL COUNTERFACTUAL FALSE PREMISE.
  * The statement must sound plausible but be Factually FALSE regarding what the code actually does (e.g. claiming it silently returns None instead of raising an error, claiming it uses an unevicted in-memory cache instead of Redis, or asserting a nonexistent library/side-effect).
  * Expected answer MUST be false.

Return STRICTLY valid JSON without markdown code fences in this format:
[
  {{
    "id": 1,
    "type": "descriptive",
    "category": "Architectural Rationale",
    "question": "Why was this specific abstraction/pattern chosen over a simpler alternative?",
    "weight": 35
  }},
  {{
    "id": 2,
    "type": "descriptive",
    "category": "Edge Cases & Failure Modes",
    "question": "What happens when unexpected input or network timeout occurs, and how does the implementation handle it?",
    "weight": 35
  }},
  {{
    "id": 3,
    "type": "counterfactual_trap",
    "category": "Counterfactual Trap Check",
    "question": "When an error occurs, the implementation catches all exceptions and silently returns null to prevent caller crashes.",
    "expected_answer": false,
    "is_counterfactual_trap": true,
    "explanation": "Trap! The code does NOT return null silently; it explicitly raises a custom exception.",
    "weight": 30
  }}
]
"""
        response_text = self._call_provider(prompt)
        parsed = self._extract_json(response_text)
        if isinstance(parsed, list) and len(parsed) == 3:
            has_trap = any(q.get("type") == "counterfactual_trap" for q in parsed)
            if has_trap:
                return parsed

        return self._fallback_questions(diff, ticket, ast_facts)

    def evaluate_all_answers(
        self,
        diff: str,
        questions: List[Dict[str, Any]],
        descriptive_answers: Dict[int, str],
        trap_answer: bool
    ) -> Dict[str, Any]:
        """
        Evaluates the 2 descriptive answers using LLM/heuristics and checks the 1 counterfactual trap.
        Threshold is 80%.
        """
        # 1. Evaluate the counterfactual trap (Question 3)
        trap_q = next((q for q in questions if q.get("type") == "counterfactual_trap"), None)
        trap_triggered = False
        trap_score = 0
        trap_weight = trap_q.get("weight", 30) if trap_q else 30

        if trap_q:
            expected = trap_q.get("expected_answer", False)
            if trap_answer == expected:
                trap_score = trap_weight
            else:
                trap_triggered = True
                trap_score = 0

        # 2. Evaluate the 2 descriptive answers (Questions 1 and 2)
        desc_questions = [q for q in questions if q.get("type") == "descriptive"]
        desc_eval_result = self._evaluate_descriptive(diff, desc_questions, descriptive_answers)

        desc_score = desc_eval_result.get("earned_score", 0)
        max_desc_score = desc_eval_result.get("max_score", 70)

        total_earned = desc_score + trap_score
        total_possible = max_desc_score + trap_weight
        total_pct = round((total_earned / max(1, total_possible)) * 100, 1)

        # Pass condition: score >= 80% AND did not fall for the trap
        passed = (total_pct >= config.threshold) and not trap_triggered

        return {
            "total_score": total_pct,
            "passed": passed,
            "trap_triggered": trap_triggered,
            "trap_question": trap_q,
            "trap_user_answer": trap_answer,
            "descriptive_feedback": desc_eval_result.get("feedback", []),
            "total_earned": total_earned,
            "total_possible": total_possible
        }

    def detect_ai_copy_paste(self, diff: str, question: str, answer: str) -> Dict[str, Any]:
        """
        Detects if a developer's answer is an unedited copy-paste from an AI coding assistant.
        Checks for:
        1. AI signature phrases ("Certainly", "In this code snippet", "It is important to note", etc.)
        2. Markdown formatting (asterisks **bold**, bullet dashes `- `, numbered lists) inside terminal input
        3. Excessively verbose, formal or generic textbook prose without referencing diff variables
        4. LLM provider classification (if online)
        """
        answer_clean = answer.strip()
        word_count = len(answer_clean.split())

        # Fast heuristic checks
        ai_markers = [
            r"\b(certainly|furthermore|moreover|in summary|overall|as an ai)\b",
            r"\b(it is worth noting|in this implementation|this approach ensures|leverages the)\b",
            r"\b(by adhering to|best practice|separation of concerns|single responsibility)\b"
        ]

        has_ai_phrases = any(re.search(p, answer_clean, re.IGNORECASE) for p in ai_markers)
        has_markdown_artifacts = bool(re.search(r"(\*\*|\*|_|\n\s*[-*]\s+|\b1\.\s+)", answer_clean))
        is_suspiciously_verbose = word_count >= 40

        # Call LLM classifier if available
        if self.provider in ("gemini", "openai", "anthropic") and word_count >= 12:
            prompt = f"""
You are an AI text detector evaluating whether a code review response was copy-pasted directly from ChatGPT, Claude, or Cursor without human synthesis.

QUESTION: "{question}"
DEVELOPER ANSWER: "{answer_clean}"
DIFF:
\"\"\"
{diff[:2000]}
\"\"\"

Analyze if this answer exhibits hallmarks of AI-generated text (formal boilerplate, synthetic phrasing, textbook lecture tone, or generic explanations detached from the specific code).
Return STRICTLY valid JSON without markdown:
{{
  "is_ai_generated": true,
  "confidence": 0.85,
  "reason": "Textbook phrasing and formal bullet structure typical of LLM output."
}}
"""
            res = self._call_provider(prompt)
            parsed = self._extract_json(res)
            if isinstance(parsed, dict) and "is_ai_generated" in parsed:
                return {
                    "is_ai_generated": bool(parsed.get("is_ai_generated")),
                    "confidence": float(parsed.get("confidence", 0.7)),
                    "reason": parsed.get("reason", "AI-generated stylistic signature detected.")
                }

        # Fallback heuristic score
        ai_score = 0
        reasons = []
        if has_ai_phrases:
            ai_score += 2
            reasons.append("Contains generic AI conversational boilerplate phrases")
        if has_markdown_artifacts:
            ai_score += 1
            reasons.append("Contains markdown formatting artifacts (* or bullet lists)")
        if is_suspiciously_verbose and (has_ai_phrases or has_markdown_artifacts):
            ai_score += 1
            reasons.append("Uncharacteristically verbose textbook response")

        is_ai = ai_score >= 2
        return {
            "is_ai_generated": is_ai,
            "confidence": 0.85 if is_ai else 0.2,
            "reason": "; ".join(reasons) if reasons else "Normal developer answer."
        }

    def generate_tricky_counter_questions(
        self,
        diff: str,
        original_q: str,
        ai_answer: str,
        max_questions: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Generates max 1-2 tricky counter-questions to puncture an AI-generated answer.
        These questions focus on concrete micro-details in the diff that a copy-pasting developer
        would not know unless they actually inspected the code.
        """
        ast_facts = ASTAnalyzer.analyze_diff(diff)

        prompt = f"""
You are an adversarial lead architect. The developer submitted an AI-generated answer to a review question.
Original Question: "{original_q}"
Developer's AI Answer: "{ai_answer}"

DIFF:
\"\"\"
{diff[:4000]}
\"\"\"

AST FACTS:
- Modified functions: {ast_facts.get('functions', [])}
- Exceptions raised: {ast_facts.get('exceptions_raised', [])}
- Return statements: {ast_facts.get('returns', [])}

TASK:
Generate exactly {max_questions} TRICKY follow-up question(s) to counter this AI answer and test if the developer actually understands the micro-implementation.
The question must:
1. Target an exact variable, condition, edge-case branch, or exception in the diff.
2. Require concrete knowledge of the code rather than conceptual theory.
3. Be direct and concise (1-2 sentences).

Return JSON array:
[
  {{
    "id": 1,
    "question": "Your answer describes the pattern, but what exact exception or status code does this function raise if validation fails on the modified line?",
    "target_concept": "Exact failure mode in diff"
  }}
]
"""
        res = self._call_provider(prompt)
        parsed = self._extract_json(res)
        if isinstance(parsed, list) and len(parsed) >= 1:
            return parsed[:max_questions]

        # Fallback tricky question using AST
        funcs = ast_facts.get("functions", [])
        exceptions = ast_facts.get("exceptions_raised", [])
        returns = ast_facts.get("returns", [])

        f_name = funcs[0] if funcs else "this logic"

        if exceptions:
            tricky_q = f"Your explanation describes the pattern, but looking directly at '{f_name}': what exact exception type is raised on failure, and does it include a custom error message?"
        elif returns:
            tricky_q = f"Your answer describes the general behavior, but what exact value does '{f_name}' return when validation succeeds versus when input is empty?"
        else:
            tricky_q = f"Looking at the actual diff for '{f_name}': if the primary parameter is passed as None or empty, which branch handles it and what happens next?"

        return [
            {
                "id": 1,
                "question": tricky_q,
                "target_concept": "Concrete micro-implementation detail"
            }
        ]

    def evaluate_tricky_answer(self, diff: str, tricky_q: Dict[str, Any], answer: str) -> Dict[str, Any]:
        """Evaluates whether the developer answered the tricky counter-question accurately."""
        ans_clean = answer.strip()
        words = len(ans_clean.split())

        if self.provider in ("gemini", "openai", "anthropic") and words > 1:
            prompt = f"""
DIFF:
\"\"\"
{diff[:3000]}
\"\"\"
TRICKY QUESTION: "{tricky_q.get('question')}"
DEVELOPER ANSWER: "{ans_clean}"

Does the developer's answer correctly reflect the actual code in the diff?
Return STRICTLY JSON:
{{
  "passed": true,
  "comment": "Accurately identified the exception in the diff."
}}
"""
            res = self._call_provider(prompt)
            parsed = self._extract_json(res)
            if isinstance(parsed, dict) and "passed" in parsed:
                return {
                    "passed": bool(parsed.get("passed")),
                    "comment": parsed.get("comment", "")
                }

        # Heuristic: non-empty answer with >= 3 words and not trivial cop-out
        is_cop_out = ans_clean.lower() in ("idk", "no idea", "pass", "ai did it", "not sure", "dunno")
        passed = words >= 3 and not is_cop_out
        return {
            "passed": passed,
            "comment": "Developer provided concrete micro-implementation response." if passed else "Failed to answer tricky counter-question."
        }

    def _evaluate_descriptive(
        self,
        diff: str,
        questions: List[Dict[str, Any]],
        answers: Dict[int, str]
    ) -> Dict[str, Any]:
        """Calls LLM (or heuristic fallback) to grade the two descriptive answers."""
        payload = []
        for q in questions:
            qid = q.get("id", 1)
            payload.append({
                "id": qid,
                "category": q.get("category"),
                "question": q.get("question"),
                "weight": q.get("weight", 35),
                "answer": answers.get(qid, "").strip()
            })

        prompt = f"""
You are a senior code reviewer grading two developer explanations for this git diff:
DIFF:
\"\"\"
{diff[:4000]}
\"\"\"

QUESTIONS AND DEVELOPER RESPONSES:
{json.dumps(payload, indent=2)}

GRADING INSTRUCTIONS:
- Grade each question from 0 up to its weight (35 points each).
- Award high points if the developer demonstrates genuine comprehension of the diff mechanics and edge cases.
- Award low or 0 points if answers are generic, shallow (e.g. "it works", "ai wrote this", "tests pass"), or inaccurate.

Return STRICTLY JSON:
{{
  "earned_score": 60,
  "max_score": 70,
  "feedback": [
    {{
      "id": 1,
      "score": 30,
      "max_score": 35,
      "comment": "Accurately detailed the retry rationale."
    }},
    {{
      "id": 2,
      "score": 30,
      "max_score": 35,
      "comment": "Clearly identified the timeout failure mode."
    }}
  ]
}}
"""
        response_text = self._call_provider(prompt)
        parsed = self._extract_json(response_text)
        if isinstance(parsed, dict) and "earned_score" in parsed:
            return parsed

        # Heuristic fallback for offline mode
        earned = 0
        feedback = []
        for q in questions:
            qid = q.get("id", 1)
            ans = answers.get(qid, "").strip()
            weight = q.get("weight", 35)
            words = len(ans.split())

            if words >= 10:
                s = weight
                c = "Thorough technical explanation demonstrating active comprehension."
            elif words >= 5:
                s = int(weight * 0.7)
                c = "Acceptable overview, though edge-case specifics were brief."
            elif words > 0:
                s = int(weight * 0.3)
                c = "Superficial answer; lacks technical depth on implementation mechanics."
            else:
                s = 0
                c = "No explanation provided."

            earned += s
            feedback.append({
                "id": qid,
                "score": s,
                "max_score": weight,
                "comment": c
            })

        return {
            "earned_score": earned,
            "max_score": sum(q.get("weight", 35) for q in questions),
            "feedback": feedback
        }

    def generate_explanation_summary(self, diff: str, ticket: str) -> str:
        """
        Generates a crisp, human-readable summary of max 50-100 words explaining why the changes were made,
        their architectural intent, and what problem they solve.
        """
        prompt = f"""
Summarize the following git diff in a concise, authoritative summary of MAXIMUM 50 to 100 WORDS.
Explain:
1. Why the changes are there (the root intent / problem solved).
2. Key architectural components touched.

Do not use conversational greetings. Keep it strictly between 50 and 100 words.

DIFF:
\"\"\"
{diff[:5000]}
\"\"\"
"""
        res = self._call_provider(prompt)
        clean = res.strip().replace("```", "").replace("\n\n", " ")
        words = clean.split()
        if len(words) > 100:
            clean = " ".join(words[:95]) + "..."
        if len(clean) < 20:
            clean = f"Commit {ticket}: Implemented targeted logic refactoring and system updates to address requirement specifications, ensuring consistent state handling and functional validation."
        return clean

    def _call_provider(self, prompt: str) -> str:
        provider = self.provider
        if provider == "gemini" and config.gemini_api_key:
            return self._call_gemini(prompt)
        elif provider == "openai" and config.openai_api_key:
            return self._call_openai(prompt)
        elif provider == "anthropic" and config.anthropic_api_key:
            return self._call_anthropic(prompt)
        return ""

    def _call_gemini(self, prompt: str) -> str:
        models_to_try = [
            "gemini-flash-lite-latest",
            "gemini-flash-latest",
            "gemini-2.5-flash",
            "gemini-1.5-flash"
        ]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }

        for model in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config.gemini_api_key}"
                res = requests.post(url, json=payload, timeout=20)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
            except Exception:
                continue

        return ""

    def _call_openai(self, prompt: str) -> str:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {config.openai_api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            pass
        return ""

    def _call_anthropic(self, prompt: str) -> str:
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return data["content"][0]["text"]
        except Exception:
            pass
        return ""

    def _extract_json(self, text: str) -> Optional[Any]:
        if not text:
            return None
        clean = text.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```[a-zA-Z]*\n", "", clean)
            clean = re.sub(r"\n```$", "", clean)
        try:
            return json.loads(clean.strip())
        except Exception:
            match = re.search(r"(\[.*\]|\{.*\})", clean, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
        return None

    def _fallback_questions(self, diff: str, ticket: str, ast_facts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback generating 2 descriptive + 1 counterfactual trap question."""
        funcs = ast_facts.get("functions", [])
        classes = ast_facts.get("classes", [])
        exceptions = ast_facts.get("exceptions_raised", [])
        has_null_check = ast_facts.get("null_or_empty_checks", False)

        if funcs:
            target_name = f"'{funcs[0]}'"
        elif classes:
            target_name = f"class '{classes[0]}'"
        else:
            target_name = "this modified logic"

        # Trap Statement (plausible falsehood)
        if exceptions:
            exc_name = exceptions[0]
            trap_stmt = f"When an invalid input or failure occurs in {target_name}, the code catches the error and silently returns None/null to avoid alerting upstream callers."
            trap_exp = f"Trap! The code does NOT return null silently; it explicitly raises '{exc_name}' to maintain fail-fast integrity."
        elif has_null_check:
            trap_stmt = f"This commit completely omits null or boundary checks in {target_name}, delegating all input sanitation to the caller."
            trap_exp = "Trap! The diff explicitly contains boundary checks to prevent null reference faults."
        else:
            trap_stmt = f"This implementation modifies {target_name} by replacing internal project calls with an unvetted third-party external dependency."
            trap_exp = "Trap! No unvetted third-party library was added; the logic relies on standard primitives."

        return [
            {
                "id": 1,
                "type": "descriptive",
                "category": "Architectural Rationale",
                "question": f"Why was {target_name} implemented with this specific structure or abstraction rather than a simpler procedural approach?",
                "weight": 35
            },
            {
                "id": 2,
                "type": "descriptive",
                "category": "Edge Cases & Failure Modes",
                "question": f"What potential edge case, null input, or failure mode could occur in {target_name}, and how does your implementation safeguard against it?",
                "weight": 35
            },
            {
                "id": 3,
                "type": "counterfactual_trap",
                "category": "Counterfactual Trap Check",
                "question": trap_stmt,
                "expected_answer": False,
                "is_counterfactual_trap": True,
                "explanation": trap_exp,
                "weight": 30
            }
        ]
