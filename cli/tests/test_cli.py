import unittest
from git_check.git_service import GitService
from git_check.llm_service import LLMService
from git_check.ast_analyzer import ASTAnalyzer
from git_check.note_generator import NoteGenerator

class TestGitCheck(unittest.TestCase):
    def test_ticket_extraction(self):
        git = GitService()
        self.assertEqual(git.extract_ticket_number("feat/PROJ-1234-retry-logic"), "PROJ-1234")
        self.assertEqual(git.extract_ticket_number("bugfix/APP-99-crash"), "APP-99")
        self.assertEqual(git.extract_ticket_number("issue-456"), "ISSUE-456")

    def test_ast_analyzer(self):
        diff_sample = """
        +def calculate_tax(amount, rate):
        +    if amount < 0:
        +        raise ValueError("negative amount")
        +    return amount * rate
        """
        facts = ASTAnalyzer.analyze_diff(diff_sample)
        self.assertIn("calculate_tax", facts["functions"])
        self.assertIn("ValueError", facts["exceptions_raised"])

    def test_question_structure_two_descriptive_one_trap(self):
        """Verifies exactly 3 questions: 2 descriptive + 1 counterfactual trap Yes/No."""
        llm = LLMService()
        diff_sample = """
        +def calculate_tax(amount, rate):
        +    if amount < 0:
        +        raise ValueError("negative amount")
        +    return amount * rate
        """
        questions = llm.generate_verification_questions(diff_sample, "feature/tax", "PROJ-101")
        self.assertEqual(len(questions), 3, "Must generate exactly 3 questions")

        descriptive_qs = [q for q in questions if q.get("type") == "descriptive"]
        trap_qs = [q for q in questions if q.get("type") == "counterfactual_trap"]

        self.assertEqual(len(descriptive_qs), 2, "Must have exactly 2 descriptive questions")
        self.assertEqual(len(trap_qs), 1, "Must have exactly 1 counterfactual trap question")
        self.assertFalse(trap_qs[0].get("expected_answer"), "Trap expected answer must be False")

    def test_ai_copy_paste_detection(self):
        llm = LLMService()
        # Normal developer answer
        human_ans = "I extracted the tax calculation into a separate helper so we can unit test negative amounts without touching the database."
        res_human = llm.detect_ai_copy_paste("diff", "Why this change?", human_ans)
        self.assertFalse(res_human["is_ai_generated"])

        # Classic AI copy-paste with conversational boilerplate and markdown bullets
        ai_ans = "Certainly! In this code implementation, furthermore by adhering to the single responsibility principle, this approach ensures best practice architecture: **1. Decoupled logic**."
        res_ai = llm.detect_ai_copy_paste("diff", "Why this change?", ai_ans)
        self.assertTrue(res_ai["is_ai_generated"])

    def test_tricky_counter_question_generation(self):
        llm = LLMService()
        diff_sample = """
        +def calculate_tax(amount, rate):
        +    if amount < 0:
        +        raise ValueError("negative amount")
        +    return amount * rate
        """
        tricky_qs = llm.generate_tricky_counter_questions(
            diff_sample,
            "Why calculate_tax?",
            "Certainly, this implementation adheres to clean architecture principles.",
            max_questions=1
        )
        self.assertEqual(len(tricky_qs), 1)
        self.assertIn("question", tricky_qs[0])

        # Developer answers correctly
        eval_pass = llm.evaluate_tricky_answer(diff_sample, tricky_qs[0], "It raises a ValueError on negative amount.")
        self.assertTrue(eval_pass["passed"])

        # Developer gives cop-out
        eval_fail = llm.evaluate_tricky_answer(diff_sample, tricky_qs[0], "idk")
        self.assertFalse(eval_fail["passed"])

    def test_evaluation_pass_when_thorough_and_trap_avoided(self):
        llm = LLMService()
        questions = [
            {"id": 1, "type": "descriptive", "category": "Architecture", "question": "Why calculate_tax?", "weight": 35},
            {"id": 2, "type": "descriptive", "category": "Edge Cases", "question": "How are errors handled?", "weight": 35},
            {"id": 3, "type": "counterfactual_trap", "category": "Trap", "question": "Silently returns None on error?", "expected_answer": False, "weight": 30}
        ]

        # Developer provides solid technical answers and answers False (No) to the trap
        res_pass = llm.evaluate_all_answers(
            diff="sample",
            questions=questions,
            descriptive_answers={
                1: "We separated calculate_tax into its own pure function to allow deterministic testing and isolation.",
                2: "The function validates amount bounds and raises ValueError on negative numbers to prevent ledger corruption."
            },
            trap_answer=False # Avoided trap!
        )
        self.assertTrue(res_pass["passed"])
        self.assertFalse(res_pass["trap_triggered"])
        self.assertGreaterEqual(res_pass["total_score"], 80.0)

    def test_evaluation_fail_when_trap_triggered(self):
        llm = LLMService()
        questions = [
            {"id": 1, "type": "descriptive", "category": "Architecture", "question": "Why calculate_tax?", "weight": 35},
            {"id": 2, "type": "descriptive", "category": "Edge Cases", "question": "How are errors handled?", "weight": 35},
            {"id": 3, "type": "counterfactual_trap", "category": "Trap", "question": "Silently returns None on error?", "expected_answer": False, "weight": 30}
        ]

        # Developer answers True (Yes) to the trap statement -> Fell into trap!
        res_fail = llm.evaluate_all_answers(
            diff="sample",
            questions=questions,
            descriptive_answers={
                1: "Standard helper method.",
                2: "Raises ValueError."
            },
            trap_answer=True # Fell for trap!
        )
        self.assertFalse(res_fail["passed"])
        self.assertTrue(res_fail["trap_triggered"])

    def test_note_generation(self):
        trailer = NoteGenerator.format_commit_trailer("PROJ-402", "Implemented webhook retry backoff", True)
        self.assertIn("GitCheck-Ticket: PROJ-402", trailer)
        self.assertIn("Acknowledged-By-Author", trailer)
        self.assertNotIn("score", trailer.lower())

if __name__ == "__main__":
    unittest.main()
