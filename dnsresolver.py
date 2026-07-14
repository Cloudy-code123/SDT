"""SDT - Subdomain Discovery Tool
DNS resolver: multi-threaded resolution with jitter, server rotation, and DoH support.
"""

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple

import dns.resolver
import dns.exception
from colorama import Fore, Style

from stealth import StealthConfig, doh_resolve, create_doh_session

logger = logging.getLogger("sdt.dnsresolver")

# Timeout per single DNS query (seconds)
_DNS_TIMEOUT: int = 3

# DNS record types to randomly query for behavioral camouflage
_DNS_TYPES = ["A", "A", "A", "AAAA", "MX", "TXT", "CNAME"]


def _resolve_single(
    hostname: str,
    config: StealthConfig,
) -> Tuple[str, bool, str | None]:
    """Resolve a single hostname with jitter and server rotation.

    Returns ``(hostname, is_valid, ip_address_or_None)``.
    """
    # Jitter between DNS queries to avoid burst detection
    if config.jitter > 0 or config.delay > 0:
        jitter_time = random.uniform(0, config.jitter + config.delay)
        if jitter_time > 0:
            time.sleep(jitter_time)

    # DoH mode: resolve via HTTPS
    if config.use_doh:
        ip = doh_resolve(hostname, config)
        if ip:
            return (hostname, True, ip)
        return (hostname, False, None)

    try:
        resolver = dns.resolver.Resolver()
        resolver.lifetime = _DNS_TIMEOUT
        resolver.timeout = _DNS_TIMEOUT

        # Rotate DNS servers to avoid single-resolver fingerprinting
        if config.rotate_dns:
            server = config.next_dns_server()
        else:
            server = config.random_dns_server()
        resolver.nameservers = [server]

        # Occasionally query for other record types to appear more like a
        # real browser doing background DNS lookups (not just A-record scanning)
        query_type = random.choice(_DNS_TYPES) if random.random() < 0.15 else "A"
        answer = resolver.resolve(hostname, query_type)

        # For A records, extract IP directly
        if query_type == "A":
            ip = answer[0].address
            return (hostname, True, ip)

        # For other record types, just confirm the hostname exists
        return (hostname, True, None)

    except dns.resolver.NXDOMAIN:
        return (hostname, False, None)
    except dns.resolver.NoAnswer:
        return (hostname, False, None)
    except dns.resolver.NoNameservers:
        # Rate limiting detected — add extra delay
        if config.backoff:
            extra = config.backoff_delay(1)
            logger.debug("NoNameservers for %s, backing off %.1fs", hostname, extra)
            time.sleep(extra)
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

    mode_label = "DoH" if cfg.use_doh else "DNS"
    print(
        Fore.CYAN
        + Style.BRIGHT
        + f"[*] Resolving {total} hostnames with {threads} threads ({mode_label})..."
        + Style.RESET_ALL
    )

    completed = 0

    # For DoH, create a shared session to reuse connections
    doh_session = create_doh_session(cfg) if cfg.use_doh else None

    # In stealth mode, reduce concurrency to avoid burst patterns
    effective_threads = threads
    if (cfg.delay > 0 or cfg.jitter > 0) and threads > 5:
        effective_threads = max(5, threads // 2)
        if effective_threads != threads:
            logger.info("Stealth mode: reduced threads from %d to %d", threads, effective_threads)

    with ThreadPoolExecutor(max_workers=effective_threads) as pool:
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

    # Clean up DoH session
    if doh_session:
        doh_session.close()

    return valid, invalid
