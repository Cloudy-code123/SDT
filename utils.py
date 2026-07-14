"""SDT - Subdomain Discovery Tool
Utility helpers: domain validation, output formatting, file I/O.
"""

import json
import re
import sys
from typing import List

from colorama import Fore, Style


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------

# RFC-1123 compliant hostname pattern (simplified)
_DOMAIN_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,}$"
)


def is_valid_domain(domain: str) -> bool:
    """Return True if *domain* looks like a valid hostname."""
    return bool(_DOMAIN_RE.match(domain))


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_info(message: str) -> None:
    """Print an informational line."""
    print(Fore.WHITE + Style.DIM + f"[*] {message}" + Style.RESET_ALL)


def print_success(message: str) -> None:
    """Print a success line."""
    print(Fore.GREEN + f"[+] {message}" + Style.RESET_ALL)


def print_warning(message: str) -> None:
    """Print a warning line."""
    print(Fore.YELLOW + f"[!] {message}" + Style.RESET_ALL)


def print_error(message: str) -> None:
    """Print an error line."""
    print(Fore.RED + Style.BRIGHT + f"[-] {message}" + Style.RESET_ALL)


def print_valid(subdomain: str) -> None:
    """Print a subdomain that resolved successfully."""
    print(
        Fore.GREEN + f"[+] {subdomain}" + Style.RESET_ALL
        + "  "
        + Fore.GREEN + Style.BRIGHT + "[VALID]" + Style.RESET_ALL
    )


def print_no_dns(subdomain: str) -> None:
    """Print a subdomain that could not be resolved."""
    print(
        Fore.RED + f"[-] {subdomain}" + Style.RESET_ALL
        + "  "
        + Fore.RED + Style.BRIGHT + "[NO DNS]" + Style.RESET_ALL
    )


def print_separator() -> None:
    """Print a visual separator line."""
    print(Fore.WHITE + Style.DIM + "-" * 40 + Style.RESET_ALL)


# ---------------------------------------------------------------------------
# File output
# ---------------------------------------------------------------------------

def save_txt(filename: str, subdomains: List[str]) -> None:
    """Write discovered subdomains to a plain-text file (one per line)."""
    with open(filename, "w", encoding="utf-8") as fh:
        for sub in sorted(subdomains):
            fh.write(f"{sub}\n")
    print_success(f"Results saved to {filename}")


def save_json(filename: str, domain: str, subdomains: List[str]) -> None:
    """Write discovered subdomains to a JSON file."""
    data = {
        "domain": domain,
        "count": len(subdomains),
        "subdomains": sorted(subdomains),
    }
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=4, ensure_ascii=False)
    print_success(f"Results saved to {filename}")


def safe_exit(message: str | None = None, code: int = 1) -> None:
    """Print an optional message and exit with *code*."""
    if message:
        print_error(message)
    sys.exit(code)
