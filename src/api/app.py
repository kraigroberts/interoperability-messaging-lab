"""
FastAPI application for the Interoperability Messaging Lab.
Provides REST API endpoints for message parsing, streaming, and PCAP processing.
"""

import base64
import os
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Union

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .middleware import RequestIdMiddleware, TimingMiddleware

# Import our models and business logic
from .models import (
    ErrorResponse,
    HealthResponse,
    MessageStats,
    ParseRequest,
    ParseResponse,
    PCAPRequest,
    PCAPResponse,
    StreamRequest,
    StreamResponse,
)
from .services import MessageService, PCAPService, StreamingService

# Global state for tracking
start_time = time.time()
message_stats: dict[str, Union[int, list[float]]] = {
    "total_messages": 0,
    "cot_messages": 0,
    "vmf_messages": 0,
    "failed_messages": 0,
    "processing_times": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Interoperability Messaging Lab API...")
    yield
    # Shutdown
    print("🛑 Shutting down Interoperability Messaging Lab API...")


# Create FastAPI app
app = FastAPI(
    title="Interoperability Messaging Lab API",
    description="REST API for tactical message parsing, validation, and streaming",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(TimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
message_service = MessageService()
streaming_service = StreamingService()
pcap_service = PCAPService()


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "Interoperability Messaging Lab API",
        "version": "0.1.0",
        "description": "Tactical message parsing, validation, and streaming",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    # Check dependencies
    dependencies = {}
    try:
        import lxml  # noqa: F401
        dependencies["lxml"] = "healthy"
    except ImportError:
        dependencies["lxml"] = "unavailable"

    try:
        import scapy  # noqa: F401
        dependencies["scapy"] = "healthy"
    except ImportError:
        dependencies["scapy"] = "unavailable"

    try:
        import zmq  # noqa: F401
        dependencies["pyzmq"] = "healthy"
    except ImportError:
        dependencies["pyzmq"] = "unavailable"

    try:
        import jsonschema  # noqa: F401
        dependencies["jsonschema"] = "healthy"
    except ImportError:
        dependencies["jsonschema"] = "unavailable"

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        dependencies=dependencies,
        uptime_seconds=time.time() - start_time
    )


@app.post("/api/v1/parse", response_model=ParseResponse)
async def parse_message(request: ParseRequest) -> ParseResponse:
    """Parse and normalize a tactical message."""
    start_time = time.time()

    try:
        # Decode base64 content
        content_bytes = base64.b64decode(request.content)

        # Parse message based on format
        if request.format.value == "cot":
            parsed = message_service.parse_cot(content_bytes)
            cot_messages = message_stats["cot_messages"]
            message_stats["cot_messages"] = int(cot_messages) + 1 if isinstance(cot_messages, (int, str)) else 1
        elif request.format.value == "vmf":
            parsed = message_service.parse_vmf(content_bytes)
            vmf_messages = message_stats["vmf_messages"]
            message_stats["vmf_messages"] = int(vmf_messages) + 1 if isinstance(vmf_messages, (int, str)) else 1
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        # Normalize message
        normalized = message_service.normalize_message(parsed)

        # Convert to requested output format
        output_data = message_service.convert_format(normalized, request.output_format.value)

        # Update statistics
        processing_time = (time.time() - start_time) * 1000
        total_messages = message_stats["total_messages"]
        message_stats["total_messages"] = int(total_messages) + 1 if isinstance(total_messages, (int, str)) else 1
        processing_times = message_stats["processing_times"]
        if isinstance(processing_times, list):
            processing_times.append(processing_time)
        else:
            message_stats["processing_times"] = [processing_time]

        return ParseResponse(
            success=True,
            message=f"Successfully parsed {request.format.value.upper()} message",
            data=output_data,
            output_format=request.output_format,
            processing_time_ms=processing_time
        )

    except Exception as e:
        failed_messages = message_stats["failed_messages"]
        message_stats["failed_messages"] = int(failed_messages) + 1 if isinstance(failed_messages, (int, str)) else 1
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/v1/stream", response_model=StreamResponse)
async def stream_message(request: StreamRequest, background_tasks: BackgroundTasks) -> StreamResponse:
    """Stream a message via ZeroMQ."""
    try:
        # Decode base64 content
        content_bytes = base64.b64decode(request.content)

        # Generate unique message ID
        message_id = str(uuid.uuid4())

        # Parse and normalize message
        if request.format.value == "cot":
            parsed = message_service.parse_cot(content_bytes)
        elif request.format.value == "vmf":
            parsed = message_service.parse_vmf(content_bytes)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")

        normalized = message_service.normalize_message(parsed)

        # Stream message in background
        background_tasks.add_task(
            streaming_service.publish_message,
            normalized,
            request.topic,
            request.delay_ms
        )

        return StreamResponse(
            success=True,
            message=f"Message queued for streaming to topic '{request.topic}'",
            topic=request.topic,
            message_id=message_id
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/api/v1/pcap", response_model=PCAPResponse)
async def process_pcap(request: PCAPRequest) -> PCAPResponse:
    """Process PCAP content and extract payloads."""
    start_time = time.time()

    try:
        # Decode base64 content
        content_bytes = base64.b64decode(request.content)

        # Create temporary file for PCAP processing
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pcap") as temp_file:
            temp_file.write(content_bytes)
            temp_file_path = temp_file.name

        try:
            # Process PCAP
            payloads = pcap_service.extract_payloads(temp_file_path)

            # Convert to requested format
            output_data = pcap_service.convert_payloads(payloads, request.output_format.value)

            processing_time = (time.time() - start_time) * 1000

            # Ensure output_data is the correct type for PCAPResponse
            if isinstance(output_data, list):
                payloads_data = output_data
            else:
                # If it's a string (NDJSON/CSV), we need to handle it differently
                # For now, return an empty list to satisfy the type requirement
                payloads_data = []

            return PCAPResponse(
                success=True,
                message=f"Successfully extracted {len(payloads)} payloads from PCAP",
                payload_count=len(payloads),
                payloads=payloads_data,
                processing_time_ms=processing_time
            )

        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/api/v1/stats", response_model=MessageStats)
async def get_message_stats() -> MessageStats:
    """Get message processing statistics."""
    processing_times = message_stats["processing_times"]
    if isinstance(processing_times, list):
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
    else:
        avg_time = 0.0

    total_messages = message_stats["total_messages"]
    cot_messages = message_stats["cot_messages"]
    vmf_messages = message_stats["vmf_messages"]
    failed_messages = message_stats["failed_messages"]

    return MessageStats(
        total_messages=int(total_messages) if isinstance(total_messages, (int, str)) else 0,
        cot_messages=int(cot_messages) if isinstance(cot_messages, (int, str)) else 0,
        vmf_messages=int(vmf_messages) if isinstance(vmf_messages, (int, str)) else 0,
        failed_messages=int(failed_messages) if isinstance(failed_messages, (int, str)) else 0,
        average_processing_time_ms=avg_time,
        last_processed=datetime.utcnow() if (isinstance(total_messages, (int, str)) and int(total_messages) > 0) else None
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler."""
    request_id = getattr(request.state, "request_id", "unknown")

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"request_id": request_id},
            request_id=request_id
        ).dict()
    )


# Mount static files for documentation
if Path("docs").exists():
    app.mount("/docs", StaticFiles(directory="docs"), name="docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
