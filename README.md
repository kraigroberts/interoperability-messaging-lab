# Interoperability Messaging Lab

[![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml)

Parsers + tooling for **VMF**, **CoT**, and **STANAG**-style messages. Includes binary ↔ structured transforms, schema normalization, and CLI workflows for rapid testing.

## Features
- **VMF** sample generator (`tools/make_vmf_sample.py`)
- **PCAP** sample generator (`tools/make_pcap_sample.py`)
- **CoT** XML parser and schema normalization
- Binary ↔ JSON ↔ XML transformations
- CI/CD with automated VMF + PCAP tests
- Works cross-platform (Linux, macOS, Windows via WSL)

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
```

## Generate Samples
```bash
# Generate VMF sample
python tools/make_vmf_sample.py

# Generate PCAP sample
python tools/make_pcap_sample.py
```
These commands will place output files in `data/samples/`.

## Usage
```bash
# Parse a VMF binary file and convert to JSON
python src/cli.py parse vmf --in data/samples/sample_vmf.bin --out output.json

# Parse a CoT XML file and normalize to the shared schema
python src/cli.py parse cot --in data/samples/sample_cot.xml --out output.json

# Export to different formats (JSON, NDJSON, CSV)
python src/cli.py parse cot --in data/samples/sample_cot.xml --out output.ndjson --out-format ndjson
python src/cli.py parse vmf --in data/samples/sample_vmf.bin --out output.csv --out-format csv

# Decode PCAP and extract payloads
python src/cli.py pcap decode --pcap data/pcaps/example_capture.pcap.txt --out output_dir
```

## Schema
The lab uses a normalized message schema (`schema/normalized_message.schema.json`) that provides a consistent format across different tactical message types:

- **CoT (XML)**: Events with position, time, and metadata
- **VMF (Binary)**: Binary messages with coordinates and timestamps
- **Validation**: All normalized messages are validated against the JSON Schema

The schema enforces required fields, data types, and rejects additional properties for data integrity.

## Export Formats
The CLI supports multiple export formats for normalized messages:

- **JSON**: Standard JSON with pretty-printing (default)
- **NDJSON**: Newline-delimited JSON for streaming and processing
- **CSV**: Flattened CSV format for spreadsheet analysis

All exports maintain data integrity while providing format flexibility for different use cases.

## Contributing
1. Fork the repo
2. Create a feature branch:
```bash
git checkout -b feature/my-change
```
3. Commit changes:
```bash
git commit -am "Add new feature"
```
4. Push branch and open a PR

## License
MIT License – see [LICENSE](LICENSE) for details.
