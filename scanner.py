"""SDT - Subdomain Discovery Tool
Scanner orchestrator: coordinates passive, active, DNS resolution, and output.
"""

import logging
import time
from typing import List

from colorama import Fore, Style

from active import generate_candidates
from dnsresolver import resolve_all
from passive import gather_passive
from stealth import StealthConfig
from utils import (
    print_info,
    print_no_dns,
    print_separator,
    print_success,
    print_valid,
    save_json,
    save_txt,
)

logger = logging.getLogger("sdt.scanner")


class Scanner:
    """Main scanner that ties together passive, active and DNS resolution."""

    def __init__(
        self,
        domain: str,
        threads: int = 20,
        output: str | None = None,
        json_output: bool = False,
        wordlist: str | None = None,
        config: StealthConfig | None = None,
    ) -> None:
        self.domain: str = domain
        self.threads: int = threads
        self.output: str | None = output
        self.json_output: bool = json_output
        self.wordlist: str | None = wordlist
        self.config: StealthConfig = config or StealthConfig()

        self.found: List[str] = []
        self.valid_dns: List[str] = []
        self.invalid_dns: List[str] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Execute the full discovery pipeline."""
        start_time = time.time()

        # Header
        print_separator()
        print_success(f"Target  : {self.domain}")
        local_time = time.strftime("%H:%M:%S", time.localtime())
        print_success(f"Started : {local_time}")
        if self.config.delay > 0 or self.config.jitter > 0:
            print_success(f"Stealth : delay={self.config.delay:.1f}s  jitter={self.config.jitter:.1f}s")
        if self.config.proxy:
            print_success(f"Proxy   : {self.config.proxy}")
        if self.config.rotate_dns:
            print_success("DNS rot.: enabled")
        print_separator()
        print()

        # 1. Passive enumeration
        passive_results = gather_passive(self.domain, self.config)

        # 2. Active brute-force candidates
        active_candidates = generate_candidates(self.domain, self.wordlist)

        # 3. Merge and deduplicate
        all_candidates = sorted(set(passive_results + active_candidates))
        print_info(f"Total unique candidates: {len(all_candidates)}")

        # 4. DNS resolution
        self.valid_dns, self.invalid_dns = resolve_all(
            all_candidates, threads=self.threads, config=self.config
        )

        self.found = sorted(set(self.valid_dns))

        # 5. Display results
        print()
        print_separator()
        for host in self.found:
            print_valid(host)
        for host in self.invalid_dns:
            print_no_dns(host)
        print_separator()
        print()

        # 6. Save results if requested
        if self.output:
            save_txt(self.output, self.found)

        if self.json_output:
            json_file = f"{self.domain}_results.json"
            save_json(json_file, self.domain, self.found)

        # 7. Statistics
        elapsed = time.time() - start_time
        self._print_stats(elapsed)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _print_stats(self, elapsed: float) -> None:
        """Print the final statistics summary."""
        print()
        print(Fore.CYAN + Style.BRIGHT + "Statistics:" + Style.RESET_ALL)
        print(Fore.WHITE + f"  Total Found   : {len(self.found)}" + Style.RESET_ALL)
        print(
            Fore.WHITE
            + f"  Valid DNS     : {len(self.valid_dns)}"
            + Style.RESET_ALL
        )
        print(
            Fore.WHITE
            + f"  No DNS        : {len(self.invalid_dns)}"
            + Style.RESET_ALL
        )
        print(
            Fore.GREEN
            + Style.BRIGHT
            + f"  Time          : {elapsed:.1f} seconds"
            + Style.RESET_ALL
        )
        print()
        print(Fore.GREEN + "Finished." + Style.RESET_ALL)
