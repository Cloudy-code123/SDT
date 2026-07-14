"""SDT - Subdomain Discovery Tool
Active enumeration: brute-force subdomain guessing via wordlist.
"""

import logging
import os
from typing import List

from colorama import Fore, Style

logger = logging.getLogger("sdt.active")

# Small built-in wordlist used when the user does not supply an external one.
_DEFAULT_WORDLIST: List[str] = [
    "www", "mail", "ftp", "smtp", "pop", "ns1", "ns2", "ns3", "dns", "dns1",
    "dns2", "mx", "mx1", "mx2", "webmail", "email", "remote", "vpn", "ssh",
    "sftp", "git", "gitlab", "github", "bitbucket", "ci", "cd", "dev",
    "development", "staging", "stage", "test", "testing", "qa", "uat",
    "demo", "sandbox", "beta", "alpha", "api", "api2", "api3", "rest",
    "graphql", "app", "app1", "app2", "apps", "portal", "dashboard",
    "panel", "admin", "admin2", "cpanel", "whm", "manage", "mgmt",
    "console", "secure", "ssl", "login", "auth", "sso", "accounts",
    "shop", "store", "ecommerce", "billing", "payment", "pay", "invoice",
    "cdn", "static", "assets", "media", "images", "img", "download",
    "downloads", "files", "upload", "uploads", "cloud", "aws", "gcp",
    "azure", "s3", "storage", "db", "database", "sql", "mysql", "postgres",
    "mongo", "redis", "elastic", "elasticsearch", "kibana", "grafana",
    "monitor", "monitoring", "logs", "log", "syslog", "ntp", "time",
    "ldap", "ad", "dc", "kdc", "proxy", "gateway", "gw", "edge",
    "loadbalancer", "lb", "haproxy", "nginx", "apache", "iis", "tomcat",
    "node", "nodejs", "python", "php", "java", "go", "rust", "ruby",
    "mobile", "ios", "android", "m", "wap", "legacy", "old", "new",
    "backup", "bak", "old", "archive", "temp", "tmp", "internal", "intranet",
    "extranet", "lan", "wan", "office", "hq", "data", "data1", "analytics",
    "bi", "report", "reports", "wiki", "docs", "documentation", "help",
    "support", "ticket", "helpdesk", "crm", "erp", "hr", "recruit",
    "mail2", "webdisk", "cpanel", "webhost", "autoconfig", "autodiscover",
    "localhost", "status", "health", "uptime", "heartbeat", "ping",
    "ns", "mx3", "mx4", "imap", "pop3", "inbound", "outbound",
]

logger = logging.getLogger("sdt.active")


def _load_wordlist(path: str | None) -> List[str]:
    """Load a wordlist from *path*, falling back to the built-in list."""
    if path and os.path.isfile(path):
        logger.info("Loading external wordlist from %s", path)
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            words = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
        if words:
            return words
        logger.warning("Wordlist file was empty – falling back to built-in list")

    logger.info("Using built-in wordlist (%d entries)", len(_DEFAULT_WORDLIST))
    return _DEFAULT_WORDLIST


def generate_candidates(domain: str, wordlist_path: str | None = None) -> List[str]:
    """Return a list of ``<word>.<domain>`` candidates to resolve."""
    words = _load_wordlist(wordlist_path)
    candidates = [f"{word}.{domain}" for word in words]

    print(
        Fore.CYAN
        + Style.BRIGHT
        + f"[*] Generated {len(candidates)} active candidates"
        + Style.RESET_ALL
    )
    return candidates
