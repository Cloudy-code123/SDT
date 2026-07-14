"""SDT - Subdomain Discovery Tool
Banner module: displays the ASCII logo and tool metadata.
"""

from colorama import Fore, Style

# ASCII art logo for SDT
LOGO: str = r"""
  ███████╗██████╗ ████████╗
  ██╔════╝██╔══██╗╚══██╔══╝
  ███████╗██║  ██║   ██║
  ╚════██║██║  ██║   ██║
  ███████║██████╔╝   ██║
  ╚══════╝╚═════╝    ╚═╝

    Subdomain Discovery Tool
           Version 1.0
"""

DISCLAIMER: str = (
    "This tool is intended only for discovering subdomains of domains that you own "
    "or are explicitly authorized to assess. The user is responsible for complying "
    "with all applicable laws and obtaining permission before use."
)


def show_banner() -> None:
    """Print the colored ASCII banner to the terminal."""
    print(Fore.CYAN + Style.BRIGHT + LOGO + Style.RESET_ALL)


def show_disclaimer() -> None:
    """Print the legal disclaimer to the terminal."""
    print(Fore.YELLOW + Style.BRIGHT + "[!] DISCLAIMER:" + Style.RESET_ALL)
    print(Fore.YELLOW + f"    {DISCLAIMER}" + Style.RESET_ALL)
    print()
