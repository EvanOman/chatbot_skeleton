"""
Performance profiling utilities for the Sample Chat App.

This module provides integrated profiling capabilities using py-spy, cProfile,
and other performance analysis tools with easy-to-use interfaces.
"""

import asyncio
import contextlib
import cProfile
import io
import os
import pstats
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


class ProfilerConfig:
    """Configuration for profiling options."""

    def __init__(self):
        self.enable_profiling = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        self.profile_output_dir = Path(os.getenv("PROFILE_OUTPUT_DIR", "./profiles"))
        self.py_spy_rate = int(os.getenv("PY_SPY_RATE", "100"))  # samples per second
        self.py_spy_duration = int(os.getenv("PY_SPY_DURATION", "30"))  # seconds
        self.auto_open_flame_graph = (
            os.getenv("AUTO_OPEN_FLAME_GRAPH", "false").lower() == "true"
        )

        # Ensure output directory exists
        self.profile_output_dir.mkdir(exist_ok=True)


class PerformanceProfiler:
    """Main profiler class with multiple profiling backends."""

    def __init__(self, config: ProfilerConfig | None = None):
        self.config = config or ProfilerConfig()
        self.active_profiles: dict[str, Any] = {}

    def is_py_spy_available(self) -> bool:
        """Check if py-spy is available in the system."""
        try:
            result = subprocess.run(
                ["py-spy", "--version"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def profile_with_py_spy(
        self,
        pid: int | None = None,
        duration: int | None = None,
        rate: int | None = None,
        output_format: str = "flamegraph",
    ) -> Path | None:
        """
        Profile application using py-spy.

        Args:
            pid: Process ID to profile (current process if None)
            duration: Profile duration in seconds
            rate: Sampling rate per second
            output_format: 'flamegraph', 'speedscope', or 'raw'

        Returns:
            Path to generated profile file
        """
        if not self.is_py_spy_available():
            console.print("❌ [bold red]py-spy is not available[/bold red]")
            return None

        pid = pid or os.getpid()
        duration = duration or self.config.py_spy_duration
        rate = rate or self.config.py_spy_rate

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if output_format == "flamegraph":
            output_file = self.config.profile_output_dir / f"flamegraph_{timestamp}.svg"
            cmd = [
                "py-spy",
                "record",
                "-o",
                str(output_file),
                "-d",
                str(duration),
                "-r",
                str(rate),
                "-p",
                str(pid),
            ]
        elif output_format == "speedscope":
            output_file = (
                self.config.profile_output_dir / f"speedscope_{timestamp}.json"
            )
            cmd = [
                "py-spy",
                "record",
                "-o",
                str(output_file),
                "-f",
                "speedscope",
                "-d",
                str(duration),
                "-r",
                str(rate),
                "-p",
                str(pid),
            ]
        else:  # raw
            output_file = self.config.profile_output_dir / f"profile_{timestamp}.txt"
            cmd = [
                "py-spy",
                "top",
                "-d",
                str(duration),
                "-r",
                str(rate),
                "-p",
                str(pid),
            ]

        try:
            console.print("🔬 [bold blue]Starting py-spy profiling...[/bold blue]")
            console.print(f"   PID: {pid}, Duration: {duration}s, Rate: {rate} Hz")
            console.print(f"   Output: {output_file}")

            if output_format == "raw":
                # For raw format, capture output directly
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=duration + 10
                )
                with open(output_file, "w") as f:
                    f.write(result.stdout)
            else:
                # For file outputs, let py-spy write directly
                result = subprocess.run(cmd, timeout=duration + 10)

            if result.returncode == 0:
                console.print(
                    f"✅ [bold green]Profile saved to {output_file}[/bold green]"
                )

                # Auto-open flame graph if configured
                if output_format == "flamegraph" and self.config.auto_open_flame_graph:
                    self._open_file(output_file)

                return output_file
            else:
                console.print(
                    f"❌ [bold red]py-spy failed with return code {result.returncode}[/bold red]"
                )
                return None

        except subprocess.TimeoutExpired:
            console.print("⚠️ [bold yellow]py-spy profiling timed out[/bold yellow]")
            return None
        except Exception as e:
            console.print(f"❌ [bold red]Error running py-spy: {e}[/bold red]")
            return None

    @contextlib.contextmanager
    def profile_with_cprofile(self, name: str = "profile"):
        """
        Context manager for cProfile profiling.

        Usage:
            with profiler.profile_with_cprofile("my_function"):
                # code to profile
                pass
        """
        profiler = cProfile.Profile()
        start_time = time.time()

        try:
            profiler.enable()
            yield profiler
        finally:
            profiler.disable()

            duration = time.time() - start_time
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save binary profile
            profile_file = (
                self.config.profile_output_dir / f"cprofile_{name}_{timestamp}.prof"
            )
            profiler.dump_stats(str(profile_file))

            # Generate text report
            text_file = (
                self.config.profile_output_dir / f"cprofile_{name}_{timestamp}.txt"
            )
            with open(text_file, "w") as f:
                stats = pstats.Stats(profiler, stream=f)
                stats.sort_stats("cumulative")
                stats.print_stats(50)  # Top 50 functions

            console.print(
                f"🔬 [bold green]cProfile completed in {duration:.2f}s[/bold green]"
            )
            console.print(f"   Binary: {profile_file}")
            console.print(f"   Report: {text_file}")

    def profile_memory_usage(self, duration: int = 30) -> Path | None:
        """
        Profile memory usage using py-spy.

        Args:
            duration: Monitoring duration in seconds

        Returns:
            Path to memory profile file
        """
        if not self.is_py_spy_available():
            console.print(
                "❌ [bold red]py-spy is not available for memory profiling[/bold red]"
            )
            return None

        pid = os.getpid()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.config.profile_output_dir / f"memory_{timestamp}.txt"

        cmd = [
            "py-spy",
            "top",
            "-p",
            str(pid),
            "-d",
            str(duration),
            "--rate",
            "10",  # Lower rate for memory profiling
            "--subprocesses",
        ]

        try:
            console.print(
                f"🧠 [bold blue]Starting memory profiling for {duration}s...[/bold blue]"
            )

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=duration + 10
            )

            if result.returncode == 0:
                with open(output_file, "w") as f:
                    f.write(f"Memory Profile - {datetime.now()}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(result.stdout)

                console.print(
                    f"✅ [bold green]Memory profile saved to {output_file}[/bold green]"
                )
                return output_file
            else:
                console.print("❌ [bold red]Memory profiling failed[/bold red]")
                return None

        except Exception as e:
            console.print(f"❌ [bold red]Error during memory profiling: {e}[/bold red]")
            return None

    def profile_async_function(self, func, *args, **kwargs):
        """
        Profile an async function with cProfile.

        Args:
            func: Async function to profile
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Function result and profile stats
        """

        async def _profile_wrapper():
            with self.profile_with_cprofile(func.__name__):
                return await func(*args, **kwargs)

        return asyncio.run(_profile_wrapper())

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report."""
        report_lines = [
            "# Performance Profiling Report",
            f"Generated: {datetime.now()}",
            "",
            "## Available Profiles",
        ]

        if self.config.profile_output_dir.exists():
            profiles = list(self.config.profile_output_dir.glob("*"))
            if profiles:
                for profile in sorted(
                    profiles, key=lambda p: p.stat().st_mtime, reverse=True
                ):
                    size = profile.stat().st_size
                    modified = datetime.fromtimestamp(profile.stat().st_mtime)
                    report_lines.append(
                        f"- {profile.name} ({size:,} bytes, {modified})"
                    )
            else:
                report_lines.append("- No profiles found")

        report_lines.extend(
            [
                "",
                "## Profiling Commands",
                "",
                "### Generate Flame Graph",
                "```bash",
                "uv run chatapp profile --type flamegraph --duration 30",
                "```",
                "",
                "### Profile Memory Usage",
                "```bash",
                "uv run chatapp profile --type memory --duration 60",
                "```",
                "",
                "### Profile Specific Endpoint",
                "```bash",
                "# In one terminal",
                "uv run dev",
                "",
                "# In another terminal",
                "uv run chatapp profile --type flamegraph --duration 10",
                "curl -X POST 'http://localhost:8000/api/threads/123e4567-e89b-12d3-a456-426614174000/messages?user_id=550e8400-e29b-41d4-a716-446655440000' \\",
                "  -H 'Content-Type: application/json' \\",
                '  -d \'{"content": "What is 25 * 18?", "message_type": "text"}\'',
                "```",
            ]
        )

        return "\n".join(report_lines)

    def _open_file(self, file_path: Path):
        """Open file with system default application."""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(file_path)])
            elif sys.platform == "linux":  # Linux
                subprocess.run(["xdg-open", str(file_path)])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["start", str(file_path)], shell=True)
        except Exception as e:
            console.print(f"⚠️ [bold yellow]Could not auto-open file: {e}[/bold yellow]")

    def list_profiles(self) -> Table:
        """List all available profile files."""
        table = Table(
            title="📊 Available Profiles", show_header=True, header_style="bold magenta"
        )
        table.add_column("File", style="cyan", no_wrap=True)
        table.add_column("Type", style="green")
        table.add_column("Size", justify="right", style="blue")
        table.add_column("Created", style="yellow")

        if not self.config.profile_output_dir.exists():
            table.add_row("No profiles directory", "", "", "")
            return table

        profiles = list(self.config.profile_output_dir.glob("*"))
        if not profiles:
            table.add_row("No profiles found", "", "", "")
            return table

        for profile in sorted(profiles, key=lambda p: p.stat().st_mtime, reverse=True):
            size = profile.stat().st_size
            modified = datetime.fromtimestamp(profile.stat().st_mtime)

            # Determine profile type from filename
            if "flamegraph" in profile.name:
                prof_type = "Flame Graph (SVG)"
            elif "speedscope" in profile.name:
                prof_type = "Speedscope (JSON)"
            elif "cprofile" in profile.name:
                if profile.suffix == ".prof":
                    prof_type = "cProfile (Binary)"
                else:
                    prof_type = "cProfile (Text)"
            elif "memory" in profile.name:
                prof_type = "Memory Usage"
            else:
                prof_type = "Unknown"

            # Format size
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"

            table.add_row(
                profile.name, prof_type, size_str, modified.strftime("%Y-%m-%d %H:%M")
            )

        return table

    def cleanup_old_profiles(self, days: int = 7) -> int:
        """
        Clean up profile files older than specified days.

        Args:
            days: Number of days to keep profiles

        Returns:
            Number of files deleted
        """
        if not self.config.profile_output_dir.exists():
            return 0

        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0

        for profile in self.config.profile_output_dir.glob("*"):
            if profile.stat().st_mtime < cutoff_time:
                try:
                    profile.unlink()
                    deleted_count += 1
                    console.print(f"🗑️ Deleted old profile: {profile.name}")
                except Exception as e:
                    console.print(f"⚠️ Could not delete {profile.name}: {e}")

        return deleted_count


# Global profiler instance
profiler = PerformanceProfiler()


# Decorator for easy function profiling
def profile_function(name: str | None = None):
    """
    Decorator to profile a function with cProfile.

    Usage:
        @profile_function("my_expensive_function")
        def expensive_function():
            # code to profile
            pass
    """

    def decorator(func):
        profile_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                with profiler.profile_with_cprofile(profile_name):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                with profiler.profile_with_cprofile(profile_name):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator
