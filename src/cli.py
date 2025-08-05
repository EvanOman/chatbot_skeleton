"""Interactive CLI for App Management using Typer."""

import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .application.services.chat_service import ChatService
from .application.services.dspy_react_agent import DSPyReactAgent
from .domain.entities.chat_message import ChatMessage
from .domain.entities.chat_thread import ChatThread
from .domain.value_objects.message_role import MessageRole
from .infrastructure.config.ports import PortConfig
from .infrastructure.container.container import Container
from .infrastructure.profiling.profiler import profiler

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


def get_services() -> tuple[Any, Any, Any]:
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
                    user_message=chat_message, thread_id=uuid.UUID(thread_id)
                )
            )
            return response
        finally:
            loop.close()

    except Exception as e:
        return f"Error: {e}"


@app.command()
def status() -> None:
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
            running_services = (
                result.stdout.strip().split("\n") if result.stdout.strip() else []
            )
            if "postgres" in running_services:
                console.print("✅ [bold green]Database[/bold green]: Running")
            else:
                console.print("❌ [bold red]Database[/bold red]: Not running")

            if "adminer" in running_services:
                console.print(
                    f"✅ [bold green]Database GUI[/bold green]: Running ({PortConfig.get_adminer_url()})"
                )
            else:
                console.print("❌ [bold red]Database GUI[/bold red]: Not running")
        else:
            console.print(
                "⚠️ [bold yellow]Docker[/bold yellow]: Unable to check services"
            )

    except Exception as e:
        console.print(f"❌ [bold red]Error[/bold red]: {e}")


@app.command()
def threads(
    user_id: str | None = typer.Option(None, "--user", "-u", help="Filter by user ID"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of threads to show"),
) -> None:
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
        (
            "123e4567-e89b-12d3-a456-426614174000",
            "General Chat",
            "user-1",
            "5",
            "2024-01-15 10:30",
        ),
        (
            "234e5678-f89c-23d4-b567-537725285111",
            "Tech Discussion",
            "user-2",
            "12",
            "2024-01-16 14:22",
        ),
        (
            "345e6789-089d-34e5-c678-648836396222",
            "Project Planning",
            "user-1",
            "8",
            "2024-01-17 09:15",
        ),
    ]

    for thread_id, title, thread_user_id, msg_count, created in sample_threads:
        if user_id is None or thread_user_id == user_id:
            table.add_row(
                thread_id[:8] + "...", title, thread_user_id, msg_count, created
            )

    console.print(table)
    console.print(f"[dim]Showing up to {limit} threads[/dim]")


@app.command()
def messages(
    thread_id: str = typer.Argument(..., help="Thread ID to show messages from"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of messages to show"),
):
    """💬 Show messages from a thread."""
    console.print(
        Panel.fit(f"📝 Messages from Thread: {thread_id[:8]}...", style="bold blue")
    )

    # Sample messages - in real implementation, fetch from database
    sample_messages = [
        ("user", "Hello! How can I analyze this data?", "2024-01-15 10:31:00"),
        (
            "assistant",
            "I'd be happy to help analyze your data! Could you share more details about the dataset?",
            "2024-01-15 10:31:15",
        ),
        (
            "user",
            "It's a CSV with sales data from the last quarter.",
            "2024-01-15 10:32:00",
        ),
        (
            "assistant",
            "Great! For sales data analysis, I can help you with trends, patterns, and visualizations. Would you like me to start with a summary analysis?",
            "2024-01-15 10:32:30",
        ),
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
    user_id: str | None = typer.Option(
        None, "--user", "-u", help="User ID (auto-generated if not provided)"
    ),
):
    """➕ Create a new chat thread."""
    if user_id is None:
        user_id = str(uuid.uuid4())

    thread_id = str(uuid.uuid4())

    console.print(Panel.fit("🆕 Creating New Thread", style="bold green"))
    console.print(f"[bold]Title:[/bold] {title}")
    console.print(f"[bold]Thread ID:[/bold] {thread_id}")
    console.print(f"[bold]User ID:[/bold] {user_id}")
    console.print(
        f"[bold]Created:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # In real implementation, save to database
    console.print("✅ [bold green]Thread created successfully![/bold green]")


@app.command()
def send_message(
    thread_id: str = typer.Argument(..., help="Thread ID"),
    message: str = typer.Argument(..., help="Message content"),
    user_id: str | None = typer.Option(None, "--user", "-u", help="User ID"),
):
    """📤 Send a message to a thread."""
    if user_id is None:
        user_id = str(uuid.uuid4())

    console.print(
        Panel.fit(
            f"📤 Sending Message to Thread: {thread_id[:8]}...", style="bold green"
        )
    )
    console.print(f"[bold]User:[/bold] {user_id}")
    console.print(f"[bold]Message:[/bold] {message}")
    console.print(
        f"[bold]Timestamp:[/bold] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

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
    user_id: str | None = typer.Option(None, "--user", "-u", help="User ID"),
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
        (
            "create-migration",
            "uv run alembic revision --autogenerate -m 'message'",
            "Create new migration",
        ),
        (
            "seed",
            "uv run python seed_database.py",
            "Seed database with example data for API docs",
        ),
        ("reset", "docker-compose down && docker-compose up -d", "Reset database"),
        (
            "gui",
            "open " + PortConfig.get_adminer_url() + "",
            "Open database GUI (Adminer)",
        ),
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
    key: str | None = typer.Option(
        None, "--key", "-k", help="Configuration key to check"
    ),
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
        console.print(
            "Use --show to display configuration or --key to check a specific value"
        )


@app.command()
def info():
    """ℹ️ Show application information."""
    console.print(Panel.fit("ℹ️ Sample Chat App Information", style="bold blue"))

    info_data = [
        ("Version", "0.1.0"),
        (
            "Python",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ),
        ("Framework", "FastAPI + SQLAlchemy"),
        ("AI Engine", "DSPy REACT Agent"),
        ("Database", "PostgreSQL"),
        ("Package Manager", "uv"),
        ("Web Interface", PortConfig.get_app_url()),
        ("API Docs", "" + PortConfig.get_app_url() + "/docs"),
        ("Database GUI", PortConfig.get_adminer_url()),
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for prop, value in info_data:
        table.add_row(prop, value)

    console.print(table)


@app.command()
def test_agent(
    test_case: str = typer.Option(
        "calculator",
        "--case",
        "-c",
        help="Test case: calculator, search, weather, memory",
    ),
):
    """🧪 Test agent capabilities with predefined test cases."""
    console.print(
        Panel.fit(f"🧪 Testing Agent: {test_case.title()}", style="bold blue")
    )

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


@app.command()
def profile(
    profile_type: str = typer.Option(
        "flamegraph",
        "--type",
        "-t",
        help="Profile type: flamegraph, speedscope, memory, cprofile",
    ),
    duration: int = typer.Option(
        30, "--duration", "-d", help="Profile duration in seconds"
    ),
    rate: int = typer.Option(100, "--rate", "-r", help="Sampling rate per second"),
    output_format: str = typer.Option("auto", "--format", "-f", help="Output format"),
):
    """🔬 Profile application performance."""
    console.print(Panel.fit("🔬 Performance Profiling", style="bold blue"))

    if profile_type == "flamegraph":
        output_file = profiler.profile_with_py_spy(
            duration=duration, rate=rate, output_format="flamegraph"
        )
        if output_file:
            console.print(
                f"🔥 [bold green]Flame graph generated:[/bold green] {output_file}"
            )
            console.print(
                "💡 [dim]Open the SVG file in your browser to view the interactive flame graph[/dim]"
            )

    elif profile_type == "speedscope":
        output_file = profiler.profile_with_py_spy(
            duration=duration, rate=rate, output_format="speedscope"
        )
        if output_file:
            console.print(
                f"📈 [bold green]Speedscope profile generated:[/bold green] {output_file}"
            )
            console.print("💡 [dim]Upload to https://speedscope.app to visualize[/dim]")

    elif profile_type == "memory":
        output_file = profiler.profile_memory_usage(duration=duration)
        if output_file:
            console.print(
                f"🧠 [bold green]Memory profile generated:[/bold green] {output_file}"
            )

    elif profile_type == "cprofile":
        console.print("⚠️ [bold yellow]cProfile requires code integration[/bold yellow]")
        console.print(
            "Use the @profile_function decorator or context manager in your code"
        )
        console.print("Example:")
        console.print(
            """
        from src.infrastructure.profiling.profiler import profile_function

        @profile_function("my_function")
        def my_expensive_function():
            # your code here
            pass
        """
        )

    else:
        console.print(f"❌ [bold red]Unknown profile type:[/bold red] {profile_type}")
        console.print("Available types: flamegraph, speedscope, memory, cprofile")


@app.command()
def profiles():
    """📊 List and manage performance profiles."""
    console.print(Panel.fit("📊 Performance Profiles", style="bold blue"))

    # List profiles
    table = profiler.list_profiles()
    console.print(table)

    # Show profile directory info
    profile_dir = profiler.config.profile_output_dir
    if profile_dir.exists():
        total_files = len(list(profile_dir.glob("*")))
        total_size = sum(f.stat().st_size for f in profile_dir.glob("*"))

        size_mb = total_size / (1024 * 1024)
        console.print(f"\n📁 [bold]Profile Directory:[/bold] {profile_dir}")
        console.print(f"📊 [bold]Total Files:[/bold] {total_files}")
        console.print(f"💾 [bold]Total Size:[/bold] {size_mb:.1f} MB")

        if total_files > 0:
            console.print(
                "\n💡 [bold yellow]Tip:[/bold yellow] Use 'uv run chatapp profile-cleanup' to remove old profiles"
            )


@app.command()
def profile_cleanup(
    days: int = typer.Option(
        7, "--days", "-d", help="Delete profiles older than N days"
    ),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """🗑️ Clean up old performance profiles."""
    console.print(Panel.fit("🗑️ Profile Cleanup", style="bold yellow"))

    if not confirm:
        response = typer.confirm(f"Delete profiles older than {days} days?")
        if not response:
            console.print("❌ [bold red]Cleanup cancelled[/bold red]")
            return

    deleted_count = profiler.cleanup_old_profiles(days)

    if deleted_count > 0:
        console.print(
            f"✅ [bold green]Deleted {deleted_count} old profile(s)[/bold green]"
        )
    else:
        console.print("ℹ️ [bold blue]No old profiles to delete[/bold blue]")


@app.command()
def profile_report():
    """📋 Generate performance profiling report."""
    console.print(Panel.fit("📋 Performance Report", style="bold blue"))

    report = profiler.generate_performance_report()

    # Save report to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = (
        profiler.config.profile_output_dir / f"performance_report_{timestamp}.md"
    )

    with open(report_file, "w") as f:
        f.write(report)

    console.print(f"📄 [bold green]Report saved to:[/bold green] {report_file}")
    console.print("\n" + "=" * 50)
    console.print(report)


@app.command()
def visualize(
    thread_id: str = typer.Argument(..., help="Thread ID to visualize"),
    open_browser: bool = typer.Option(
        True, "--open", "-o", help="Open browser automatically"
    ),
):
    """🌳 Visualize a chat thread as an interactive tree."""
    console.print(Panel.fit("🌳 Thread Visualization", style="bold blue"))

    try:
        # Validate UUID format
        uuid.UUID(thread_id)
    except ValueError:
        console.print(f"❌ [bold red]Invalid UUID format:[/bold red] {thread_id}")
        return

    visualization_url = (
        "" + PortConfig.get_app_url() + "/api/visualization/thread/{thread_id}/tree"
    )

    console.print(f"🌐 [bold green]Visualization URL:[/bold green] {visualization_url}")

    if open_browser:
        try:
            import webbrowser

            webbrowser.open(visualization_url)
            console.print("🚀 [bold green]Opening in browser...[/bold green]")
        except Exception as e:
            console.print(f"⚠️ [bold yellow]Could not open browser:[/bold yellow] {e}")
            console.print("💡 Please open the URL manually in your browser")
    else:
        console.print("💡 Copy the URL above and open it in your browser")


@app.command()
def overview(
    open_browser: bool = typer.Option(
        True, "--open", "-o", help="Open browser automatically"
    ),
):
    """📊 Show threads overview dashboard."""
    console.print(Panel.fit("📊 Threads Overview", style="bold blue"))

    overview_url = "" + PortConfig.get_app_url() + "/api/visualization/threads/overview"

    console.print(f"🌐 [bold green]Overview URL:[/bold green] {overview_url}")

    if open_browser:
        try:
            import webbrowser

            webbrowser.open(overview_url)
            console.print("🚀 [bold green]Opening in browser...[/bold green]")
        except Exception as e:
            console.print(f"⚠️ [bold yellow]Could not open browser:[/bold yellow] {e}")
            console.print("💡 Please open the URL manually in your browser")
    else:
        console.print("💡 Copy the URL above and open it in your browser")


@app.command()
def export(
    thread_id: str = typer.Argument(..., help="Thread ID to export"),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json, csv, markdown, html"
    ),
    output_dir: str = typer.Option(
        ".", "--output", "-o", help="Output directory for exported file"
    ),
    include_metadata: bool = typer.Option(
        True, "--metadata/--no-metadata", help="Include message metadata"
    ),
):
    """💾 Export a chat thread to a file."""
    console.print(Panel.fit("💾 Thread Export", style="bold blue"))

    try:
        # Validate UUID format
        uuid.UUID(thread_id)
    except ValueError:
        console.print(f"❌ [bold red]Invalid UUID format:[/bold red] {thread_id}")
        return

    if format.lower() not in ["json", "csv", "markdown", "html"]:
        console.print(
            f"❌ [bold red]Invalid format:[/bold red] {format}. Use: json, csv, markdown, html"
        )
        return

    export_url = "" + PortConfig.get_app_url() + "/api/export/thread/{thread_id}"
    params = {"format": format.lower(), "include_metadata": include_metadata}

    console.print(f"📄 [bold cyan]Exporting thread:[/bold cyan] {thread_id[:8]}...")
    console.print(f"📝 [bold cyan]Format:[/bold cyan] {format.upper()}")
    console.print(f"📊 [bold cyan]Include metadata:[/bold cyan] {include_metadata}")

    try:
        import requests  # type: ignore[import-untyped]

        with console.status("[bold green]Downloading export..."):
            response = requests.get(export_url, params=params)

        if response.status_code == 200:
            # Extract filename from Content-Disposition header
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[1].strip('"')
            else:
                filename = f"thread_export_{thread_id[:8]}.{format.lower()}"

            output_path = Path(output_dir) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            console.print("✅ [bold green]Export successful![/bold green]")
            console.print(f"📁 [bold green]Saved to:[/bold green] {output_path}")

            # Show file size
            file_size = output_path.stat().st_size
            size_str = (
                f"{file_size / 1024:.1f} KB"
                if file_size > 1024
                else f"{file_size} bytes"
            )
            console.print(f"📊 [bold blue]File size:[/bold blue] {size_str}")

        elif response.status_code == 404:
            console.print("❌ [bold red]Thread not found[/bold red]")
        else:
            console.print(
                f"❌ [bold red]Export failed:[/bold red] HTTP {response.status_code}"
            )
            console.print(response.text)

    except ImportError:
        console.print(
            "❌ [bold red]requests library not available. Install with:[/bold red] uv add requests"
        )
    except Exception as e:
        console.print(f"❌ [bold red]Export failed:[/bold red] {e}")


@app.command()
def export_formats():
    """📋 Show available export formats and their descriptions."""
    console.print(Panel.fit("📋 Export Formats", style="bold blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Format", style="cyan", no_wrap=True)
    table.add_column("Extension", style="yellow")
    table.add_column("Description", style="green")
    table.add_column("Best For", style="blue")

    formats = [
        (
            "JSON",
            ".json",
            "Structured data with complete metadata",
            "API integration, data processing",
        ),
        (
            "CSV",
            ".csv",
            "Tabular format for spreadsheet analysis",
            "Data analysis, Excel import",
        ),
        (
            "Markdown",
            ".md",
            "Human-readable formatted text",
            "Documentation, GitHub README",
        ),
        (
            "HTML",
            ".html",
            "Styled web page ready for viewing",
            "Printing, web sharing, archival",
        ),
    ]

    for format_name, ext, desc, best_for in formats:
        table.add_row(format_name, ext, desc, best_for)

    console.print(table)

    console.print("\n💡 [bold yellow]Usage examples:[/bold yellow]")
    console.print("  uv run chatapp export <thread-id> --format json")
    console.print("  uv run chatapp export <thread-id> --format html --no-metadata")
    console.print(
        "  uv run chatapp export <thread-id> --format csv --output ./exports/"
    )


@app.command()
def webhooks():
    """🪝 Manage webhook configurations."""
    console.print(Panel.fit("🪝 Webhook Management", style="bold blue"))

    console.print("Available webhook commands:")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    commands = [
        ("list", "List all configured webhooks"),
        ("create", "Create a new webhook configuration"),
        ("test", "Send a test event to a webhook"),
        ("history", "View webhook delivery history"),
        ("events", "List available event types"),
    ]

    for cmd, desc in commands:
        table.add_row(f"uv run chatapp webhook-{cmd}", desc)

    console.print(table)

    console.print("\n💡 [bold yellow]Example webhook creation:[/bold yellow]")
    console.print("  curl -X POST " + PortConfig.get_app_url() + "/api/webhooks/ \\")
    console.print("    -H 'Content-Type: application/json' \\")
    console.print("    -d '{")
    console.print('      "name": "My Webhook",')
    console.print('      "url": "https://my-app.com/webhook",')
    console.print('      "events": ["message_created", "agent_response"]')
    console.print("    }'")


@app.command("webhook-list")
def webhook_list():
    """📋 List all configured webhooks."""
    console.print(Panel.fit("📋 Webhook List", style="bold blue"))

    try:
        import requests  # type: ignore[import-untyped]

        with console.status("[bold green]Fetching webhooks..."):
            response = requests.get("" + PortConfig.get_app_url() + "/api/webhooks/")

        if response.status_code == 200:
            webhooks = response.json()

            if not webhooks:
                console.print("ℹ️ [bold blue]No webhooks configured[/bold blue]")
                return

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="green")
            table.add_column("URL", style="yellow")
            table.add_column("Events", style="blue")
            table.add_column("Active", style="red")
            table.add_column("Last Triggered", style="dim")

            for webhook in webhooks:
                status_icon = "✅" if webhook["active"] else "❌"
                events_str = ", ".join(webhook["events"][:2])
                if len(webhook["events"]) > 2:
                    events_str += f" (+{len(webhook['events']) - 2})"

                last_triggered = webhook.get("last_triggered")
                if last_triggered:
                    from datetime import datetime

                    dt = datetime.fromisoformat(last_triggered.replace("Z", "+00:00"))
                    last_triggered_str = dt.strftime("%m/%d %H:%M")
                else:
                    last_triggered_str = "Never"

                table.add_row(
                    webhook["id"][:8] + "...",
                    webhook["name"],
                    (
                        str(webhook["url"])[:30] + "..."
                        if len(str(webhook["url"])) > 30
                        else str(webhook["url"])
                    ),
                    events_str,
                    status_icon,
                    last_triggered_str,
                )

            console.print(table)
            console.print(
                f"\n📊 [bold blue]Total webhooks:[/bold blue] {len(webhooks)}"
            )
        else:
            console.print(
                f"❌ [bold red]Failed to fetch webhooks:[/bold red] HTTP {response.status_code}"
            )

    except ImportError:
        console.print("❌ [bold red]requests library not available[/bold red]")
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {e}")


@app.command("webhook-events")
def webhook_events():
    """📡 List available webhook event types."""
    console.print(Panel.fit("📡 Webhook Events", style="bold blue"))

    try:
        import requests  # type: ignore[import-untyped]

        with console.status("[bold green]Fetching event types..."):
            response = requests.get(
                "" + PortConfig.get_app_url() + "/api/webhooks/events/types"
            )

        if response.status_code == 200:
            data = response.json()
            event_types = data["event_types"]

            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Event Type", style="cyan", no_wrap=True)
            table.add_column("Description", style="green")
            table.add_column("Example Data Keys", style="yellow")

            for event_type in event_types:
                example_keys = list(event_type["example_data"].keys())[:3]
                keys_str = ", ".join(example_keys)
                if len(event_type["example_data"]) > 3:
                    keys_str += "..."

                table.add_row(event_type["name"], event_type["description"], keys_str)

            console.print(table)
            console.print(
                f"\n📊 [bold blue]Total event types:[/bold blue] {len(event_types)}"
            )
        else:
            console.print(
                f"❌ [bold red]Failed to fetch event types:[/bold red] HTTP {response.status_code}"
            )

    except ImportError:
        console.print("❌ [bold red]requests library not available[/bold red]")
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {e}")


@app.command("webhook-test")
def webhook_test(
    webhook_id: str = typer.Argument(..., help="Webhook ID to test"),
):
    """🧪 Send a test event to a webhook."""
    console.print(Panel.fit("🧪 Webhook Test", style="bold blue"))

    try:
        import requests  # type: ignore[import-untyped]

        console.print(f"📡 [bold cyan]Testing webhook:[/bold cyan] {webhook_id[:8]}...")

        with console.status("[bold green]Sending test event..."):
            response = requests.post(
                "" + PortConfig.get_app_url() + "/api/webhooks/{webhook_id}/test"
            )

        if response.status_code == 200:
            result = response.json()

            if result["success"]:
                console.print("✅ [bold green]Test successful![/bold green]")
                console.print(
                    f"📊 [bold blue]Status Code:[/bold blue] {result['status_code']}"
                )
                if result.get("response_body"):
                    console.print(
                        f"📄 [bold blue]Response:[/bold blue] {result['response_body'][:100]}..."
                    )
            else:
                console.print("❌ [bold red]Test failed![/bold red]")
                if result.get("error"):
                    console.print(f"❌ [bold red]Error:[/bold red] {result['error']}")
                if result.get("status_code"):
                    console.print(
                        f"📊 [bold blue]Status Code:[/bold blue] {result['status_code']}"
                    )
        else:
            console.print(
                f"❌ [bold red]Request failed:[/bold red] HTTP {response.status_code}"
            )

    except ImportError:
        console.print("❌ [bold red]requests library not available[/bold red]")
    except Exception as e:
        console.print(f"❌ [bold red]Error:[/bold red] {e}")


if __name__ == "__main__":
    app()
