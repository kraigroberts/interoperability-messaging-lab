"""
Tests for the Interoperability Messaging Lab REST API.
"""

import base64
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Import our API app
try:
    from src.api.app import app
except ImportError:
    from api.app import app


@pytest.fixture
def client():
    """Create test client for the API."""
    return TestClient(app)


@pytest.fixture
def sample_cot_content():
    """Sample CoT XML content encoded in base64."""
    xml_content = b'<event version="2.0" uid="T-123" type="a-f-A" how="m-g" time="2025-08-14T12:00:00Z"><point lat="38.7" lon="-77.2"/></event>'
    return base64.b64encode(xml_content).decode('utf-8')


@pytest.fixture
def sample_vmf_content():
    """Sample VMF binary content encoded in base64."""
    # Create a proper VMF binary structure matching the parser expectations
    # Format: magic(4) + msg_type(2) + lat(8) + lon(8) + timestamp(8) = 30 bytes
    import struct
    binary_content = struct.pack("<4sHddQ", b"VMF1", 7, 38.7, -77.2, 1725000000)
    return base64.b64encode(binary_content).decode('utf-8')


class TestAPIRoot:
    """Test the root API endpoint."""

    def test_root_endpoint(self, client):
        """Test that root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Interoperability Messaging Lab API"
        assert data["version"] == "0.1.0"
        assert "docs" in data
        assert "health" in data


class TestAPIHealth:
    """Test the health check endpoint."""

    def test_health_endpoint(self, client):
        """Test that health endpoint returns system status."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"
        assert "dependencies" in data
        assert "uptime_seconds" in data
        assert data["uptime_seconds"] > 0

    def test_health_dependencies(self, client):
        """Test that health endpoint checks dependencies."""
        response = client.get("/health")
        data = response.json()

        # Check that key dependencies are reported
        dependencies = data["dependencies"]
        assert "lxml" in dependencies
        assert "scapy" in dependencies
        assert "pyzmq" in dependencies
        assert "jsonschema" in dependencies


class TestAPIParse:
    """Test the message parsing endpoint."""

    def test_parse_cot_message(self, client, sample_cot_content):
        """Test parsing a CoT message."""
        request_data = {
            "format": "cot",
            "content": sample_cot_content,
            "output_format": "json"
        }

        response = client.post("/api/v1/parse", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "Successfully parsed COT message" in data["message"]
        assert data["output_format"] == "json"
        assert data["data"] is not None
        assert data["processing_time_ms"] > 0

    def test_parse_vmf_message(self, client, sample_vmf_content):
        """Test parsing a VMF message."""
        request_data = {
            "format": "vmf",
            "content": sample_vmf_content,
            "output_format": "json"
        }

        response = client.post("/api/v1/parse", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "Successfully parsed VMF message" in data["message"]
        assert data["output_format"] == "json"
        assert data["data"] is not None

    def test_parse_invalid_format(self, client, sample_cot_content):
        """Test parsing with invalid format."""
        request_data = {
            "format": "invalid",
            "content": sample_cot_content,
            "output_format": "json"
        }

        response = client.post("/api/v1/parse", json=request_data)
        assert response.status_code == 422  # FastAPI validation error
        assert "Input should be 'cot' or 'vmf'" in response.text

    def test_parse_invalid_base64(self, client):
        """Test parsing with invalid base64 content."""
        request_data = {
            "format": "cot",
            "content": "invalid-base64!",
            "output_format": "json"
        }

        response = client.post("/api/v1/parse", json=request_data)
        assert response.status_code == 422  # FastAPI validation error
        assert "Content must be valid base64-encoded data" in response.text

    def test_parse_different_output_formats(self, client, sample_cot_content):
        """Test parsing with different output formats."""
        formats = ["json", "ndjson", "csv"]

        for fmt in formats:
            request_data = {
                "format": "cot",
                "content": sample_cot_content,
                "output_format": fmt
            }

            response = client.post("/api/v1/parse", json=request_data)
            assert response.status_code == 200

            data = response.json()
            assert data["success"] is True
            assert data["output_format"] == fmt


class TestAPIStream:
    """Test the message streaming endpoint."""

    @patch('src.api.services.StreamingService.publish_message')
    def test_stream_message(self, mock_publish, client, sample_cot_content):
        """Test streaming a message."""
        mock_publish.return_value = None

        request_data = {
            "format": "cot",
            "content": sample_cot_content,
            "topic": "test-topic",
            "delay_ms": 1000
        }

        response = client.post("/api/v1/stream", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "queued for streaming" in data["message"]
        assert data["topic"] == "test-topic"
        assert "message_id" in data

    def test_stream_invalid_format(self, client, sample_cot_content):
        """Test streaming with invalid format."""
        request_data = {
            "format": "invalid",
            "content": sample_cot_content,
            "topic": "test-topic"
        }

        response = client.post("/api/v1/stream", json=request_data)
        assert response.status_code == 422  # FastAPI validation error
        assert "Input should be 'cot' or 'vmf'" in response.text


class TestAPIPCAP:
    """Test the PCAP processing endpoint."""

    @patch('src.api.services.PCAPService.extract_payloads')
    def test_process_pcap(self, mock_extract, client):
        """Test processing PCAP content."""
        # Mock PCAP service to return sample payloads
        mock_payloads = [
            {
                "filename": "payload1.bin",
                "size_bytes": 100,
                "content": base64.b64encode(b"test content").decode('utf-8'),
                "content_type": "binary"
            }
        ]
        mock_extract.return_value = mock_payloads

        # Create sample PCAP content
        pcap_content = b"dummy pcap content"
        encoded_content = base64.b64encode(pcap_content).decode('utf-8')

        request_data = {
            "content": encoded_content,
            "output_format": "json"
        }

        response = client.post("/api/v1/pcap", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["payload_count"] == 1
        assert len(data["payloads"]) == 1
        assert data["processing_time_ms"] > 0


class TestAPIStats:
    """Test the statistics endpoint."""

    def test_stats_endpoint(self, client):
        """Test that stats endpoint returns message statistics."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_messages" in data
        assert "cot_messages" in data
        assert "vmf_messages" in data
        assert "failed_messages" in data
        assert "average_processing_time_ms" in data
        assert isinstance(data["total_messages"], int)
        assert isinstance(data["cot_messages"], int)
        assert isinstance(data["vmf_messages"], int)


class TestAPIMiddleware:
    """Test API middleware functionality."""

    def test_request_id_header(self, client):
        """Test that request ID is added to response headers."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0

    def test_timing_headers(self, client):
        """Test that timing headers are added to response."""
        response = client.get("/health")
        assert "X-Processing-Time" in response.headers
        assert "X-Processing-Time-MS" in response.headers

        # Check that timing values are reasonable
        timing = float(response.headers["X-Processing-Time"])
        timing_ms = int(response.headers["X-Processing-Time-MS"])
        assert timing > 0
        assert timing_ms > 0
        assert abs(timing_ms - (timing * 1000)) < 10  # Allow small rounding differences


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_global_exception_handler(self, client):
        """Test that global exception handler works."""
        # This test would require mocking a service to throw an exception
        # For now, we'll just verify the endpoint exists
        response = client.get("/health")
        assert response.status_code == 200

    def test_validation_errors(self, client):
        """Test that validation errors are handled properly."""
        # Test with missing required fields
        response = client.post("/api/v1/parse", json={})
        assert response.status_code == 422  # Validation error

        # Test with invalid enum values
        response = client.post("/api/v1/parse", json={
            "format": "invalid_format",
            "content": "dGVzdA==",  # "test" in base64
            "output_format": "invalid_output"
        })
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
