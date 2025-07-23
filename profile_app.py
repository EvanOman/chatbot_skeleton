#!/usr/bin/env python3
"""
Performance profiling script for Sample Chat App.

This script provides various profiling options to analyze application performance
and identify bottlenecks during development.

Usage:
    python profile_app.py --help
    python profile_app.py --type flamegraph --duration 30
    python profile_app.py --type memory --duration 60
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="🔬 Profile Sample Chat App Performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --type flamegraph --duration 30    # Generate flame graph for 30 seconds
  %(prog)s --type speedscope --duration 10    # Generate speedscope profile
  %(prog)s --type memory --duration 60        # Profile memory usage for 60 seconds
  %(prog)s --attach 1234 --type flamegraph    # Profile existing process with PID 1234
        """
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["flamegraph", "speedscope", "memory", "top"],
        default="flamegraph",
        help="Profile type to generate (default: flamegraph)"
    )
    
    parser.add_argument(
        "--duration", "-d",
        type=int,
        default=30,
        help="Profiling duration in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--rate", "-r",
        type=int,
        default=100,
        help="Sampling rate per second (default: 100)"
    )
    
    parser.add_argument(
        "--attach", "-p",
        type=int,
        help="Attach to existing process PID instead of starting new app"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./profiles",
        help="Output directory for profile files (default: ./profiles)"
    )
    
    parser.add_argument(
        "--start-app",
        action="store_true",
        help="Start the application before profiling"
    )
    
    parser.add_argument(
        "--endpoint-test",
        action="store_true",
        help="Run endpoint tests during profiling"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Check if py-spy is available
    if not check_py_spy():
        console.print("❌ [bold red]py-spy is not available[/bold red]")
        console.print("Install with: pip install py-spy")
        sys.exit(1)
    
    console.print(Panel.fit("🔬 Sample Chat App Profiler", style="bold blue"))
    
    app_process = None
    target_pid = args.attach
    
    try:
        # Start application if requested
        if args.start_app and not args.attach:
            console.print("🚀 [bold green]Starting application...[/bold green]")
            app_process = start_application()
            target_pid = app_process.pid
            
            # Wait for app to start
            console.print("⏳ Waiting for application to start...")
            time.sleep(3)
        
        if not target_pid:
            # Try to find running application
            target_pid = find_running_app()
            if not target_pid:
                console.print("❌ [bold red]No running application found[/bold red]")
                console.print("Use --start-app to start the application or --attach PID to attach to existing process")
                sys.exit(1)
        
        console.print(f"🎯 [bold blue]Profiling PID: {target_pid}[/bold blue]")
        
        # Start endpoint tests if requested
        test_process = None
        if args.endpoint_test:
            console.print("🧪 [bold yellow]Starting endpoint tests...[/bold yellow]")
            test_process = start_endpoint_tests()
        
        # Run profiling
        profile_file = run_profiling(
            profile_type=args.type,
            pid=target_pid,
            duration=args.duration,
            rate=args.rate,
            output_dir=output_dir
        )
        
        if profile_file:
            console.print(f"✅ [bold green]Profile saved: {profile_file}[/bold green]")
            
            # Show usage instructions
            show_usage_instructions(args.type, profile_file)
        else:
            console.print("❌ [bold red]Profiling failed[/bold red]")
            sys.exit(1)
    
    finally:
        # Cleanup
        if app_process:
            console.print("🛑 [bold yellow]Stopping application...[/bold yellow]")
            app_process.terminate()
            try:
                app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                app_process.kill()


def check_py_spy() -> bool:
    """Check if py-spy is available."""
    try:
        result = subprocess.run(
            ["py-spy", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def start_application() -> subprocess.Popen:
    """Start the Sample Chat App."""
    try:
        # Try to start with uv
        process = subprocess.Popen(
            ["uv", "run", "python", "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process
    except FileNotFoundError:
        # Fallback to direct python
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return process


def find_running_app() -> int | None:
    """Find PID of running Sample Chat App."""
    try:
        # Look for python processes running main.py
        result = subprocess.run(
            ["pgrep", "-f", "main.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            return int(pids[0])  # Return first match
        
        return None
    except (subprocess.SubprocessError, ValueError):
        return None


def start_endpoint_tests() -> subprocess.Popen:
    """Start endpoint tests to generate load during profiling."""
    test_script = """
import requests
import time
import json
from uuid import uuid4

base_url = "http://localhost:8000"
user_id = "123e4567-e89b-12d3-a456-426614174000" 
thread_id = "123e4567-e89b-12d3-a456-426614174000"

test_messages = [
    "Hello! How can you help me?",
    "What is 25 * 18?",
    "What's the weather like in San Francisco?",
    "Search for the latest AI news",
    "Explain how machine learning works"
]

print("Starting endpoint tests...")
for i in range(10):  # Run for about 30 seconds
    for message in test_messages:
        try:
            response = requests.post(
                f"{base_url}/api/threads/{thread_id}/messages",
                params={"user_id": user_id},
                json={"content": message, "message_type": "text"},
                timeout=10
            )
            print(f"Test {i+1}: {response.status_code} - {message[:30]}...")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)
"""
    
    process = subprocess.Popen(
        [sys.executable, "-c", test_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process


def run_profiling(profile_type: str, pid: int, duration: int, rate: int, output_dir: Path) -> Path | None:
    """Run the actual profiling with py-spy."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    if profile_type == "flamegraph":
        output_file = output_dir / f"flamegraph_{timestamp}.svg"
        cmd = [
            "py-spy", "record",
            "-o", str(output_file),
            "-d", str(duration),
            "-r", str(rate),
            "-p", str(pid)
        ]
    
    elif profile_type == "speedscope":
        output_file = output_dir / f"speedscope_{timestamp}.json"
        cmd = [
            "py-spy", "record",
            "-o", str(output_file),
            "-f", "speedscope", 
            "-d", str(duration),
            "-r", str(rate),
            "-p", str(pid)
        ]
    
    elif profile_type == "memory":
        output_file = output_dir / f"memory_{timestamp}.txt"
        cmd = [
            "py-spy", "top",
            "-p", str(pid),
            "-d", str(duration),
            "--rate", "10"
        ]
    
    elif profile_type == "top":
        output_file = output_dir / f"top_{timestamp}.txt"
        cmd = [
            "py-spy", "top",
            "-p", str(pid),
            "-d", str(duration),
            "-r", str(rate)
        ]
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Profiling with py-spy ({profile_type})...", total=None)
            
            if profile_type in ["memory", "top"]:
                # Capture output for text-based profiles
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
                if result.returncode == 0:
                    with open(output_file, 'w') as f:
                        f.write(f"Profile Type: {profile_type}\n")
                        f.write(f"PID: {pid}\n")
                        f.write(f"Duration: {duration}s\n")
                        f.write(f"Rate: {rate} Hz\n")
                        f.write(f"Timestamp: {timestamp}\n")
                        f.write("=" * 50 + "\n\n")
                        f.write(result.stdout)
                    return output_file
            else:
                # File output for flamegraph/speedscope
                result = subprocess.run(cmd, timeout=duration + 10)
                if result.returncode == 0 and output_file.exists():
                    return output_file
        
        return None
        
    except subprocess.TimeoutExpired:
        console.print(f"⚠️ [bold yellow]Profiling timed out after {duration + 10} seconds[/bold yellow]")
        return None
    except Exception as e:
        console.print(f"❌ [bold red]Profiling error: {e}[/bold red]")
        return None


def show_usage_instructions(profile_type: str, profile_file: Path):
    """Show instructions for viewing the generated profile."""
    console.print("\n" + "="*60)
    console.print("📋 [bold blue]How to View Your Profile:[/bold blue]")
    
    if profile_type == "flamegraph":
        console.print(f"""
🔥 [bold green]Flame Graph (SVG)[/bold green]
   • Open in browser: {profile_file}
   • Interactive: Click on functions to zoom
   • Width = time spent, Height = call stack depth
   • Red = hot code paths
        """)
        
    elif profile_type == "speedscope":
        console.print(f"""
📈 [bold green]Speedscope Profile (JSON)[/bold green]
   • Go to: https://speedscope.app
   • Upload: {profile_file}
   • Multiple views: Time Order, Left Heavy, Sandwich
   • Great for call tree analysis
        """)
        
    elif profile_type in ["memory", "top"]:
        console.print(f"""
📊 [bold green]Text Profile[/bold green]
   • View with: cat {profile_file}
   • Or: less {profile_file}
   • Shows function call frequencies and times
        """)
    
    console.print("="*60)


if __name__ == "__main__":
    main()