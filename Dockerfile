# Multi-stage Dockerfile for Interoperability Messaging Lab
# Stage 1: Build environment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY schema/ ./schema/

# Install build dependencies and build package
RUN pip install --no-cache-dir build wheel setuptools
RUN python -m build --wheel --outdir dist/

# Stage 2: Runtime environment
FROM python:3.11-slim as runtime

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash interop && \
    mkdir -p /home/interop/data && \
    chown -R interop:interop /home/interop

# Set working directory
WORKDIR /home/interop

# Copy built package from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install the package
RUN pip install --no-cache-dir /tmp/*.whl

# Switch to non-root user
USER interop

# Set environment variables
ENV PYTHONPATH=/home/interop
ENV PYTHONUNBUFFERED=1

# Create data directories
RUN mkdir -p data/samples data/pcaps

# Expose default ZeroMQ port
EXPOSE 5555

# Default command
CMD ["interop-cli", "--help"]

# Labels
LABEL maintainer="Kraig Roberts <kraig.roberts@example.com>"
LABEL description="Interoperability Messaging Lab - Tactical message parsing and streaming"
LABEL version="0.1.0"
LABEL org.opencontainers.image.source="https://github.com/kraigroberts/interoperability-messaging-lab"
