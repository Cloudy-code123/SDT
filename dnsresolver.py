"""SDT - Subdomain Discovery Tool
DNS resolver: multi-threaded resolution of hostnames.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Tuple

import dns.resolver
from colorama import Fore, Style

logger = logging.getLogger("sdt.dnsresolver")

# Default DNS server to fall back to
_DEFAULT_DNS: str = "8.8.8.8"

# Timeout per single DNS query (seconds)
_DNS_TIMEOUT: int = 3


def _resolve_single(hostname: str, dns_server: str | None) -> Tuple[str, bool, str | None]:
    """Resolve a single hostname.

    Returns ``(hostname, is_valid, ip_address_or_None)``.
    """
    try:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = _DNS_TIMEOUT
        resolver.timeout = _DNS_TIMEOUT

        if dns_server:
            resolver.nameservers = [dns_server]

        answer = resolver.resolve(hostname, "A")
        ip = answer[0].address
        return (hostname, True, ip)

    except dns.resolver.NXDOMAIN:
        return (hostname, False, None)
    except dns.resolver.NoAnswer:
        return (hostname, False, None)
    except dns.resolver.NoNameservers:
        return (hostname, False, None)
    except dns.exception.Timeout:
        return (hostname, False, None)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unexpected DNS error for %s: %s", hostname, exc)
        return (hostname, False, None)


def resolve_all(
    hostnames: List[str],
    threads: int = 20,
    dns_server: str | None = None,
) -> Tuple[List[str], List[str]]:
    """Resolve *hostnames* using *threads* worker threads.

    Returns ``(valid_list, invalid_list)`` where each element is a hostname.
    """
    valid: List[str] = []
    invalid: List[str] = []

    total = len(hostnames)
    if total == 0:
        return valid, invalid

    print(
        Fore.CYAN
        + Style.BRIGHT
        + f"[*] Resolving {total} hostnames with {threads} threads..."
        + Style.RESET_ALL
    )

    completed = 0

    with ThreadPoolExecutor(max_workers=threads) as pool:
        future_to_host = {
            pool.submit(_resolve_single, host, dns_server): host
            for host in hostnames
        }

        for future in as_completed(future_to_host):
            hostname, is_valid, ip = future.result()
            completed += 1

            if is_valid:
                valid.append(hostname)
                logger.debug("VALID   %s => %s", hostname, ip)
            else:
                invalid.append(hostname)
                logger.debug("INVALID %s", hostname)

            # Progress indicator every 10 %
            step = max(1, total // 10)
            if completed % step == 0 or completed == total:
                pct = completed * 100 // total
                print(
                    Fore.WHITE
                    + Style.DIM
                    + f"    Progress: {completed}/{total} ({pct}%)"
                    + Style.RESET_ALL
                )

    return valid, invalid
