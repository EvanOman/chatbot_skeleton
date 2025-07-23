"""Rich colorized request/response logging middleware for development."""

import json
import time
from typing import Callable

from fastapi import Request, Response
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from starlette.middleware.base import BaseHTTPMiddleware

console = Console()


class RichLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs requests and responses with rich formatting."""

    def __init__(self, app, enable_logging: bool = True):
        super().__init__(app)
        self.enable_logging = enable_logging

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enable_logging:
            return await call_next(request)

        # Skip logging for static files and health checks
        if (
            request.url.path.startswith("/static")
            or request.url.path == "/favicon.ico"
            or request.url.path == "/health"
        ):
            return await call_next(request)

        start_time = time.time()

        # Log incoming request
        await self._log_request(request)

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log outgoing response
        await self._log_response(request, response, process_time)

        return response

    async def _log_request(self, request: Request):
        """Log incoming request with rich formatting."""
        # Create request info table
        table = Table(title="🔵 Incoming Request", show_header=False)
        table.add_column("Field", style="bold cyan", width=15)
        table.add_column("Value", style="white")

        table.add_row("Method", self._colorize_method(request.method))
        table.add_row("URL", str(request.url))
        table.add_row("Path", request.url.path)

        if request.query_params:
            table.add_row("Query", str(dict(request.query_params)))

        # Add headers (filter sensitive ones)
        if request.headers:
            headers = {
                key: value if key.lower() not in ["authorization", "cookie"] else "***"
                for key, value in request.headers.items()
            }
            for key, value in headers.items():
                if key.lower() in ["content-type", "accept", "user-agent", "host"]:
                    table.add_row(f"Header {key}", value)

        console.print(table)

        # Log request body for POST/PUT/PATCH
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    # Try to parse as JSON for pretty printing
                    try:
                        json_body = json.loads(body.decode())
                        json_str = json.dumps(json_body, indent=2)
                        syntax = Syntax(
                            json_str, "json", theme="monokai", line_numbers=False
                        )
                        console.print(
                            Panel(syntax, title="📝 Request Body", border_style="blue")
                        )
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # If not JSON, show as plain text
                        body_text = body.decode("utf-8", errors="replace")[:500]
                        if len(body) > 500:
                            body_text += "... (truncated)"
                        console.print(
                            Panel(
                                body_text, title="📝 Request Body", border_style="blue"
                            )
                        )
            except Exception:
                pass  # Skip body logging if there's an issue

        console.print()  # Add spacing

    async def _log_response(
        self, request: Request, response: Response, process_time: float
    ):
        """Log outgoing response with rich formatting."""
        # Create response info table
        table = Table(title="🟢 Response", show_header=False)
        table.add_column("Field", style="bold green", width=15)
        table.add_column("Value", style="white")

        status_color = self._get_status_color(response.status_code)
        table.add_row(
            "Status", f"[{status_color}]{response.status_code}[/{status_color}]"
        )
        table.add_row("Time", f"{process_time:.3f}s")

        # Add important response headers
        if hasattr(response, "headers"):
            for key, value in response.headers.items():
                if key.lower() in ["content-type", "content-length", "location"]:
                    table.add_row(f"Header {key}", value)

        console.print(table)

        # Try to log response body for JSON responses
        if hasattr(response, "headers") and response.headers.get(
            "content-type", ""
        ).startswith("application/json"):
            try:
                # This is tricky with FastAPI responses, so we'll skip body logging for now
                # to avoid interfering with the response stream
                pass
            except Exception:
                pass

        # Add a separator line
        console.print("─" * 80, style="dim")
        console.print()

    def _colorize_method(self, method: str) -> str:
        """Return colorized HTTP method."""
        colors = {
            "GET": "green",
            "POST": "blue",
            "PUT": "yellow",
            "PATCH": "orange3",
            "DELETE": "red",
        }
        color = colors.get(method, "white")
        return f"[{color}]{method}[/{color}]"

    def _get_status_color(self, status_code: int) -> str:
        """Return color for status code."""
        if 200 <= status_code < 300:
            return "green"
        elif 300 <= status_code < 400:
            return "yellow"
        elif 400 <= status_code < 500:
            return "red"
        elif status_code >= 500:
            return "bright_red"
        else:
            return "white"
