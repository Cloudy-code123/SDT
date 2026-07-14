"""SDT - Subdomain Discovery Tool
Stealth module: User-Agent rotation, request throttling, jitter, proxy support.
"""

import logging
import random
import time
from typing import Any

import requests

logger = logging.getLogger("sdt.stealth")

# ---------------------------------------------------------------------------
# User-Agent rotation pool — real browser signatures
# ---------------------------------------------------------------------------

_USER_AGENTS: list[str] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# ---------------------------------------------------------------------------
# DNS servers for rotation (public, reputable resolvers)
# ---------------------------------------------------------------------------

_DNS_SERVERS: list[str] = [
    "8.8.8.8",        # Google
    "8.8.4.4",        # Google
    "1.1.1.1",        # Cloudflare
    "1.0.0.1",        # Cloudflare
    "9.9.9.9",        # Quad9
    "149.112.112.112", # Quad9
    "208.67.222.222",  # OpenDNS
    "208.67.220.220",  # OpenDNS
]


class StealthConfig:
    """Centralised stealth configuration."""

    def __init__(
        self,
        delay: float = 0.0,
        jitter: float = 0.0,
        stealth: bool = False,
        proxy: str | None = None,
        rotate_dns: bool = False,
    ) -> None:
        # If stealth mode is enabled, apply sensible defaults
        if stealth:
            self.delay = max(delay, random.uniform(1.0, 3.0))
            self.jitter = max(jitter, random.uniform(0.5, 2.0))
        else:
            self.delay = delay
            self.jitter = jitter

        self.proxy = proxy
        self.rotate_dns = rotate_dns
        self._dns_index = 0

    def random_ua(self) -> str:
        """Return a random User-Agent string."""
        return random.choice(_USER_AGENTS)

    def random_headers(self) -> dict[str, str]:
        """Return a realistic set of HTTP headers."""
        ua = self.random_ua()
        headers: dict[str, str] = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en;q=0.9,en-US;q=0.8",
                "en-US,en;q=0.9,fr;q=0.8",
                "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": random.choice(["max-age=0", "no-cache"]),
        }
        return headers

    def next_dns_server(self) -> str:
        """Return the next DNS server in rotation."""
        if not self.rotate_dns:
            return _DNS_SERVERS[0]
        server = _DNS_SERVERS[self._dns_index % len(_DNS_SERVERS)]
        self._dns_index += 1
        return server

    def random_dns_server(self) -> str:
        """Return a random DNS server."""
        return random.choice(_DNS_SERVERS)

    def throttle(self) -> None:
        """Sleep for the configured delay + random jitter."""
        total = self.delay + random.uniform(0, self.jitter)
        if total > 0:
            logger.debug("Throttle: sleeping %.2fs", total)
            time.sleep(total)


def create_session(config: StealthConfig | None = None) -> requests.Session:
    """Create a requests.Session with stealth headers and optional proxy."""
    session = requests.Session()
    cfg = config or StealthConfig()

    session.headers.update(cfg.random_headers())

    if cfg.proxy:
        session.proxies = {
            "http": cfg.proxy,
            "https": cfg.proxy,
        }
        logger.info("Proxy configured: %s", cfg.proxy)

    return session
