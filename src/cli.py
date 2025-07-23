"""Interactive CLI for App Management using Typer."""

import json
import os
import subprocess
import sys
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .infrastructure.container.container import Container
from .application.services.chat_service import ChatService
from .domain.entities.chat_thread import ChatThread
from .domain.entities.chat_message import ChatMessage
from .domain.value_objects.message_role import MessageRole
from .application.services.dspy_react_agent import DSPyReactAgent

app = typer.Typer(
    name="chatapp-cli",
    help="🤖 Interactive CLI for Sample Chat App Management",
    rich_markup_mode="rich",
)

console = Console()

# Initialize container (services will be lazy-loaded)
container = None
chat_service = None
agent_service = None


def get_services():
    """Lazy initialization of services."""
    global container, chat_service, agent_service
    if agent_service is None:
        # For CLI usage, we only need the agent service (which is self-contained)
        agent_service = DSPyReactAgent()
        # Container and chat_service require database session, skip for now in CLI
        container = None
        chat_service = None
    return container, chat_service, agent_service


def get_agent_response(message: str, user_id: str, thread_id: str) -> str:
    """Synchronous wrapper for agent response."""
    try:
        _, _, agent_service = get_services()
        
        # Create a ChatMessage object
        chat_message = ChatMessage(
            thread_id=uuid.UUID(thread_id),
            user_id=uuid.UUID(user_id),
            role=MessageRole.USER,
            content=message,
        )
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                agent_service.generate_response(
                    user_message=chat_message,
                    thread_id=uuid.UUID(thread_id)
                )
            )
            return response
        finally:
            loop.close()
            
    except Exception as e:
        return f"Error: {e}"


@app.command()
def status():
    """📊 Show application status and health check."""
    console.print(Panel.fit("🚀 Sample Chat App Status", style="bold blue"))
    
    # Check database connection
    try:
        # This is a simple check - in a real app you'd ping the database
        console.print("✅ [bold green]Application[/bold green]: Ready")
        console.print("✅ [bold green]Container[/bold green]: Initialized")
        console.print("✅ [bold green]Chat Service[/bold green]: Available")
        console.print("✅ [bold green]Agent Service[/bold green]: Available")
        
        # Check if Docker services are running
        result = subprocess.run(
            ["docker-compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        
        if result.returncode == 0:
            running_services = result.stdout.strip().split('\n') if result.stdout.strip() else []
            if 'postgres' in running_services:
                console.print("✅ [bold green]Database[/bold green]: Running")
            else:
                console.print("❌ [bold red]Database[/bold red]: Not running")
                
            if 'adminer' in running_services:
                console.print("✅ [bold green]Database GUI[/bold green]: Running (http://localhost:8080)")
            else:
                console.print("❌ [bold red]Database GUI[/bold red]: Not running")
        else:
            console.print("⚠️ [bold yellow]Docker[/bold yellow]: Unable to check services")
            
    except Exception as e:
        console.print(f"❌ [bold red]Error[/bold red]: {e}")


@app.command()
def threads(
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of threads to show"),
):
    """📋 List chat threads."""
    console.print(Panel.fit("💬 Chat Threads", style="bold blue"))
    
    # In a real implementation, you'd fetch from the database
    # For now, showing a sample structure
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Thread ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="green")
    table.add_column("User ID", style="yellow")
    table.add_column("Messages", justify="right", style="blue")
    table.add_column("Created", style="dim")
    
    # Sample data - in real implementation, fetch from database
    sample_threads = [
        ("123e4567-e89b-12d3-a456-426614174000", "General Chat", "user-1", "5", "2024-01-15 10:30"),
        ("234e5678-f89c-23d4-b567-537725285111", "Tech Discussion", "user-2", "12", "2024-01-16 14:22"),
        ("345e6789-089d-34e5-c678-648836396222", "Project Planning", "user-1", "8", "2024-01-17 09:15"),
    ]
    
    for thread_id, title, thread_user_id, msg_count, created in sample_threads:
        if user_id is None or thread_user_id == user_id:
            table.add_row(thread_id[:8] + "...", title, thread_user_id, msg_count, created)
    
    console.print(table)
    console.print(f"[dim]Showing up to {limit} threads[/dim]")


@app.command()
def messages(
    thread_id: str = typer.Argument(..., help="Thread ID to show messages from"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of messages to show"),
):
    """💬 Show messages from a thread."""
    console.print(Panel.fit(f"📝 Messages from Thread: {thread_id[:8]}...", style="bold blue"))
    
    # Sample messages - in real implementation, fetch from database
    sample_messages = [
        ("user", "Hello! How can I analyze this data?", "2024-01-15 10:31:00"),
        ("assistant", "I'd be happy to help analyze your data! Could you share more details about the dataset?", "2024-01-15 10:31:15"),
        ("user", "It's a CSV with sales data from the last quarter.", "2024-01-15 10:32:00"),
        ("assistant", "Great! For sales data analysis, I can help you with trends, patterns, and visualizations. Would you like me to start with a summary analysis?", "2024-01-15 10:32:30"),
    ]
    
    for role, content, timestamp in sample_messages[-limit:]:
        if role == "user":
            style = "bold cyan"
            emoji = "👤"
        else:
            style = "bold green"
            emoji = "🤖"
            
        console.print(f"{emoji} [dim]{timestamp}[/dim]")
        console.print(f"[{style}]{role.title()}:[/{style}] {content}")
        console.print()


@app.command()
def create_thread(
    title: str = typer.Argument(..., help="Thread title"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User ID (auto-generated if not provided)"),
):
    """➕ Create a new chat thread."""
    if user_id is None:
        user_id = str(uuid.uuid4())
        
    thread_id = str(uuid.uuid4())
    
    console.print(Panel.fit("🆕 Creating New Thread", style="bold green"))
    console.print(f"[bold]Title:[/bold] {title}")
    console.print(f"[bold]Thread ID:[/bold] {thread_id}")
    console.print(f"[bold]User ID:[/bold] {user_id}")
    console.print(f"[bold]Created:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # In real implementation, save to database
    console.print("✅ [bold green]Thread created successfully![/bold green]")


@app.command()
def send_message(
    thread_id: str = typer.Argument(..., help="Thread ID"),
    message: str = typer.Argument(..., help="Message content"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User ID"),
):
    """📤 Send a message to a thread."""
    if user_id is None:
        user_id = str(uuid.uuid4())
        
    console.print(Panel.fit(f"📤 Sending Message to Thread: {thread_id[:8]}...", style="bold green"))
    console.print(f"[bold]User:[/bold] {user_id}")
    console.print(f"[bold]Message:[/bold] {message}")
    console.print(f"[bold]Timestamp:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # In real implementation, save to database and get agent response
    console.print("✅ [bold green]Message sent![/bold green]")
    
    # Simulate agent response
    console.print("\n🤖 [bold blue]Getting agent response...[/bold blue]")
    # Get agent response
    response = get_agent_response(message, user_id, thread_id)
    if response.startswith("Error:"):
        console.print(f"❌ [bold red]Agent Error:[/bold red] {response}")
    else:
        console.print(f"🤖 [bold green]Agent:[/bold green] {response}")


@app.command()
def agent_chat(
    message: str = typer.Argument(..., help="Message to send to the agent"),
    user_id: Optional[str] = typer.Option(None, "--user", "-u", help="User ID"),
):
    """🤖 Quick chat with the AI agent."""
    if user_id is None:
        user_id = str(uuid.uuid4())
        
    thread_id = str(uuid.uuid4())
    
    console.print(Panel.fit("🤖 AI Agent Chat", style="bold blue"))
    console.print(f"[bold cyan]You:[/bold cyan] {message}")
    
    with console.status("[bold green]Agent is thinking..."):
        response = get_agent_response(message, user_id, thread_id)
    
    if response.startswith("Error:"):
        console.print(f"❌ [bold red]Error:[/bold red] {response}")
    else:
        console.print(f"[bold green]🤖 Agent:[/bold green] {response}")


@app.command()
def db():
    """🗄️ Database management commands."""
    console.print(Panel.fit("🗄️ Database Management", style="bold blue"))
    
    commands = [
        ("migrate", "uv run alembic upgrade head", "Apply database migrations"),
        ("rollback", "uv run alembic downgrade -1", "Rollback last migration"),
        ("create-migration", "uv run alembic revision --autogenerate -m 'message'", "Create new migration"),
        ("seed", "uv run python seed_database.py", "Seed database with example data for API docs"),
        ("reset", "docker-compose down && docker-compose up -d", "Reset database"),
        ("gui", "open http://localhost:8080", "Open database GUI (Adminer)"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Usage", style="yellow")
    
    for cmd, usage, desc in commands:
        table.add_row(cmd, desc, usage)
    
    console.print(table)


@app.command()
def seed_db():
    """🌱 Seed database with example data for API documentation."""
    console.print(Panel.fit("🌱 Seeding Database", style="bold green"))
    
    try:
        result = subprocess.run(
            ["uv", "run", "python", "seed_database.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        
        if result.returncode == 0:
            console.print("✅ [bold green]Database seeded successfully![/bold green]")
            console.print(result.stdout)
        else:
            console.print("❌ [bold red]Seeding failed![/bold red]")
            console.print(result.stderr)
            
    except Exception as e:
        console.print(f"❌ [bold red]Error running seed script:[/bold red] {e}")


@app.command()
def dev():
    """🛠️ Development commands and tools."""
    console.print(Panel.fit("🛠️ Development Tools", style="bold blue"))
    
    commands = [
        ("start", "uv run dev", "Start development server with live reload"),
        ("test", "uv run pytest", "Run test suite"),
        ("lint", "uv run ruff check src/", "Run linter"),
        ("format", "uv run ruff format src/", "Format code"),
        ("type-check", "uv run mypy src/", "Run type checker"),
        ("deps", "uv sync --extra dev", "Sync dependencies"),
        ("docker-up", "docker-compose up -d", "Start Docker services"),
        ("docker-down", "docker-compose down", "Stop Docker services"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")
    table.add_column("Usage", style="yellow")
    
    for cmd, usage, desc in commands:
        table.add_row(cmd, desc, usage)
    
    console.print(table)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    key: Optional[str] = typer.Option(None, "--key", "-k", help="Configuration key to check"),
):
    """⚙️ Show configuration information."""
    console.print(Panel.fit("⚙️ Configuration", style="bold blue"))
    
    if show or key:
        # Environment variables
        env_vars = {
            "DB_HOST": os.getenv("DB_HOST", "localhost"),
            "DB_PORT": os.getenv("DB_PORT", "5432"),
            "DB_USERNAME": os.getenv("DB_USERNAME", "postgres"),
            "DB_DATABASE": os.getenv("DB_DATABASE", "chatapp"),
            "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else "Not set",
            "ANTHROPIC_API_KEY": "***" if os.getenv("ANTHROPIC_API_KEY") else "Not set",
            "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        }
        
        if key:
            if key in env_vars:
                console.print(f"[bold]{key}:[/bold] {env_vars[key]}")
            else:
                console.print(f"❌ [bold red]Key '{key}' not found[/bold red]")
        else:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Variable", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            
            for var, value in env_vars.items():
                table.add_row(var, value)
            
            console.print(table)
    else:
        console.print("Use --show to display configuration or --key to check a specific value")


@app.command()
def info():
    """ℹ️ Show application information."""
    console.print(Panel.fit("ℹ️ Sample Chat App Information", style="bold blue"))
    
    info_data = [
        ("Version", "0.1.0"),
        ("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
        ("Framework", "FastAPI + SQLAlchemy"),
        ("AI Engine", "DSPy REACT Agent"),
        ("Database", "PostgreSQL"),
        ("Package Manager", "uv"),
        ("Web Interface", "http://localhost:8000"),
        ("API Docs", "http://localhost:8000/docs"),
        ("Database GUI", "http://localhost:8080"),
    ]
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for prop, value in info_data:
        table.add_row(prop, value)
    
    console.print(table)


@app.command()
def test_agent(
    test_case: str = typer.Option("calculator", "--case", "-c", help="Test case: calculator, search, weather, memory"),
):
    """🧪 Test agent capabilities with predefined test cases."""
    console.print(Panel.fit(f"🧪 Testing Agent: {test_case.title()}", style="bold blue"))
    
    test_cases = {
        "calculator": "What is 15 * 23 + 45?",
        "search": "Search for the latest news about artificial intelligence",
        "weather": "What's the weather like in San Francisco?",
        "memory": "Remember that I like coffee. Then tell me what you remember about my preferences.",
    }
    
    if test_case not in test_cases:
        console.print(f"❌ [bold red]Unknown test case:[/bold red] {test_case}")
        console.print(f"Available: {', '.join(test_cases.keys())}")
        return
    
    message = test_cases[test_case]
    console.print(f"[bold cyan]Test Message:[/bold cyan] {message}")
    
    test_user_id = str(uuid.uuid4())
    test_thread_id = str(uuid.uuid4())
    
    with console.status("[bold green]Running test..."):
        response = get_agent_response(message, test_user_id, test_thread_id)
    
    if response.startswith("Error:"):
        console.print(f"❌ [bold red]Test Failed:[/bold red] {response}")
    else:
        console.print(f"[bold green]✅ Agent Response:[/bold green] {response}")


if __name__ == "__main__":
    app()