#!/usr/bin/env python3
"""SDT - Subdomain Discovery Tool
CLI entry-point: argument parsing, setup and launch.
"""

import argparse
import logging
import sys

# Force UTF-8 output on Windows so Unicode box-drawing chars render correctly.
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from colorama import init as colorama_init

from banner import show_banner, show_disclaimer
from scanner import Scanner
from utils import is_valid_domain, print_error, safe_exit

# ---------------------------------------------------------------------------
# Colour initialisation (must happen before any colorama output)
# ---------------------------------------------------------------------------
colorama_init(autoreset=True)

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("sdt")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="sdt",
        description="SDT - Subdomain Discovery Tool  v1.0",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-d",
        "--domain",
        type=str,
        required=True,
        help="Target domain to enumerate (e.g. example.com)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Save valid subdomains to a TXT file (one per line)",
    )

    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        default=False,
        help="Save results to a JSON file (<domain>_results.json)",
    )

    parser.add_argument(
        "--threads",
        type=int,
        default=20,
        help="Number of concurrent DNS resolver threads (default: 20)",
    )

    parser.add_argument(
        "--wordlist",
        type=str,
        default=None,
        help="Path to a custom wordlist for active brute-force",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging",
    )

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry-point for the SDT CLI."""
    show_banner()
    show_disclaimer()

    parser = build_parser()
    args = parser.parse_args()

    # Verbose mode
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")

    # Validate domain
    domain: str = args.domain.strip().lower()
    if not is_valid_domain(domain):
        safe_exit(f"Invalid domain format: {domain}")

    # Validate threads
    if args.threads < 1 or args.threads > 200:
        safe_exit("Thread count must be between 1 and 200.")

    # Launch scanner
    try:
        scanner = Scanner(
            domain=domain,
            threads=args.threads,
            output=args.output,
            json_output=args.json_output,
            wordlist=args.wordlist,
        )
        scanner.run()

    except KeyboardInterrupt:
        print()
        print_error("Scan interrupted by user (Ctrl+C).")
        sys.exit(130)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error")
        safe_exit(f"Fatal error: {exc}")


if __name__ == "__main__":
    main()
