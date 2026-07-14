"""SDT - Subdomain Discovery Tool
Passive enumeration: query public data-sources for subdomains.
"""

import logging
from typing import List

import requests
from colorama import Fore, Style

logger = logging.getLogger("sdt.passive")

# Per-source timeout in seconds
_TIMEOUT: int = 15


# ---------------------------------------------------------------------------
# crt.sh  (Certificate Transparency logs)
# ---------------------------------------------------------------------------

def _query_crtsh(domain: str) -> List[str]:
    """Query crt.sh for subdomains found in CT logs.

    Returns a deduplicated list of hostnames.
    """
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    results: List[str] = []

    try:
        logger.info("Querying crt.sh for .%s", domain)
        resp = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "SDT/1.0"})
        resp.raise_for_status()

        data = resp.json()
        for entry in data:
            name: str = entry.get("name_value", "")
            # A single entry can contain multiple names separated by newlines
            for line in name.split("\n"):
                line = line.strip().lower()
                if line.endswith(f".{domain}") or line == domain:
                    results.append(line)

        logger.info("crt.sh returned %d raw entries", len(results))

    except requests.exceptions.Timeout:
        logger.warning("crt.sh timed out after %ds", _TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("crt.sh connection error: %s", exc)
    except requests.exceptions.HTTPError as exc:
        logger.warning("crt.sh HTTP error: %s", exc)
    except (ValueError, KeyError) as exc:
        logger.warning("crt.sh returned invalid JSON: %s", exc)

    return results


# ---------------------------------------------------------------------------
# hackertarget  (public DNS dataset)
# ---------------------------------------------------------------------------

def _query_hackertarget(domain: str) -> List[str]:
    """Query the HackerTarget API for DNS records of a domain."""
    url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
    results: List[str] = []

    try:
        logger.info("Querying hackertarget for %s", domain)
        resp = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "SDT/1.0"})
        resp.raise_for_status()

        for line in resp.text.splitlines():
            host = line.split(",")[0].strip().lower()
            if host.endswith(f".{domain}") or host == domain:
                results.append(host)

        logger.info("hackertarget returned %d raw entries", len(results))

    except requests.exceptions.Timeout:
        logger.warning("hackertarget timed out after %ds", _TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("hackertarget connection error: %s", exc)
    except requests.exceptions.HTTPError as exc:
        logger.warning("hackertarget HTTP error: %s", exc)

    return results


# ---------------------------------------------------------------------------
# Aliased VT-lite  (Certificate Transparency via Google crt search fallback)
# ---------------------------------------------------------------------------

def _query_certspotter(domain: str) -> List[str]:
    """Query CertSpotter's CT log API for subdomains."""
    url = f"https://api.certspotter.com/v1/issuances?domain={domain}&include_subdomains=true&expand=dns_names"
    results: List[str] = []

    try:
        logger.info("Querying CertSpotter for %s", domain)
        resp = requests.get(url, timeout=_TIMEOUT, headers={"User-Agent": "SDT/1.0"})
        resp.raise_for_status()

        data = resp.json()
        for entry in data:
            for name in entry.get("dns_names", []):
                name = name.strip().lower()
                if name.endswith(f".{domain}") or name == domain:
                    results.append(name)

        logger.info("CertSpotter returned %d raw entries", len(results))

    except requests.exceptions.Timeout:
        logger.warning("CertSpotter timed out after %ds", _TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        logger.warning("CertSpotter connection error: %s", exc)
    except requests.exceptions.HTTPError as exc:
        logger.warning("CertSpotter HTTP error: %s", exc)
    except (ValueError, KeyError) as exc:
        logger.warning("CertSpotter returned invalid JSON: %s", exc)

    return results


# ---------------------------------------------------------------------------
# Public aggregator
# ---------------------------------------------------------------------------

def gather_passive(domain: str) -> List[str]:
    """Run every passive source and return a deduplicated list of subdomains."""
    print(
        Fore.CYAN
        + Style.BRIGHT
        + "[*] Running passive enumeration..."
        + Style.RESET_ALL
    )

    all_results: List[str] = []

    sources = [
        ("crt.sh", _query_crtsh),
        ("HackerTarget", _query_hackertarget),
        ("CertSpotter", _query_certspotter),
    ]

    for name, func in sources:
        try:
            found = func(domain)
            all_results.extend(found)
            print(
                Fore.WHITE
                + Style.DIM
                + f"    [{name}] => {len(found)} subdomains"
                + Style.RESET_ALL
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Source %s raised an unexpected error: %s", name, exc)

    # Deduplicate
    unique = sorted(set(all_results))
    print(
        Fore.GREEN
        + f"[+] Passive total (unique): {len(unique)}"
        + Style.RESET_ALL
    )
    return unique
