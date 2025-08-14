# Interoperability Messaging Lab

[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)

Parsers + tooling for **VMF**, **CoT**, and **STANAG**-style messages.  
Includes binary ↔ structured transforms, schema normalization, and CLI workflows for rapid testing.

---

## Features
- **VMF** sample generator (`tools/make_vmf_sample.py`)
- **PCAP** sample generator (`tools/make_pcap_sample.py`)
- **CoT** XML parser and schema normalization
- Binary ↔ JSON ↔ XML transformations
- CI/CD with automated VMF + PCAP tests
- Works cross-platform (Linux, macOS, Windows via WSL)

---

## Quickstart

```bash
# Clone and enter
git clone https://github.com/<OWNER>/<REPO>.git
cd interoperability-messaging-lab

# Create venv and install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run CLI help
python src/cli.py --help
