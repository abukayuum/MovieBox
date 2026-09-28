CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BANNER_TEXT = r"""
  MOVIE DEKHO BD
"""


def get_banner() -> str:
    """Returns formatted ASCII banner as a raw string with ANSI styling."""
    lines = [
        f"{BOLD}{CYAN}{BANNER_TEXT.strip()}{RESET}",
        f"{DIM}------------------------------------------------------------{RESET}",
        f"  Stream Movies, Series, Download",
        f"{DIM}------------------------------------------------------------{RESET}",
    ]
    return "\n".join(lines)
