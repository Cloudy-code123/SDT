"""SDT - Subdomain Discovery Tool
Stealth module: UA rotation, throttling, jitter, proxy, DoH, fingerprint evasion.
"""

import logging
import random
import time
from typing import Any

import requests

logger = logging.getLogger("sdt.stealth")

# ---------------------------------------------------------------------------
# User-Agent rotation pool — real browser signatures (expanded)
# ---------------------------------------------------------------------------

_USER_AGENTS: list[str] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:126.0) Gecko/20100101 Firefox/126.0",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    # Safari on iPad
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

# ---------------------------------------------------------------------------
# Accept-Language variations by locale
# ---------------------------------------------------------------------------

_ACCEPT_LANGUAGES: list[str] = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.9,fr;q=0.8",
    "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,es;q=0.8",
    "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "en-US,en;q=0.9,it;q=0.8",
    "en-AU,en;q=0.9",
]

# ---------------------------------------------------------------------------
# Realistic Referer URLs (for common navigation patterns)
# ---------------------------------------------------------------------------

_REFERER_PATTERNS: list[str] = [
    "https://www.google.com/",
    "https://www.google.co.uk/",
    "https://www.bing.com/",
    "https://search.yahoo.com/",
    "https://duckduckgo.com/",
    "https://www.facebook.com/",
    "https://twitter.com/",
    "https://www.reddit.com/",
    "https://www.baidu.com/",
    "https://yandex.com/",
]

# ---------------------------------------------------------------------------
# DNS servers for rotation (public, reputable resolvers + DoH endpoints)
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
    "64.233.160.0",    # Google (alternate)
    "76.76.19.19",     # Alternate DNS
    "94.140.14.14",    # AdGuard DNS
    "94.140.15.15",    # AdGuard DNS
]

# ---------------------------------------------------------------------------
# DNS-over-HTTPS (DoH) endpoints
# ---------------------------------------------------------------------------

_DOH_ENDPOINTS: list[str] = [
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/dns-query",
    "https://dns.quad9.net/dns-query",
]

# ---------------------------------------------------------------------------
# Realistic screen resolution / viewport headers
# ---------------------------------------------------------------------------

_VIEWPORTS: list[tuple[str, str]] = [
    ("1920", "1080"),
    ("1366", "768"),
    ("1536", "864"),
    ("1440", "900"),
    ("1280", "720"),
    ("2560", "1440"),
    ("1600", "900"),
    ("1280", "1024"),
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
        use_doh: bool = False,
        timeout_randomize: bool = False,
        backoff: bool = False,
        max_retries: int = 3,
    ) -> None:
        if stealth:
            self.delay = max(delay, random.uniform(1.0, 3.0))
            self.jitter = max(jitter, random.uniform(0.5, 2.0))
        else:
            self.delay = delay
            self.jitter = jitter

        self.proxy = proxy
        self.rotate_dns = rotate_dns
        self.use_doh = use_doh
        self.timeout_randomize = timeout_randomize
        self.backoff = backoff
        self.max_retries = max_retries
        self._dns_index = 0

        # Per-session state
        self._session_cookies: dict[str, str] = {}
        self._referer: str = random.choice(_REFERER_PATTERNS)
        self._viewport_w, self._viewport_h = random.choice(_VIEWPORTS)
        self._request_count: int = 0

    def random_ua(self) -> str:
        """Return a random User-Agent string."""
        return random.choice(_USER_AGENTS)

    def random_headers(self) -> dict[str, str]:
        """Return a realistic set of HTTP headers with fingerprint diversity."""
        ua = self.random_ua()
        is_firefox = "Firefox" in ua
        is_safari = "Safari" in ua and "Chrome" not in ua
        is_edge = "Edg/" in ua

        # Rotate referer periodically to simulate natural browsing
        if self._request_count > 0 and self._request_count % random.randint(5, 15) == 0:
            self._referer = random.choice(_REFERER_PATTERNS)

        headers: dict[str, str] = {
            "User-Agent": ua,
            "Accept": random.choice([
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            ]),
            "Accept-Language": random.choice(_ACCEPT_LANGUAGES),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": random.choice(["1", "1", "0"]),
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none" if self._request_count < 3 else "cross-origin",
            "Cache-Control": random.choice([
                "max-age=0", "no-cache", "max-age=300",
                "no-cache, no-store, must-revalidate",
            ]),
            "Referer": self._referer,
        }

        # Browser-specific headers to match fingerprint
        if is_firefox:
            headers["Sec-Fetch-User"] = "?1"
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        elif is_safari:
            # Safari doesn't send Sec-Fetch-User
            headers.pop("Sec-Fetch-User", None)
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        elif is_edge:
            headers["Sec-Fetch-User"] = "?1"
            headers["sec-ch-ua"] = random.choice([
                '"Chromium";v="126", "Microsoft Edge";v="126", "Not.A/Brand";v="99"',
                '"Chromium";v="125", "Microsoft Edge";v="125", "Not.A/Brand";v="24"',
            ])
            headers["sec-ch-ua-mobile"] = "?0"
            headers["sec-ch-ua-platform"] = '"Windows"'
        else:
            # Chrome
            headers["Sec-Fetch-User"] = "?1"
            headers["sec-ch-ua"] = random.choice([
                '"Chromium";v="126", "Not(A:Brand";v="24", "Google Chrome";v="126"',
                '"Chromium";v="125", "Not.A/Brand";v="24", "Google Chrome";v="125"',
                '"Chromium";v="124", "Not.A/Brand";v="99", "Google Chrome";v="124"',
            ])
            headers["sec-ch-ua-mobile"] = "?0"
            headers["sec-ch-ua-platform"] = random.choice(['"Windows"', '"macOS"', '"Linux"'])

        self._request_count += 1
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

    def random_doh_endpoint(self) -> str:
        """Return a random DNS-over-HTTPS endpoint."""
        return random.choice(_DOH_ENDPOINTS)

    def throttle(self) -> None:
        """Sleep for the configured delay + random jitter."""
        total = self.delay + random.uniform(0, self.jitter)
        if total > 0:
            logger.debug("Throttle: sleeping %.2fs", total)
            time.sleep(total)

    def throttled_sleep(self, base: float | None = None) -> None:
        """Sleep with optional override base and natural variation."""
        b = base if base is not None else self.delay
        # Add occasional longer pauses to simulate human distraction
        extra_pause = random.uniform(0, 8) if random.random() < 0.05 else 0
        total = b + random.uniform(0, self.jitter) + extra_pause
        if total > 0:
            logger.debug("Throttled sleep: %.2fs (extra=%.2fs)", total, extra_pause)
            time.sleep(total)

    def backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retries."""
        base = min(2 ** attempt, 30)
        return base + random.uniform(0, min(attempt, 5))

    def random_timeout(self) -> float:
        """Return a randomized request timeout to avoid timing fingerprinting."""
        if self.timeout_randomize:
            return random.uniform(8, 20)
        return 15.0


def create_session(config: StealthConfig | None = None) -> requests.Session:
    """Create a requests.Session with stealth headers, cookies, and optional proxy."""
    session = requests.Session()
    cfg = config or StealthConfig()

    session.headers.update(cfg.random_headers())

    # Set realistic connection pool settings
    adapter = requests.adapters.HTTPAdapter(
        pool_connections=5,
        pool_maxsize=5,
        max_retries=0,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    if cfg.proxy:
        session.proxies = {
            "http": cfg.proxy,
            "https": cfg.proxy,
        }
        logger.info("Proxy configured: %s", cfg.proxy)

    return session


def create_doh_session(config: StealthConfig | None = None) -> requests.Session:
    """Create a requests.Session optimized for DNS-over-HTTPS queries."""
    session = requests.Session()
    cfg = config or StealthConfig()

    ua = cfg.random_ua()
    session.headers.update({
        "User-Agent": ua,
        "Accept": "application/dns-json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })

    if cfg.proxy:
        session.proxies = {
            "http": cfg.proxy,
            "https": cfg.proxy,
        }

    return session


def doh_resolve(
    hostname: str,
    config: StealthConfig,
    session: requests.Session | None = None,
) -> str | None:
    """Resolve a hostname via DNS-over-HTTPS (Google JSON API).

    Returns the IP address or None if unresolved.
    """
    import json as _json

    sess = session or create_doh_session(config)
    endpoint = config.random_doh_endpoint()

    try:
        if "dns.google" in endpoint:
            url = f"https://dns.google/resolve?name={hostname}&type=A"
        elif "cloudflare-dns" in endpoint:
            url = f"https://cloudflare-dns.com/dns-query?name={hostname}&type=A"
            sess.headers["accept"] = "application/dns-json"
        elif "quad9" in endpoint:
            url = f"https://dns.quad9.net/dns-query?name={hostname}&type=A"
            sess.headers["accept"] = "application/dns-json"
        else:
            url = f"https://dns.google/resolve?name={hostname}&type=A"

        timeout = config.random_timeout()
        resp = sess.get(url, timeout=timeout)
        resp.raise_for_status()

        data = resp.json()
        answers = data.get("Answer", [])
        for answer in answers:
            if answer.get("type") == 1:  # A record
                return answer.get("data")

    except Exception as exc:
        logger.debug("DoH resolution failed for %s: %s", hostname, exc)

    return None
