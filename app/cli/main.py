"""Interactive Typer / Rich CLI utility for testing and operating fast-api-archon."""

import asyncio
import json
import sys
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from app.core.database import AsyncSessionLocal, init_db
from app.services.seed_data import seed_database
from app.domains.auth.router import AuthRepository, AuthService
from app.domains.interview.router import InterviewRepository
from app.domains.reports.router import ReportRepository
from app.domains.quiz.router import QuizRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest

app = typer.Typer(help="Archon: AI-Native System Design Interview Platform CLI")
console = Console()


@app.command()
def seed():
    """Seed system design questions and quiz decks into local database."""
    async def _seed():
        await init_db()
        async with AsyncSessionLocal() as db:
            await seed_database(db)
        console.print("[green]✓ Database seeded with system design questions and quiz decks.[/green]")
    asyncio.run(_seed())


@app.command()
def questions():
    """List all available system design interview questions."""
    async def _list():
        await init_db()
        async with AsyncSessionLocal() as db:
            repo = InterviewRepository(db)
            qs = await repo.list_questions()

        table = Table(title="Archon System Design Questions Bank")
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="bold white")
        table.add_column("Difficulty", style="magenta")
        table.add_column("Time Limit", style="yellow")
        table.add_column("Key Topics", style="green")

        for q in qs:
            table.add_row(
                q.id,
                q.title,
                q.difficulty,
                f"{q.time_limit_minutes} min",
                ", ".join(q.expected_topics[:3]) if q.expected_topics else "-",
            )
        console.print(table)
    asyncio.run(_list())


@app.command()
def register(name: str, email: str, password: str = "Password123!"):
    """Register a new candidate account via CLI."""
    async def _reg():
        await init_db()
        async with AsyncSessionLocal() as db:
            service = AuthService(AuthRepository(db))
            res = await service.register(UserRegisterRequest(name=name, email=email, password=password))
        console.print(Panel(f"[green]Registered candidate:[/green] {res.name} ({res.email})\n[yellow]Access Token:[/yellow] {res.access_token[:30]}..."))
    asyncio.run(_reg())


@app.command()
def start(question_id: str, email: str = "demo@archon.dev"):
    """Start a new system design interview session."""
    async def _start():
        await init_db()
        async with AsyncSessionLocal() as db:
            auth_repo = AuthRepository(db)
            user = await auth_repo.get_by_email(email)
            if not user:
                user = await auth_repo.create_user("Candidate", email, "hashed_pw")
            repo = InterviewRepository(db)
            it = await repo.create_interview(user.id, question_id)
            q = await repo.get_question(question_id)
        console.print(Panel(
            f"[bold green]Interview Session Started![/bold green]\n"
            f"Session ID: [cyan]{it.id}[/cyan]\n"
            f"Question: [white]{q.title if q else question_id}[/white]\n"
            f"Phase: [yellow]{it.current_phase}[/yellow]\n"
            f"Connect via WebSocket: ws://localhost:8080/ai/chat?interview_id={it.id}"
        ))
    asyncio.run(_start())


@app.command()
def submit(interview_id: str, email: str = "demo@archon.dev"):
    """Submit an interview session for AI scoring and evaluation."""
    async def _submit():
        await init_db()
        async with AsyncSessionLocal() as db:
            auth_repo = AuthRepository(db)
            user = await auth_repo.get_by_email(email)
            if not user:
                console.print("[red]User not found.[/red]")
                return
            repo = InterviewRepository(db)
            it = await repo.submit_interview(interview_id, user.id, "Candidate completed whiteboard and QPS math.")
            report_repo = ReportRepository(db)
            rep = await report_repo.create_default_report(interview_id)
        console.print(Panel(
            f"[bold green]Interview Submitted & Scored![/bold green]\n"
            f"Overall Score: [yellow]{rep.overall_score}/100[/yellow]\n"
            f"Requirements: {rep.requirements_score}/100 | Architecture: {rep.architecture_score}/100\n"
            f"Scalability: {rep.scalability_score}/100 | Estimation: {rep.estimation_score}/100"
        ))
    asyncio.run(_submit())


@app.command()
def quiz():
    """List quiz decks and take the daily architecture challenge."""
    async def _quiz():
        await init_db()
        async with AsyncSessionLocal() as db:
            repo = QuizRepository(db)
            decks = await repo.list_decks()
            daily = await repo.get_daily_challenge()

        table = Table(title="System Design Quiz Decks")
        table.add_column("Deck ID", style="cyan")
        table.add_column("Title", style="bold white")
        table.add_column("Category", style="green")
        table.add_column("Difficulty", style="magenta")

        for d in decks:
            table.add_row(d.id, d.title, d.category, d.difficulty)
        console.print(table)

        if daily:
            console.print(Panel(f"[bold yellow]Daily Architecture Challenge:[/bold yellow]\n{daily.question}\n[italic]{daily.scenario}[/italic]"))
    asyncio.run(_quiz())


@app.command()
def health():
    """Verify health and database connection."""
    async def _health():
        await init_db()
        console.print("[green]✓ System healthy. Database connected and tables verified.[/green]")
    asyncio.run(_health())


if __name__ == "__main__":
    app()
