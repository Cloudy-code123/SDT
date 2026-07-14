"""SDT - Subdomain Discovery Tool
Passive enumeration: query public data-sources for subdomains.
"""

import logging
import random
from typing import List

import requests
from colorama import Fore, Style

from stealth import StealthConfig, create_session

logger = logging.getLogger("sdt.passive")

# Per-source timeout in seconds
_TIMEOUT: int = 15


# ---------------------------------------------------------------------------
# crt.sh  (Certificate Transparency logs)
# ---------------------------------------------------------------------------

def _query_crtsh(domain: str, config: StealthConfig) -> List[str]:
    """Query crt.sh for subdomains found in CT logs."""
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    results: List[str] = []

    for attempt in range(config.max_retries):
        try:
            logger.info("Querying crt.sh for .%s (attempt %d)", domain, attempt + 1)
            config.throttle()
            session = create_session(config)
            timeout = config.random_timeout()
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()

            data = resp.json()
            for entry in data:
                name: str = entry.get("name_value", "")
                for line in name.split("\n"):
                    line = line.strip().lower()
                    if line.endswith(f".{domain}") or line == domain:
                        results.append(line)

            logger.info("crt.sh returned %d raw entries", len(results))
            return results

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("crt.sh attempt %d failed: %s", attempt + 1, exc)
            if config.backoff and attempt < config.max_retries - 1:
                delay = config.backoff_delay(attempt)
                logger.info("Backing off %.1fs before retry", delay)
                time_sleep(delay)
        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                logger.warning("crt.sh rate limited, backing off")
                if config.backoff:
                    delay = config.backoff_delay(attempt + 2)
                    time_sleep(delay)
                continue
            logger.warning("crt.sh HTTP error: %s", exc)
            return results
        except (ValueError, KeyError) as exc:
            logger.warning("crt.sh returned invalid JSON: %s", exc)
            return results

    return results


# ---------------------------------------------------------------------------
# hackertarget  (public DNS dataset)
# ---------------------------------------------------------------------------

def _query_hackertarget(domain: str, config: StealthConfig) -> List[str]:
    """Query the HackerTarget API for DNS records of a domain."""
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    results: List[str] = []

    for attempt in range(config.max_retries):
        try:
            logger.info("Querying hackertarget for %s (attempt %d)", domain, attempt + 1)
            config.throttle()
            session = create_session(config)
            timeout = config.random_timeout()
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()

            for line in resp.text.splitlines():
                host = line.split(",")[0].strip().lower()
                if host.endswith(f".{domain}") or host == domain:
                    results.append(host)

            logger.info("hackertarget returned %d raw entries", len(results))
            return results

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("hackertarget attempt %d failed: %s", attempt + 1, exc)
            if config.backoff and attempt < config.max_retries - 1:
                delay = config.backoff_delay(attempt)
                time_sleep(delay)
        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                logger.warning("hackertarget rate limited, backing off")
                if config.backoff:
                    delay = config.backoff_delay(attempt + 2)
                    time_sleep(delay)
                continue
            logger.warning("hackertarget HTTP error: %s", exc)
            return results

    return results


# ---------------------------------------------------------------------------
# CertSpotter  (Certificate Transparency via Google crt search fallback)
# ---------------------------------------------------------------------------

def _query_certspotter(domain: str, config: StealthConfig) -> List[str]:
    """Query CertSpotter's CT log API for subdomains."""
    url = f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
    results: List[str] = []

    for attempt in range(config.max_retries):
        try:
            logger.info("Querying CertSpotter for %s (attempt %d)", domain, attempt + 1)
            config.throttle()
            session = create_session(config)
            timeout = config.random_timeout()
            resp = session.get(url, timeout=timeout)
            resp.raise_for_status()

            data = resp.json()
            for entry in data:
                for name in entry.get("dns_names", []):
                    name = name.strip().lower()
                    if name.endswith(f".{domain}") or name == domain:
                        results.append(name)

            logger.info("CertSpotter returned %d raw entries", len(results))
            return results

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            logger.warning("CertSpotter attempt %d failed: %s", attempt + 1, exc)
            if config.backoff and attempt < config.max_retries - 1:
                delay = config.backoff_delay(attempt)
                time_sleep(delay)
        except requests.exceptions.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 429:
                logger.warning("CertSpotter rate limited, backing off")
                if config.backoff:
                    delay = config.backoff_delay(attempt + 2)
                    time_sleep(delay)
                continue
            logger.warning("CertSpotter HTTP error: %s", exc)
            return results
        except (ValueError, KeyError) as exc:
            logger.warning("CertSpotter returned invalid JSON: %s", exc)
            return results

    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def time_sleep(delay: float) -> None:
    """Wrapper for time.sleep to avoid importing time at module level collision."""
    import time
    time.sleep(delay)


# ---------------------------------------------------------------------------
# Public aggregator
# ---------------------------------------------------------------------------

def gather_passive(domain: str, config: StealthConfig | None = None) -> List[str]:
    """Run every passive source and return a deduplicated list of subdomains."""
    cfg = config or StealthConfig()

    print(
        Fore.CYAN
        + Style.BRIGHT
        + "[*] Running passive enumeration..."
        + Style.RESET_ALL
    )

    all_results: List[str] = []

    # Randomise source order to avoid predictable query patterns
    sources = [
        ("crt.sh", _query_crtsh),
        ("HackerTarget", _query_hackertarget),
        ("CertSpotter", _query_certspotter),
    ]
    random.shuffle(sources)

    for idx, (name, func) in enumerate(sources):
        try:
            found = func(domain, cfg)
            all_results.extend(found)
            print(
                Fore.WHITE
                + Style.DIM
                + f"    [{name}] => {len(found)} subdomains"
                + Style.RESET_ALL
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Source %s raised an unexpected error: %s", name, exc)

        # Random inter-source delay to avoid burst-like patterns
        if idx < len(sources) - 1:
            inter_delay = random.uniform(1.0, 4.0)
            logger.debug("Inter-source delay: %.1fs", inter_delay)
            time_sleep(inter_delay)

    # Deduplicate
    unique = sorted(set(all_results))
    print(
        Fore.GREEN
        + f"[+] Passive total (unique): {len(unique)}"
        + Style.RESET_ALL
    )
    return unique
