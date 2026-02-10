"""
DevHub - Internal Developer Knowledge Assistant
===============================================

VERSION: V0 (no observability - students will add it)

This is the main entry point for DevHub. The application helps developers
find information about APIs, service owners, and system status.

INTENTIONAL PROBLEMS (for workshop debugging):
- Random latency spikes in VectorDB (10%)
- Connection failures in VectorDB (5%)
- Stale data in TeamDB (10%)
- Low similarity results in VectorDB (15%)
- Status API timeouts (2%)

Students will:
1. Session 1: Add OpenTelemetry tracing to find these problems
2. Session 2: Add DeepEval testing to catch regressions
"""

import sys
from pathlib import Path

# Load .env file before importing Config (which reads env vars at import time)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from config import Config
from agent import DevHubAgent


# Rich console for formatted output
console = Console()


WELCOME_BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   ██████╗ ███████╗██╗   ██╗██╗  ██╗██╗   ██╗██████╗         ║
║   ██╔══██╗██╔════╝██║   ██║██║  ██║██║   ██║██╔══██╗        ║
║   ██║  ██║█████╗  ██║   ██║███████║██║   ██║██████╔╝        ║
║   ██║  ██║██╔══╝  ╚██╗ ██╔╝██╔══██║██║   ██║██╔══██╗        ║
║   ██████╔╝███████╗ ╚████╔╝ ██║  ██║╚██████╔╝██████╔╝        ║
║   ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝         ║
║                                                              ║
║   Internal Developer Knowledge Assistant - V0                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def print_welcome():
    """Print welcome banner and instructions."""
    console.print(WELCOME_BANNER, style="bold blue")
    console.print("Ask me about APIs, documentation, service owners, or system status.", style="dim")
    console.print("Type [bold]quit[/bold], [bold]exit[/bold], or [bold]q[/bold] to exit.\n", style="dim")


def print_response(result: dict):
    """
    Print agent response with formatting.

    Args:
        result: Response from DevHubAgent.query()
    """
    # Show tools used (debug info)
    if result.get("tools_called"):
        tools_text = ", ".join(result["tools_called"])
        console.print(f"[dim]Tools used: {tools_text}[/dim]")

    # Check for any errors in tool results
    for tool_result in result.get("tool_results", []):
        if tool_result.get("error"):
            console.print(f"[yellow]Warning: {tool_result['tool']} - {tool_result['error']}[/yellow]")

    # Print main response with Markdown formatting
    response_text = result.get("response", "No response generated.")
    md = Markdown(response_text)
    console.print(Panel(md, title="DevHub", border_style="green"))


def run_repl(agent: DevHubAgent):
    """
    Run interactive REPL mode.

    Args:
        agent: Initialized DevHubAgent instance
    """
    print_welcome()

    while True:
        try:
            # Get user input
            console.print("[bold cyan]You:[/bold cyan] ", end="")
            user_input = input().strip()

            # Check for exit commands
            if user_input.lower() in ("quit", "exit", "q", ""):
                if user_input == "":
                    continue
                console.print("[dim]Goodbye![/dim]")
                break

            # Process query
            console.print("[dim]Thinking...[/dim]")
            result = agent.query(user_input)

            # Print response
            print_response(result)
            console.print()  # Blank line for readability

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Goodbye![/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def run_single_query(agent: DevHubAgent, query: str):
    """
    Run a single query and exit.

    Args:
        agent: Initialized DevHubAgent instance
        query: The user's question
    """
    try:
        result = agent.query(query)
        print_response(result)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for DevHub CLI."""
    # Validate configuration
    issues = Config.validate()
    if issues:
        console.print("[red]Configuration Issues:[/red]")
        for issue in issues:
            console.print(f"[red]  - {issue}[/red]")
        sys.exit(1)

    # Initialize agent
    try:
        agent = DevHubAgent()
    except ValueError as e:
        console.print(f"[red]Initialization Error: {e}[/red]")
        sys.exit(1)

    # Check for single query mode (command line argument)
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        run_single_query(agent, query)
    else:
        # Interactive REPL mode
        run_repl(agent)


if __name__ == "__main__":
    main()
