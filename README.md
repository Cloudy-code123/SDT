# SDT - Subdomain Discovery Tool

A fast, modular Python 3 CLI tool that discovers subdomains for domains you own or are authorized to test.

## Features

- **Passive enumeration** via crt.sh, CertSpotter, and HackerTarget
- **Active brute-force** with a built-in or custom wordlist
- **Multi-threaded DNS resolution** with configurable thread count
- **Colored terminal output** using Colorama / Rich
- **Export** to TXT and JSON
- **Progress indicator** and **execution timer**
- **Statistics summary** after each scan

## Installation

cd sdt
pip install -r requirements.txt
```

## Usage Examples

```bash
# Basic scan
python sdt.py -d example.com

# Save results to a text file
python sdt.py -d example.com -o results.txt

# Export to JSON
python sdt.py -d example.com --json

# Use 50 threads for faster DNS resolution
python sdt.py -d example.com --threads 50

# Use a custom wordlist
python sdt.py -d example.com --wordlist wordlist.txt

# Show help
python sdt.py -h

# Verbose / debug output
python sdt.py -d example.com -v
```

## Example Output

```
  ███████╗██████╗ ████████╗
  ██╔════╝██╔══██╗╚══██╔══╝
  ███████╗██║  ██║   ██║
  ╚════██║██║  ██║   ██║
  ███████║██████╔╝   ██║
  ╚══════╝╚═════╝    ╚═╝

    Subdomain Discovery Tool
           Version 1.0

[!] DISCLAIMER:
    This tool is intended only for discovering subdomains of domains that you own
    or are explicitly authorized to assess...

----------------------------------------
Target  : example.com
Started : 12:30:11
----------------------------------------

[*] Running passive enumeration...
    [crt.sh] => 12 subdomains
    [HackerTarget] => 8 subdomains
    [CertSpotter] => 5 subdomains
[+] Passive total (unique): 18
[*] Generated 168 active candidates
[*] Resolving 172 hostnames with 20 threads...
    Progress: 17/172 (10%)
    ...
[+] api.example.com  [VALID]
[+] mail.example.com  [VALID]
[-] ftp.example.com  [NO DNS]
...

Statistics:
  Total Found   : 15
  Valid DNS     : 12
  No DNS        : 3
  Time          : 4.2 seconds

Finished.
```

## Project Structure

```
sdt/
├── sdt.py            # CLI entry-point
├── banner.py         # ASCII logo & disclaimer
├── scanner.py        # Orchestrator
├── passive.py        # Passive sources (crt.sh, etc.)
├── active.py         # Active brute-force wordlist logic
├── dnsresolver.py    # Multi-threaded DNS resolution
├── utils.py          # Helpers, validation, output
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Dependencies

| Library      | Purpose                    |
|-------------|----------------------------|
| requests    | HTTP client for APIs       |
| dnspython   | DNS resolution             |
| rich        | Rich terminal formatting   |
| colorama    | Cross-platform colours     |
| tqdm        | Progress bars              |

## Legal Disclaimer

This tool is intended **only** for discovering subdomains of domains that you own or are explicitly authorized to assess. The user is responsible for complying with all applicable laws and obtaining permission before use. Unauthorized scanning of third-party domains is illegal and unethical.

## License

MIT License
