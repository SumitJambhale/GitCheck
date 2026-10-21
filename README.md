# GitCheck: Pre-Commit Verification Gate (`git-check`)

GitCheck is a pre-commit verification harness and comprehension gate for AI-assisted software development. It prevents comprehension debt, duplicate libraries, and review gridlock before code is pushed to pull requests.

---

## Architecture Overview

```
GitCheck/
├── cli/                 # Python CLI harness installed on developer machines
│   ├── git_check/       # Diff inspection, Socratic interrogation, Supabase sync
│   └── tests/           # Unit test suite
├── web/                 # React Single Page App (deployed to Vercel)
│   ├── src/             # Commit review description, previous context timeline
│   └── vercel.json      # Vercel deployment configuration
└── supabase/
    └── schema.sql       # PostgreSQL schema with RLS and indexing
```

---

## 1. CLI Harness (`GitCheck/cli`)

### Key Features
- **Hybrid Verification (2 Descriptive + 1 Counterfactual Trap)**:
  - **2 Descriptive Questions**: Evaluates the developer's explanations of architectural trade-offs, pattern choices, and edge-case handling.
  - **1 Counterfactual Trap (Yes/No)**: An intentional subtle false premise about the code behavior (e.g. claiming a method silently returns None on failure). Expected answer is No/False.
- **AI Copy-Paste Detection & Tricky Counter-Questions**:
  - Automatically analyzes developer explanations for AI signatures (boilerplate, synthetic formatting, or disconnected textbook lectures).
  - If an answer appears copied from ChatGPT, Claude, or Cursor, GitCheck immediately challenges the developer with **1–2 tricky micro-implementation questions** (e.g., exact parameter checks, exception types, or failure return values) to force active human comprehension.
- **80% Acceptance Threshold & Trap Detection**:
  - **Pass (≥ 80% & no traps triggered)**: Confirms active comprehension, generates a concise 50–100 word summary, and tags the commit.
  - **Needs Review (< 80% or Trap Caught)**: Highlights the counterfactual false premise that was accepted, displays a concise **50–100 word explanation** of why the changes exist, and prompts the developer to confirm agreement (`[y/N]`).
- **Privacy Guaranteed**: Quiz scores and individual comprehension grades are kept strictly confidential. Only the architectural summary and author agreement are recorded.
- **Configurable LLM Provider**: Supports Google Gemini (`gemini-1.5-flash`), OpenAI (`gpt-4o-mini`), Anthropic Claude (`claude-3-haiku`), or intelligent AST-driven local heuristics.
- **PostgreSQL / Supabase Integration**: Automatically caches findings and past context to prevent repeated rework.

### Installation & Usage

```bash
# 1. Install CLI locally
cd GitCheck/cli
pip install -e .

# 2. Configure API Keys (optional; falls back to offline heuristic engine)
export GEMINI_API_KEY="your-gemini-api-key"
# or export OPENAI_API_KEY="your-openai-key"
# or export ANTHROPIC_API_KEY="your-anthropic-key"

# 3. Configure Supabase (optional; falls back to local cache)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-supabase-anon-key"

# 4. Install Git Pre-Commit Hook in any repo
git-check install-hook

# 5. Run manual verification on staged diff
git add .
git-check run
```

---

## 2. Web Review Dashboard (`GitCheck/web`)

### Key Features
- **Single Page Commit Description**: Displays the ticket number, commit hash, author, agreement status, modified files, and the 50–100 word architectural summary.
- **Previous Rejection Context**: Displays historical commit iterations when a PR was previously rejected, ensuring developers and reviewers understand prior feedback and avoid rework loops.
- **Vercel-Ready**: Preconfigured with `vercel.json` for one-click deployment.

### Local Development & Vercel Deployment

```bash
# Local development
cd GitCheck/web
npm install
npm run dev

# Build for production
npm run build
```

To deploy to Vercel:
1. Connect your GitHub repository to Vercel.
2. Set Root Directory to `GitCheck/web`.
3. Add environment variables in Vercel project settings:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
4. Click Deploy.

---

## 3. Database Setup (`GitCheck/supabase`)

1. Open your [Supabase Dashboard](https://supabase.com).
2. Go to the **SQL Editor**.
3. Run the SQL script located at `GitCheck/supabase/schema.sql`.
