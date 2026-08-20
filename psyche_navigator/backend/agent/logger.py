"""
Terminal Logging Utilities for the PsycheNavigator Agent.

Provides colored, structured log output for each node in the agent graph.
Uses ANSI escape codes to change text color and style in the terminal
(e.g. '\\033[92m' turns text green, '\\033[0m' resets back to normal).
"""

RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
CYAN    = "\033[96m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
RED     = "\033[91m"
BLUE    = "\033[94m"
MAGENTA = "\033[95m"
ORANGE  = "\033[33m"


def _tag(node: str, color: str) -> str:
    """
    Create a colored tag like [GUARD] or [RETRIEVER] for log lines.
    """
    return f"{color}{BOLD}[{node}]{RESET}"


def log_node_start(node: str):
    """
    Print a visible box in the terminal when a node starts running.

    Example output:
        ┌──────────────────────┐
        │  NODE: GUARD         │
        └──────────────────────┘
    """
    width = 58
    bar = "─" * width
    label = f"  NODE: {node.upper()}"
    print(f"\n{BOLD}{CYAN}┌{bar}┐", flush=True)
    print(f"│{label:<{width}}│", flush=True)
    print(f"└{bar}┘{RESET}", flush=True)


def log_input(node: str, label: str, value: str):
    """Log what data a node received, displayed in yellow."""
    print(f"{_tag(node, YELLOW)}  INPUT    {BOLD}{label}:{RESET} {DIM}{value}{RESET}", flush=True)


def log_llm(node: str, label: str, value: str):
    """Log what the LLM returned, displayed in magenta."""
    print(f"{_tag(node, MAGENTA)}  LLM      {BOLD}{label}:{RESET} {value}", flush=True)


def log_ok(node: str, label: str, value: str):
    """Log a success result with a checkmark, displayed in green."""
    print(f"{_tag(node, GREEN)}  ✓        {BOLD}{label}:{RESET} {GREEN}{value}{RESET}", flush=True)


def log_warn(node: str, label: str, value: str):
    """Log a failure or problem with an X mark, displayed in red."""
    print(f"{_tag(node, RED)}  ✗        {BOLD}{label}:{RESET} {RED}{value}{RESET}", flush=True)


def log_info(node: str, label: str, value: str):
    """Log general information, displayed in cyan."""
    print(f"{_tag(node, CYAN)}  INFO     {BOLD}{label}:{RESET} {value}", flush=True)


def log_route(node: str, destination: str):
    """Log which node the graph will route to next, displayed in blue."""
    print(f"{_tag(node, BLUE)}  ROUTE    → {BOLD}{CYAN}{destination}{RESET}", flush=True)
