"""
Pydantic models for the Interoperability Messaging Lab API.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, validator


class MessageFormat(str, Enum):
    """Supported message formats."""
    COT = "cot"
    VMF = "vmf"


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    NDJSON = "ndjson"
    CSV = "csv"


class ParseRequest(BaseModel):
    """Request model for parsing messages."""
    format: MessageFormat = Field(..., description="Message format to parse")
    content: str = Field(..., description="Base64-encoded message content")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Desired output format")

    @validator('content')
    def validate_content(cls, v):
        """Validate that content is valid base64."""
        try:
            import base64
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Content must be valid base64-encoded data")


class ParseResponse(BaseModel):
    """Response model for parsed messages."""
    success: bool = Field(..., description="Whether parsing was successful")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Union[dict[str, Any], str]] = Field(None, description="Parsed and normalized message data or formatted output")
    output_format: OutputFormat = Field(..., description="Output format used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class StreamRequest(BaseModel):
    """Request model for streaming messages."""
    format: MessageFormat = Field(..., description="Message format to stream")
    content: str = Field(..., description="Base64-encoded message content")
    topic: str = Field(default="tactical", description="Topic to publish to")
    delay_ms: int = Field(default=1000, ge=0, le=60000, description="Delay between messages in milliseconds")


class StreamResponse(BaseModel):
    """Response model for streaming operations."""
    success: bool = Field(..., description="Whether streaming was successful")
    message: str = Field(..., description="Human-readable message")
    topic: str = Field(..., description="Topic message was published to")
    message_id: str = Field(..., description="Unique message identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PCAPRequest(BaseModel):
    """Request model for PCAP processing."""
    content: str = Field(..., description="Base64-encoded PCAP content")
    output_format: OutputFormat = Field(default=OutputFormat.JSON, description="Desired output format")


class PCAPResponse(BaseModel):
    """Response model for PCAP processing."""
    success: bool = Field(..., description="Whether processing was successful")
    message: str = Field(..., description="Human-readable message")
    payload_count: int = Field(..., description="Number of payloads extracted")
    payloads: list[dict[str, Any]] = Field(..., description="Extracted payload data")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class HealthResponse(BaseModel):
    """Response model for health checks."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    dependencies: dict[str, str] = Field(..., description="Dependency status")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")


class MessageStats(BaseModel):
    """Message processing statistics."""
    total_messages: int = Field(..., description="Total messages processed")
    cot_messages: int = Field(..., description="CoT messages processed")
    vmf_messages: int = Field(..., description="VMF messages processed")
    failed_messages: int = Field(..., description="Failed message processing attempts")
    average_processing_time_ms: float = Field(..., description="Average processing time in milliseconds")
    last_processed: Optional[datetime] = Field(None, description="Timestamp of last processed message")
