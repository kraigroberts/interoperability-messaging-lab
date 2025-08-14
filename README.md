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

# Option 1: Install in development mode
python3 -m pip install -e .

# Option 2: Traditional setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run CLI help
interop-cli --help
# or
python src/cli.py --help

# Check system status
interop-cli status

# Start interactive shell
interop-cli interactive
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

# Check system status
python src/cli.py status

# Start interactive shell
python src/cli.py interactive

# Start REST API server
python src/cli.py api --port 8000
```

## REST API

The lab now includes a comprehensive REST API for integration with other systems:

### API Server
```bash
# Start API server
python src/cli.py api --host 0.0.0.0 --port 8000

# With auto-reload for development
python src/cli.py api --reload
```

### API Endpoints
- **`GET /`**: API information and documentation links
- **`GET /health`**: Health check with dependency status
- **`POST /api/v1/parse`**: Parse and normalize tactical messages
- **`POST /api/v1/stream`**: Stream messages via ZeroMQ
- **`POST /api/v1/pcap`**: Process PCAP files and extract payloads
- **`GET /api/v1/stats`**: Message processing statistics
- **`GET /docs`**: Interactive API documentation (Swagger UI)
- **`GET /redoc`**: Alternative API documentation

### API Features
- **FastAPI Framework**: Modern, fast web framework with automatic OpenAPI generation
- **Request Validation**: Pydantic models with automatic validation and serialization
- **Background Processing**: Asynchronous message streaming with background tasks
- **Request Tracking**: Unique request IDs and timing information
- **Multiple Formats**: Support for JSON, NDJSON, and CSV output
- **Health Monitoring**: Comprehensive health checks and dependency status

### Example API Usage
```bash
# Parse a CoT message via API
curl -X POST "http://localhost:8000/api/v1/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "cot",
    "content": "PGV2ZW50IHZlcnNpb249IjIuMCIgdWlkPSJULTEyMyI+PC9ldmVudD4=",
    "output_format": "json"
  }'

# Check API health
curl "http://localhost:8000/health"

# View API documentation
open "http://localhost:8000/docs"
```

## Enhanced CLI Features

The CLI provides a modern, user-friendly interface with comprehensive features:

### Visual Feedback & Progress
- **Progress Indicators**: Real-time feedback for all operations
- **Color-coded Output**: Success (✅), warning (⚠️), and error (❌) indicators
- **Rich Formatting**: Beautiful output with Rich library integration
- **Detailed Status**: File sizes, message counts, and operation summaries

### Interactive Exploration
- **Interactive Shell**: Explore samples and schema interactively
- **Status Monitoring**: Check dependencies and system health
- **Sample Browsing**: List and examine available sample files
- **Schema Inspection**: View schema structure and requirements

### Comprehensive Help
- **Detailed Help Text**: Extensive descriptions for all commands and options
- **Usage Examples**: Practical examples for common use cases
- **Command Discovery**: Easy navigation through subcommands
- **Version Information**: Built-in version checking and display

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

## Streaming Demo
The lab includes real-time message streaming via ZeroMQ:

```bash
# Terminal 1: Start subscriber
python3 -m src.cli stream sub

# Terminal 2: Publish messages
python3 -m src.cli stream pub --in data/samples/sample_cot.xml --format cot
python3 -m src.cli stream pub --in data/samples/sample_vmf.bin --format vmf

# Continuous streaming mode
python3 -m src.cli stream pub --in data/samples/*.xml --format cot --stream --delay 2.0
```

**Features:**
- **PUB/SUB Pattern**: Publisher broadcasts, multiple subscribers receive
- **Message Validation**: All messages validated against schema before publishing
- **Continuous Streaming**: Loop through files with configurable delays
- **Real-time Display**: Subscriber shows formatted message details
- **Configurable Topics**: Subscribe to specific message types

## Packaging & Deployment

### Python Package
The lab is packaged as a Python package with a CLI entry point:

```bash
# Install in development mode
pip install -e .

# Use the CLI command
interop-cli --help
interop-cli parse cot --in file.xml --out output.json
interop-cli stream pub --in file.xml --format cot
```

### Docker
Containerized deployment with multi-stage build:

```bash
# Build the image
docker build -t interop-lab .

# Run the CLI
docker run --rm interop-lab interop-cli --help

# Run streaming demo
docker-compose up -d
```

**Docker Features:**
- **Multi-stage build**: Optimized runtime image
- **Non-root user**: Security best practices
- **Volume mounting**: Easy data access
- **Network isolation**: ZeroMQ communication between containers

## Quality Gates

The project uses automated quality checks to maintain code standards:

### Code Quality Tools
- **Ruff**: Fast Python linter with auto-fixing capabilities
- **MyPy**: Static type checker for Python
- **Pytest**: Testing framework with comprehensive coverage

### Running Quality Checks
```bash
# Run all quality checks
python3 scripts/quality_check.py

# Individual checks
ruff check src/ tests/ cli.py          # Linting
mypy src/ --ignore-missing-imports    # Type checking
pytest tests/ -q                       # Unit tests
python3 -m build                      # Package build
```

### Quality Standards
- **Linting**: Ruff enforces PEP 8, import sorting, and best practices
- **Type Safety**: MyPy ensures type annotations are correct
- **Test Coverage**: All functionality must have passing tests
- **Build Success**: Package must build successfully for distribution

## Contributing
1. Fork the repo
2. Create a feature branch:
```bash
git checkout -b feature/my-change
```
3. Run quality checks:
```bash
python3 scripts/quality_check.py
```
4. Commit changes:
```bash
git commit -am "Add new feature"
```
5. Push branch and open a PR

## License
MIT License – see [LICENSE](LICENSE) for details.
