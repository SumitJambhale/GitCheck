import sys
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

try:
    from .config import config
    from .git_service import GitService
    from .llm_service import LLMService
    from .supabase_service import SupabaseService
    from .note_generator import NoteGenerator
except (ImportError, ValueError):
    try:
        from git_check.config import config
        from git_check.git_service import GitService
        from git_check.llm_service import LLMService
        from git_check.supabase_service import SupabaseService
        from git_check.note_generator import NoteGenerator
    except (ImportError, ValueError):
        from config import config
        from git_service import GitService
        from llm_service import LLMService
        from supabase_service import SupabaseService
        from note_generator import NoteGenerator

console = Console()

def render_banner():
    console.print(
        Panel.fit(
            "[bold cyan]GitCheck[/bold cyan] [white]• Pre-Commit Verification Gate[/white]\n"
            "[dim]Comprehension Harness for AI-Assisted Code[/dim]",
            border_style="cyan"
        )
    )

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """GitCheck: Pre-Commit Verification Gate for AI-Generated & Modified Code."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)

@cli.command()
@click.option("--hook", is_flag=True, help="Invoked automatically by git pre-commit hook.")
@click.option("--ticket", "-t", default=None, help="Explicit Jira/Issue ticket number.")
@click.option("--last-commit", is_flag=True, help="Verify the last commit made on HEAD instead of staged changes.")
def run(hook: bool, ticket: Optional[str] = None, last_commit: bool = False):
    """Run interactive comprehension verification on staged git changes."""
    render_banner()

    git = GitService()
    if not git.is_git_repo():
        console.print("[bold red]Error:[/bold red] Not inside a Git repository.")
        sys.exit(1)

    diff = git.get_staged_diff(allow_last_commit=last_commit)
    if not diff or not diff.strip():
        console.print("[yellow]Notice:[/yellow] No changes found to verify.")
        console.print("[dim]Stage your changes with `git add <files>` before running git-check.\n(Or use `git-check run --last-commit` to re-verify the previous commit).[/dim]")
        sys.exit(0 if hook else 1)

    branch = git.get_branch_name()
    detected_ticket = ticket or git.extract_ticket_number(branch) or "UNASSIGNED"
    author_name, author_email = git.get_author_info()
    diff_stats = git.get_diff_stats()
    commit_hash = git.get_latest_commit_hash()

    console.print(f"[bold]Branch:[/bold] {branch} | [bold]Ticket:[/bold] [green]{detected_ticket}[/green]")
    console.print(f"[bold]Author:[/bold] {author_name} <{author_email}>")
    console.print(
        f"[dim]Files changed: {len(diff_stats['files_changed'])} | "
        f"+{diff_stats['lines_added']} -{diff_stats['lines_removed']}[/dim]\n"
    )

    supabase = SupabaseService()

    # Check for previous commit context for this ticket
    previous_reviews = supabase.fetch_ticket_history(detected_ticket)
    if previous_reviews:
        console.print(
            Panel(
                f"[yellow]Previous context found for ticket {detected_ticket} ({len(previous_reviews)} past iterations).[/yellow]\n"
                f"[dim]Most recent reason: {previous_reviews[0].get('summary', 'N/A')}[/dim]",
                title="Historical PR Context (Anti-Rework)",
                border_style="yellow"
            )
        )

    llm = LLMService()
    provider_name = llm.provider.upper()
    console.print(f"[cyan]Analyzing diff & AST via {provider_name} Verification Engine...[/cyan]")

    with console.status("[bold green]Generating 2 descriptive questions + 1 counterfactual trap..."):
        questions = llm.generate_verification_questions(diff, branch, detected_ticket)

    console.print(
        Panel(
            "[bold white]GitCheck Pre-Commit Verification (3 Questions)[/bold white]\n"
            "[dim]• 2 Descriptive questions on architecture and edge cases\n"
            "• 1 Counterfactual Trap (Yes/No) with an intentional subtle false premise\n"
            "Threshold: 80% combined score. Catches blind AI copy-pasting.[/dim]",
            border_style="blue"
        )
    )

    desc_answers = {}
    trap_user_answer = False

    for idx, q in enumerate(questions, 1):
        q_type = q.get("type", "descriptive")
        category = q.get("category", "Verification")

        if q_type == "descriptive":
            console.print(f"\n[bold cyan]Question {idx} / 3: [{category}][/bold cyan]")
            console.print(f"[white]{q.get('question')}[/white]")
            ans = Prompt.ask("[green]Your explanation[/green]").strip()

            # Check if answer appears copied from AI (ChatGPT / Claude / Cursor)
            with console.status("[dim]Checking answer originality...[/dim]"):
                ai_check = llm.detect_ai_copy_paste(diff, q.get("question", ""), ans)

            if ai_check.get("is_ai_generated"):
                console.print(
                    Panel(
                        f"[bold yellow]⚠️ AI-Generated Answer Detected![/bold yellow]\n"
                        f"[dim]Reason: {ai_check.get('reason')}[/dim]\n\n"
                        "[bold white]Running Counter-Interrogation:[/bold white] To verify direct human understanding rather than "
                        "unmediated AI copy-pasting, answer this tricky micro-implementation question:",
                        title="AI Copy-Paste Interceptor",
                        border_style="yellow"
                    )
                )

                with console.status("[bold green]Generating tricky counter-question..."):
                    tricky_qs = llm.generate_tricky_counter_questions(diff, q.get("question", ""), ans, max_questions=1)

                if tricky_qs:
                    tricky_q = tricky_qs[0]
                    console.print(f"[bold magenta]Tricky Counter-Question:[/bold magenta] [white]{tricky_q.get('question')}[/white]")
                    tricky_ans = Prompt.ask("[green]Your micro-implementation answer[/green]").strip()

                    with console.status("[dim]Verifying tricky response...[/dim]"):
                        tricky_eval = llm.evaluate_tricky_answer(diff, tricky_q, tricky_ans)

                    if tricky_eval.get("passed"):
                        console.print("[bold green]✔ Tricky question passed![/bold green] [dim]Author verified direct code knowledge.[/dim]")
                        desc_answers[q.get("id", idx)] = f"{ans}\n[Author Verified Detail: {tricky_ans}]"
                    else:
                        console.print("[bold red]✘ Tricky question failed.[/bold red] [dim]Could not defend implementation detail.[/dim]")
                        desc_answers[q.get("id", idx)] = "[Copied AI answer without understanding micro-implementation]"
                else:
                    desc_answers[q.get("id", idx)] = ans
            else:
                desc_answers[q.get("id", idx)] = ans

        else:
            console.print(f"\n[bold magenta]Question {idx} / 3: [Counterfactual Trap Check - Yes/No][/bold magenta]")
            console.print(f"[white]\"{q.get('question')}\"[/white]")
            raw_ans = Prompt.ask(
                "[green]Does this statement accurately describe what your changes do? (y/n / True/False)[/green]",
                default="y"
            ).strip().lower()
            trap_user_answer = raw_ans in ("y", "yes", "true", "t", "1")

    with console.status("[bold green]Evaluating comprehension and trap verification..."):
        eval_result = llm.evaluate_all_answers(diff, questions, desc_answers, trap_user_answer)

    passed = eval_result.get("passed", False)
    score = eval_result.get("total_score", 0.0)
    trap_triggered = eval_result.get("trap_triggered", False)

    # Branch logic based on 80% acceptance threshold and trap detection
    if passed:
        console.print(
            Panel(
                f"[bold green]✔ Verification Passed ({score}%)! Comprehension Verified.[/bold green]\n"
                "[dim]You successfully answered the technical prompts and avoided the counterfactual trap.[/dim]",
                border_style="green"
            )
        )
        with console.status("[bold green]Generating architectural change summary..."):
            summary_50_100 = llm.generate_explanation_summary(diff, detected_ticket)
        agreed = True
        status_label = "PASSED"

    else:
        fail_msg = f"[bold yellow]⚠️ Verification Failed (Score: {score}% < {config.threshold}%).[/bold yellow]\n"
        if trap_triggered:
            fail_msg += "[bold red]Caught in Counterfactual Trap:[/bold red] You accepted an intentional false premise about the code!\n"
        fail_msg += "[dim]AI code generation frequently introduces subtle assumptions that go unnoticed without active review.[/dim]"

        console.print(Panel(fail_msg, border_style="yellow"))

        # If counterfactual trap was triggered, show why
        if trap_triggered:
            trap_q = eval_result.get("trap_question", {})
            console.print(
                f"\n• [bold red][Counterfactual Trap Breakdown][/bold red]\n"
                f"  [bold]Statement:[/bold] \"{trap_q.get('question')}\"\n"
                f"  [red]Your Answer:[/red] Yes (Agreed) | [green]Expected:[/green] No (False)\n"
                f"  [dim]{trap_q.get('explanation')}[/dim]\n"
            )

        # Show descriptive feedback if any
        desc_feedbacks = eval_result.get("descriptive_feedback", [])
        if desc_feedbacks:
            console.print("[dim]Descriptive Evaluation Feedback:[/dim]")
            for df in desc_feedbacks:
                console.print(f"  • Q{df.get('id')}: {df.get('score')}/{df.get('max_score')} pts - {df.get('comment')}")

        with console.status("[bold green]Generating 50-100 word concise explanation..."):
            summary_50_100 = llm.generate_explanation_summary(diff, detected_ticket)

        console.print(
            Panel(
                f"[bold white]Why these changes are here (Summary):[/bold white]\n\n"
                f"{summary_50_100}",
                title="Architectural Explanation & Purpose",
                border_style="cyan"
            )
        )

        # Ask if developer agrees with the changes
        agreed = Confirm.ask(
            "\n[bold magenta]Do you agree with these changes and accept responsibility for committing them?[/bold magenta]",
            default=True
        )

        if not agreed:
            console.print("\n[bold red]Commit Aborted.[/bold red] Please review, refactor, or discuss the changes before committing.")
            sys.exit(1)

        status_label = "ACKNOWLEDGED_WITH_EXPLANATION"

    # Create defense card and trailer
    note_dir = git.get_git_root() or Path.cwd()
    defense_data = {
        "ticket_number": detected_ticket,
        "branch_name": branch,
        "commit_hash": commit_hash,
        "author_name": author_name,
        "author_email": author_email,
        "summary": summary_50_100,
        "detailed_analysis": {
            "files_changed": diff_stats["files_changed"],
            "lines_added": diff_stats["lines_added"],
            "lines_removed": diff_stats["lines_removed"],
        },
        "agreed_with_changes": agreed,
        "passed_verification": passed,
        "status": status_label,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    defense_card_path = NoteGenerator.write_pr_defense_card(note_dir / ".gitcheck", defense_data)
    commit_trailer = NoteGenerator.format_commit_trailer(detected_ticket, summary_50_100, agreed)

    # Save to Supabase (Confidential store of findings and understanding)
    saved, db_msg = supabase.save_review(defense_data)
    if saved:
        db_status = f"[bold green]Synced to Supabase[/bold green] [dim]({supabase.url})[/dim]"
    elif supabase.is_configured():
        db_status = f"[bold red]Supabase Sync Failed:[/bold red] {db_msg} [dim](Cached locally)[/dim]"
    else:
        db_status = "[dim]Cached locally (Run 'git-check set-supabase' to sync to Supabase DB)[/dim]"

    console.print(
        Panel(
            f"[bold green]Pre-Commit Gate Completed Successfully[/bold green]\n\n"
            f"• [bold]Summary Note:[/bold] Added to PR defense artifact\n"
            f"• [bold]Defense Card:[/bold] [link=file://{defense_card_path}]{defense_card_path}[/link]\n"
            f"• [bold]Database:[/bold] {db_status}\n"
            f"• [bold]Review Dashboard:[/bold] {config.dashboard_url}/ticket/{detected_ticket}\n\n"
            f"[dim]Commit Trailer ready:\n{commit_trailer.strip()}[/dim]",
            border_style="green"
        )
    )

    # If run as a git commit-msg or pre-commit hook, we exit 0 so git commit proceeds
    sys.exit(0)

@cli.command()
def install_hook():
    """Install GitCheck as a git pre-commit hook in the current repository."""
    git = GitService()
    success, msg = git.install_pre_commit_hook()
    if success:
        console.print(f"[bold green]✔[/bold green] {msg}")
    else:
        console.print(f"[bold red]✘[/bold red] {msg}")
        sys.exit(1)

@cli.command()
@click.argument("ticket", required=False)
def history(ticket: Optional[str] = None):
    """View previous commit comprehension and review history for a ticket."""
    render_banner()
    git = GitService()
    target_ticket = ticket or git.extract_ticket_number()
    if not target_ticket:
        target_ticket = Prompt.ask("Enter Ticket Number (e.g. PROJ-402)")

    supabase = SupabaseService()
    records = supabase.fetch_ticket_history(target_ticket)

    if not records:
        console.print(f"[yellow]No previous GitCheck reviews found for {target_ticket}.[/yellow]")
        return

    table = Table(title=f"GitCheck History: {target_ticket}")
    table.add_column("Date", style="dim")
    table.add_column("Branch")
    table.add_column("Author")
    table.add_column("Status")
    table.add_column("Summary (50–100 Words)", max_width=50)

    for r in records:
        created = r.get("created_at", "")[:10]
        status_style = "green" if r.get("status") == "PASSED" else "yellow"
        table.add_row(
            created,
            r.get("branch_name", "N/A"),
            r.get("author_name", "N/A"),
            f"[{status_style}]{r.get('status', 'DONE')}[/{status_style}]",
            r.get("summary", "")
        )

    console.print(table)

@cli.command()
@click.argument("api_key", required=False)
def set_gemini(api_key: Optional[str] = None):
    """Save Gemini API key to ~/.gitcheckrc for all repositories."""
    target_key = api_key or Prompt.ask("[cyan]Enter Gemini API Key (starts with AIzaSy...)[/cyan]", password=True)
    if not target_key or not target_key.strip():
        console.print("[red]Error: No API key provided.[/red]")
        return
    home_rc = Path.home() / ".gitcheckrc"
    data = {}
    if home_rc.exists():
        try:
            with open(home_rc, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data["GEMINI_API_KEY"] = target_key.strip()
    with open(home_rc, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    console.print(f"[bold green]✔[/bold green] Gemini API Key saved to [cyan]{home_rc}[/cyan]!")
    console.print("[dim]GitCheck will now automatically use Google Gemini 1.5 Flash for all verification runs.[/dim]")

@cli.command()
@click.option("--url", prompt="[cyan]Enter Supabase Project URL (e.g. https://xyz.supabase.co)[/cyan]")
@click.option("--key", prompt="[cyan]Enter Supabase anon/public key[/cyan]", hide_input=True)
def set_supabase(url: str, key: str):
    """Save Supabase credentials to ~/.gitcheckrc for all repositories."""
    if not url.strip() or not key.strip():
        console.print("[red]Error: URL and key are required.[/red]")
        return
    home_rc = Path.home() / ".gitcheckrc"
    data = {}
    if home_rc.exists():
        try:
            with open(home_rc, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data["SUPABASE_URL"] = url.strip().rstrip("/")
    data["SUPABASE_ANON_KEY"] = key.strip()
    with open(home_rc, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    console.print(f"[bold green]✔[/bold green] Supabase credentials saved to [cyan]{home_rc}[/cyan]!")
    console.print("[dim]GitCheck CLI will now sync all commit verification reviews to your Supabase PostgreSQL DB.[/dim]")

@cli.command()
def sync_supabase():
    """Sync locally cached reviews (.gitcheck_history.json) to Supabase database."""
    render_banner()
    supabase = SupabaseService()
    if not supabase.is_configured():
        console.print("[bold red]Supabase not configured in CLI.[/bold red]")
        console.print("Run [cyan]git-check set-supabase[/cyan] first to configure your credentials.")
        return

    with console.status("[bold green]Syncing local reviews to Supabase..."):
        synced, total, last_err = supabase.sync_local_cache_to_supabase()

    if synced > 0:
        console.print(f"[bold green]✔ Successfully synced {synced} of {total} reviews to Supabase ({supabase.url})![/bold green]")
    elif total == 0:
        console.print("[yellow]No local reviews found to sync in .gitcheck_history.json.[/yellow]")
    else:
        console.print(f"[bold red]✘ Failed to sync reviews to Supabase:[/bold red] {last_err}")

@cli.command()
def config_info():
    """View active GitCheck configuration and provider status."""
    render_banner()
    table = Table(title="GitCheck Configuration Status")
    table.add_column("Setting")
    table.add_column("Value")
    table.add_column("Status")

    provider = config.resolve_provider()
    table.add_row("LLM Provider", provider.upper(), "[green]Active[/green]" if provider != "fallback" else "[yellow]Offline Heuristics[/yellow]")
    table.add_row("Gemini API Key", "***" + config.gemini_api_key[-4:] if config.gemini_api_key else "Not Set", "[green]Configured[/green]" if config.gemini_api_key else "[dim]Optional[/dim]")
    table.add_row("OpenAI API Key", "***" + config.openai_api_key[-4:] if config.openai_api_key else "Not Set", "[green]Configured[/green]" if config.openai_api_key else "[dim]Optional[/dim]")
    table.add_row("Claude API Key", "***" + config.anthropic_api_key[-4:] if config.anthropic_api_key else "Not Set", "[green]Configured[/green]" if config.anthropic_api_key else "[dim]Optional[/dim]")
    table.add_row("Supabase URL", config.supabase_url or "Not Set", "[green]Connected[/green]" if config.supabase_url else "[dim]Using local store[/dim]")
    table.add_row("Comprehension Threshold", f"{config.threshold}%", "[green]Active (80%)[/green]")

    console.print(table)

if __name__ == "__main__":
    cli()
