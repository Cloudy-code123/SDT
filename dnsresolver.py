"""SDT - Subdomain Discovery Tool
DNS resolver: multi-threaded resolution of hostnames with jitter and server rotation.
"""

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import dns.resolver
from colorama import Fore, Style

from stealth import StealthConfig

logger = logging.getLogger("sdt.dnsresolver")

# Timeout per single DNS query (seconds)
_DNS_TIMEOUT: int = 3


def _resolve_single(
    hostname: str,
    config: StealthConfig,
) -> Tuple[str, bool, str | None]:
    """Resolve a single hostname with jitter and server rotation.

    Returns ``(hostname, is_valid, ip_address_or_None)``.
    """
    # Random jitter between DNS queries to avoid burst detection
    if config.jitter > 0 or config.delay > 0:
        jitter_time = random.uniform(0, config.jitter + config.delay)
        if jitter_time > 0:
            time.sleep(jitter_time)

    try:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = _DNS_TIMEOUT
        resolver.timeout = _DNS_TIMEOUT

        # Rotate DNS servers to avoid single-resolver fingerprinting
        server = config.next_dns_server() if config.rotate_dns else config.random_dns_server()
        resolver.nameservers = [server]

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
    config: StealthConfig | None = None,
) -> Tuple[List[str], List[str]]:
    """Resolve *hostnames* using *threads* worker threads.

    Returns ``(valid_list, invalid_list)`` where each element is a hostname.
    """
    valid: List[str] = []
    invalid: List[str] = []

    total = len(hostnames)
    if total == 0:
        return valid, invalid

    cfg = config or StealthConfig()

    print(
        Fore.CYAN
        + Style.BRIGHT
        + f"[*] Resolving {total} hostnames with {threads} threads..."
        + Style.RESET_ALL
    )

    completed = 0

    with ThreadPoolExecutor(max_workers=threads) as pool:
        future_to_host = {
            pool.submit(_resolve_single, host, cfg): host
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
