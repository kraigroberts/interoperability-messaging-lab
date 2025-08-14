# Interoperability Messaging Lab

[![CI](https://github.com/kraigroberts/interoperability-messaging-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/kraigroberts/interoperability-messaging-lab/actions/workflows/ci.yml)

Parsers + tooling for **VMF**, **CoT**, and **STANAG**-style messages.  
Includes binary ↔ structured transforms, schema normalization, and CLI workflows for rapid testing.

---

## Features
- **CoT** XML parser and schema normalization
- **VMF** demo binary parser + generator (`tools/make_vmf_sample.py`)
- **PCAP** payload extraction + generator (`tools/make_pcap_sample.py`)
- Binary → Normalized JSON transforms
- CI with unit tests (VMF + PCAP)

---

## Quickstart

```bash
# Clone and enter
git clone https://github.com/kraigroberts/interoperability-messaging-lab.git
cd interoperability-messaging-lab

# Create venv and install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# CLI help
python src/cli.py --help
