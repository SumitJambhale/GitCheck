# GITCHECK: Pitch Deck Specification
## Pre-Commit Verification Gate & Comprehension Harness for AI-Assisted Code

---

### Executive Banner: The Macro Paradigm Shift

> **AI Solved the Drafting Bottleneck. It Created a Review Crisis.**
> 
> AI coding assistants generate 30% more code, but shipped throughput remains flat because PR review times have surged by 49%. **GitCheck** introduces an author-side pre-commit comprehension gate that verifies developer understanding via counterfactual traps, intercepts AI copy-pasting, eliminates rework loops, and attaches an auditable defense card before pull requests hit human review.

---

## Slide 1: The Macro Problem (Empirical Developer Data)
**Badge:** `Validation`

### Core Metrics:
* **+30%** — Code Volume Generated per Developer (Copilot, Cursor, Claude Code)
* **+49%** — PR Review Latency Spike across Engineering Teams
* **0%** — Net Gain in Shipped Production Features (Harvard Empirical / GitClear Data)

### The Two Clocks Phenomenon:
* **Clock 1 (Drafting Speed):** AI coding assistants (Cursor, GitHub Copilot, Claude Code) drastically accelerate drafting by dumping unvetted, synthetically confident diffs into repositories.
* **Clock 2 (Defensible Decisions):** Software delivery velocity is constrained by Clock 2, where human reviewers must painstakingly verify architectural soundness, concurrency, security boundaries, and subtle edge cases.

### Comprehension Debt:
Developers routinely commit and submit code they cannot explain. When Principal Engineers or Tech Leads question abstractions, unexpected side-effects, or duplicate dependencies, authors fall back on unmediated prompt-relaying ("ChatGPT generated it this way"). This triggers multi-day review ping-pong, PR rejections, and engineering fatigue.

---

## Slide 2: Who Feels the Friction?
**Badge:** `User Hierarchy`

| Role / Stakeholder | Primary Pain Point | Root Cause |
| :--- | :--- | :--- |
| **Software Engineers (Authors)** | PR embarrassment, multi-day review ping-pong, repetitive rework on rejected PRs. | Lack of mental model for agent-generated diffs; inability to defend architectural trade-offs during review. |
| **Principal Engineers (Reviewers)** | Burnout from acting as manual linters, test executors, and architecture watchdogs. | Flooded with unvetted, bloated PRs containing speculative abstractions, duplicate helpers, and unverified edge cases. |
| **VP of Engineering (Buyer)** | Zero net ROI on generative AI tool licenses; release cycles stalled by review gate bottlenecks. | Local drafting speed creates operational gridlock at the review gate (Theory of Constraints). |

---

## Slide 3: The Solution — `GitCheck`
**Badge:** `Comprehension Gate`

GitCheck is a local CLI harness and cloud anti-rework system that executes at `git commit`. It interrogates the author before code leaves their workstation, intercepts blind AI copy-pasting, and provides historical context on rejected PRs.

### 1. Hybrid Socratic Verification (2+1 Model)
* **2 Descriptive Architectural Prompts:** Evaluates the author's comprehension of architectural choices, abstraction trade-offs, and failure boundaries.
* **1 Counterfactual Trap Check (Yes/No):** Generates an intentional, subtle false premise about the code behavior (e.g., claiming a function silently catches errors and returns null). Answering "Yes" exposes blind agreement and halts the gate.

### 2. AI Copy-Paste Detection & Micro-Implementation Probes
* Automatically analyzes developer explanations for synthetic AI signatures (boilerplate bullet points, disconnected theoretical lectures).
* If an answer appears copy-pasted from ChatGPT/Claude, GitCheck immediately triggers an **adversarial micro-implementation counter-question** (e.g., exact return types, exception parameters, or null fallbacks) to confirm firsthand inspection.

### 3. 80% Acceptance Threshold & Author Accountability Gate
* Requires a combined score of **≥ 80%** with zero traps triggered to pass automatically.
* If a trap is triggered or score falls below 80%, GitCheck surfaces the false premise, presents a concise **50–100 word architectural summary**, and requires explicit author responsibility confirmation (`[y/N]`).

### 4. Anti-Rework PR Defense Card & History Sync
* Writes an auditable `GITCHECK_DEFENSE_CARD.md` and attaches a structured commit trailer (`GitCheck-Summary`, `GitCheck-Status`).
* Automatically syncs commit context to **Supabase PostgreSQL** and the **GitCheck Web Dashboard**, giving reviewers full historical timeline context on prior PR rejections to stop rework loops.
* **Privacy Guaranteed:** Individual comprehension quiz scores are strictly confidential; only the architectural defense summary is published.

---

## Slide 4: Developer Comprehension Score ($DCS$)
**Badge:** `Mathematical Engine`

GitCheck evaluates author comprehension using a multi-factor mathematical scoring model designed to prevent automated gaming and prompt-relaying:

$$\text{DCS} = \left( w_{\text{arch}} \cdot S_{\text{arch}} + w_{\text{edge}} \cdot S_{\text{edge}} + w_{\text{trap}} \cdot T \right) - \lambda_{\text{cheat}}$$

Where:
* **Architectural Rationale ($S_{\text{arch}} \in [0, 1]$):** Evaluates depth of explanation regarding pattern choices, trade-offs, and repo alignment ($w_{\text{arch}} = 0.35$).
* **Edge-Case & Failure Resilience ($S_{\text{edge}} \in [0, 1]$):** Evaluates coverage of error handling, null boundaries, timeouts, and concurrency ($w_{\text{edge}} = 0.35$).
* **Counterfactual Trap Score ($T \in \{0, 1\}$):** Binary verification of the intentional false premise ($w_{\text{trap}} = 0.30$).
  $$T = \mathbb{I}(y_{\text{user}} = y_{\text{expected}}), \quad \text{where } y_{\text{expected}} = \text{False}$$
  If $y_{\text{user}} = \text{True}$ (author accepts false premise), $T = 0$ and `trap_triggered` flag forces review.
* **AI Copy-Paste Penalty ($\lambda_{\text{cheat}}$):**
  $$\lambda_{\text{cheat}} = \begin{cases} 
  0 & \text{if answer is original human explanation} \\ 
  0 & \text{if AI detected BUT author passes micro-implementation probe} \\
  0.70 & \text{if AI detected AND author fails micro-implementation probe}
  \end{cases}$$
* **Passing Condition:** $\text{DCS} \ge 0.80 \quad \land \quad T = 1$

---

## Slide 5: The 60-Second Terminal Experience
**Badge:** `Developer Workflow`

```bash
$ git add src/services/payment_webhook.py
$ git commit -m "feat(payment): add exponential backoff retry for webhooks"

┌─────────────────────────────────────────────────────────────┐
│ GitCheck • Pre-Commit Verification Gate                     │
│ Comprehension Harness for AI-Assisted Code                  │
└─────────────────────────────────────────────────────────────┘
Branch: feat/PROJ-402-payment-webhook-retry | Ticket: PROJ-402
Author: Milind Mane <milind.mane@company.internal>
Files changed: 3 | +84 -12

╭─ Historical PR Context (Anti-Rework) ──────────────────────────────────────╮
│ Previous context found for ticket PROJ-402 (1 past iteration).             │
│ Most recent rejection: In-memory retry failed during cluster restarts.     │
╰────────────────────────────────────────────────────────────────────────────╯
Analyzing diff & AST via GEMINI-1.5-FLASH Verification Engine...

Question 1 / 3: [Architectural Rationale]
Why was Redis chosen for storing webhook retry state instead of an in-memory queue?
Your explanation: Redis provides distributed state persistence across service restarts and multiple cluster nodes.

Question 2 / 3: [Edge Cases & Failure Modes]
What occurs when Redis connection pool times out during webhook receipt?
Your explanation: According to best practices in distributed systems, when connection pool exhaustion happens...
⚠️  AI-Generated Answer Detected! [Textbook boilerplate detected]
╭─ AI Copy-Paste Interceptor ────────────────────────────────────────────────╮
│ Tricky Micro-Implementation Counter-Question:                              │
│ "Looking directly at payment_webhook.py: line 48: what exact exception is  │
│  caught on Redis timeout, and what fallback HTTP status code is returned?" │
╰────────────────────────────────────────────────────────────────────────────╯
Your micro-implementation answer: ConnectionError; it logs an alert and returns HTTP 503 Service Unavailable.
✔ Tricky question passed! Author verified direct code knowledge.

Question 3 / 3: [Counterfactual Trap Check - Yes/No]
"Does line 62 silently drop failed webhooks if the signature header is empty?"
Does this statement accurately describe what your changes do? (y/n): n
✔ Counterfactual Trap Avoided! (Expected: No; Code raises InvalidSignatureError).

✔ Verification Passed (88.5%)! Comprehension Verified.

Why these changes are here (Summary):
Introduced exponential backoff retry mechanism for failed payment gateway webhooks. Centralized retry state in distributed Redis cache to prevent redundant transaction processing under high network latency, avoiding race conditions during peak checkout volumes.

╭─ Pre-Commit Gate Completed Successfully ───────────────────────────────────╮
│ • Summary Note: Added to PR defense artifact                               │
│ • Defense Card: .gitcheck/GITCHECK_DEFENSE_CARD.md                         │
│ • Database: Synced to Supabase (https://xyz.supabase.co)                   │
│ • Review Dashboard: https://gitcheck-review.vercel.app/ticket/PROJ-402     │
╰────────────────────────────────────────────────────────────────────────────╯
```

---

## Slide 6: How We Built It (Architecture & Tech Stack)
**Badge:** `Tech Stack`

| Component | Technology Stack | Implementation Details |
| :--- | :--- | :--- |
| **CLI Core** | Python 3.10+, Click, Rich | Lightweight interactive terminal UI executing sub-second local checks. Packaged for `pip install` / `pipx`. |
| **AST & Diff Analyzer** | Native `ast` & Multi-Language Heuristics | Deep AST parsing for Python; robust structural regex extraction for TypeScript, Go, and C# (functions, exceptions, imports, returns). |
| **Verification Engine** | Gemini 1.5 Flash / Claude 3 Haiku / GPT-4o-mini | Generates 2 architectural prompts + 1 counterfactual trap. Offline heuristic mode available when disconnected. |
| **Anti-Cheating Engine** | LLM Classifier + Micro AST Probes | Detects AI syntax patterns and generates targeted micro-implementation challenges targeting exact lines, returns, and exceptions. |
| **Anti-Rework Cloud Store** | Supabase PostgreSQL + Row Level Security | Stores commit metadata, 50-100 word summaries, and review history indexed by ticket number and commit recency. |
| **Web Review Dashboard** | React 18, Vite, TypeScript, Tailwind CSS | Single-page commit review interface with timeline of previous PR rejections, deployed on Vercel. |
| **Git Hook Harness** | Native `.git/hooks` (`pre-commit`) | Zero-friction installation via `git-check install-hook` with bypass flag (`--no-verify` or `--skip`). |

---

## Slide 7: Competitive Landscape
**Badge:** `Market Differentiation`

| Solution Category | Key Examples | Primary Limitation | GitCheck Advantage |
| :--- | :--- | :--- | :--- |
| **PR Review Bots** | CodeRabbit, PR-Agent, Copilot PR | **Downstream on GitHub:** Generates comment noise after PR is created; authors mindlessly copy-paste bot suggestions back into Cursor. | **Author-Side Pre-Commit Gate:** Shifts comprehension verification to the author's terminal *before* the PR is created. |
| **General LLMs** | ChatGPT, Claude Chat, Cursor inline | **Passive & Acquiescent:** Suffers from acquiescence bias; validates the user's false premises and encourages unvetted code dumping. | **Active Adversarial Traps:** Counterfactual traps and tricky micro-probes catch blind copy-pasting. |
| **Static Linters** | SonarQube, Semgrep, ESLint | **Blind to Intent:** Checks AST syntax rules, formatting, and known CVE patterns, but cannot verify architecture or intent. | **Architectural & Intent Verification:** Verifies *why* code was written, trade-offs made, and edge-case handling. |
| **PR Management Dashboards** | LinearB, Jellyfish, DX | **Post-Mortem Metrics:** Measures PR cycle time after the bottleneck has already damaged delivery schedules. | **Anti-Rework Prevention:** Surfaces prior rejection history directly in the CLI and web dashboard to prevent repeated review loops. |

---

## Slide 8: ROI & Go-To-Market Strategy
**Badge:** `Business Case`

### Bottom-Up Developer Adoption
* **Open-Source CLI Distribution:** Installable in 10 seconds via `pip install git-check` and `git-check install-hook`.
* **Individual Developer Benefit:** Eliminates PR review embarrassment, clarifies commit intent, and auto-generates PR defense summaries that accelerate peer review sign-offs.
* **Strict Confidentiality:** Individual comprehension scores and quiz responses are kept strictly private; peers and managers only see the author's verified architectural defense summary.

### Enterprise Governance & Anti-Rework Tier
* **Centralized Anti-Rework Repository:** Connects enterprise engineering teams via Supabase/Cloud dashboard.
* **Eliminates Repeated Review Loops:** When a PR iteration is rejected, past review context and architectural notes persist across subsequent commits, preventing authors from re-introducing failed patterns.
* **Review Gate Velocity:** Shrinks PR turnaround time by arming Principal Engineers with instant, verified defense cards.

### The Bottom Line:
* **Latency Reduction:** Cuts PR review cycle time from **48 hours to 4 hours**.
* **Engineering Hours Saved:** Reclaims **12+ hours per week** of Principal Engineer and Tech Lead time otherwise spent acting as manual code examiners.
* **Expected ROI:** **~15x per developer seat annually** in saved senior engineering capacity.
