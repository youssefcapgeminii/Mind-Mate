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
    return f"{color}{BOLD}[{node}]{RESET}"

def log_node_start(node: str):
    width = 58
    bar = "─" * width
    label = f"  NODE: {node.upper()}"
    print(f"\n{BOLD}{CYAN}┌{bar}┐", flush=True)
    print(f"│{label:<{width}}│", flush=True)
    print(f"└{bar}┘{RESET}", flush=True)

def log_input(node: str, label: str, value: str):
    print(f"{_tag(node, YELLOW)}  INPUT    {BOLD}{label}:{RESET} {DIM}{value}{RESET}", flush=True)

def log_llm(node: str, label: str, value: str):
    print(f"{_tag(node, MAGENTA)}  LLM      {BOLD}{label}:{RESET} {value}", flush=True)

def log_ok(node: str, label: str, value: str):
    print(f"{_tag(node, GREEN)}  ✓        {BOLD}{label}:{RESET} {GREEN}{value}{RESET}", flush=True)

def log_warn(node: str, label: str, value: str):
    print(f"{_tag(node, RED)}  ✗        {BOLD}{label}:{RESET} {RED}{value}{RESET}", flush=True)

def log_info(node: str, label: str, value: str):
    print(f"{_tag(node, CYAN)}  INFO     {BOLD}{label}:{RESET} {value}", flush=True)

def log_route(node: str, destination: str):
    print(f"{_tag(node, BLUE)}  ROUTE    → {BOLD}{CYAN}{destination}{RESET}", flush=True)
