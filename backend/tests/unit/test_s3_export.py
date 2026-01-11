"""
Unit tests for S3Exporter class in s3_export.py
"""

# pylint: disable=redefined-outer-name

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, cast
from unittest.mock import MagicMock, patch

import pytest

# Add backend to path (must be before s3_export import)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from s3_export import S3Exporter  # pylint: disable=wrong-import-position


@pytest.fixture
def s3_exporter() -> Generator[S3Exporter, Any, Any]:
    """Create S3Exporter instance with mocked boto3 client"""
    with patch("boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        mock_boto.return_value = mock_s3
        # Mock head_bucket to simulate bucket exists
        mock_s3.head_bucket.return_value = {}
        exporter = S3Exporter()
        exporter.s3_client = mock_s3
        yield exporter


def test_export_to_json_success(s3_exporter: S3Exporter) -> None:
    """Test exporting data to JSON format"""
    data: List[Dict[str, int | float | str]] = [
        {"id": 1, "value": 120.5, "timestamp": "2026-01-11T10:00:00"},
        {"id": 2, "value": 121.2, "timestamp": "2026-01-11T10:01:00"},
    ]

    result: Dict[str, Any] = s3_exporter.export_to_json(data, "test_export.json")

    assert result["status"] == "success"
    assert "test_export.json" in result["message"]
    assert result["location"] == f"s3://{s3_exporter.bucket_name}/test_export.json"
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    assert mock_client.put_object.call_count == 1
    call_args = mock_client.put_object.call_args
    assert call_args is not None
    assert call_args[1]["Key"] == "test_export.json"
    assert call_args[1]["Body"] is not None


def test_export_to_csv_success(s3_exporter: S3Exporter) -> None:
    """Test exporting data to CSV format"""
    data: List[Dict[str, Any]] = [
        {"id": 1, "voltage": 120.5, "timestamp": "2026-01-11T10:00:00"},
        {"id": 2, "voltage": 121.2, "timestamp": "2026-01-11T10:01:00"},
    ]

    result: Dict[str, Any] = s3_exporter.export_to_csv(data, "test_export.csv")

    assert result["status"] == "success"
    assert "test_export.csv" in result["message"]
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    assert mock_client.put_object.called
    call_args = mock_client.put_object.call_args
    assert call_args is not None
    assert call_args.kwargs["Body"] is not None


def test_export_to_csv_empty_data(s3_exporter: S3Exporter) -> None:
    """Test exporting empty data to CSV returns error"""
    data: List[Dict[str, Any]] = []

    result: Dict[str, Any] = s3_exporter.export_to_csv(data, "empty.csv")

    assert result["status"] == "error"
    assert "No data to export" in result["message"]


def test_export_voltage_data(s3_exporter: S3Exporter) -> None:
    """Test exporting voltage data"""
    data: List[Dict[str, Any]] = [
        {"sensor_id": "sensor1", "voltage": 120.5},
        {"sensor_id": "sensor2", "voltage": 121.2},
    ]

    result: Dict[str, Any] = s3_exporter.export_voltage_data(data, hours=24)

    assert result["status"] == "success"
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    assert mock_client.put_object.called
    call_args = mock_client.put_object.call_args
    assert call_args is not None
    assert call_args.kwargs["Key"].startswith("exports/voltage_24h_")


def test_export_voltage_data_custom_hours(s3_exporter: S3Exporter) -> None:
    """Test exporting voltage data with custom hours"""
    data: List[Dict[str, Any]] = [{"sensor_id": "sensor1", "voltage": 120.5}]

    result: Dict[str, Any] = s3_exporter.export_voltage_data(data, hours=48)

    assert result["status"] == "success"
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    call_args = mock_client.put_object.call_args
    assert call_args is not None
    assert "voltage_48h_" in call_args.kwargs["Key"]


def test_export_fault_events(s3_exporter: S3Exporter) -> None:
    """Test exporting fault events"""
    data: List[Dict[str, Any]] = [
        {"sensor_id": "sensor1", "fault_type": "overcurrent", "severity": "high"},
        {"sensor_id": "sensor2", "fault_type": "undervoltage", "severity": "medium"},
    ]

    result: Dict[str, Any] = s3_exporter.export_fault_events(data)

    assert result["status"] == "success"
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    assert mock_client.put_object.called
    call_args = mock_client.put_object.call_args
    assert call_args is not None
    assert call_args.kwargs["Key"].startswith("exports/faults_")
    assert call_args.kwargs["Key"].endswith(".csv")


def test_list_exports_with_files(s3_exporter: S3Exporter) -> None:
    """Test listing exports from S3"""
    mock_s3_objects: Dict[str, Any] = {
        "Contents": [
            {
                "Key": "exports/voltage_2026-01-11.json",
                "Size": 1024,
                "LastModified": datetime(2026, 1, 11, 10, 0, 0, tzinfo=timezone.utc),
            },
            {
                "Key": "exports/faults_2026-01-10.csv",
                "Size": 2048,
                "LastModified": datetime(2026, 1, 10, 15, 30, 0, tzinfo=timezone.utc),
            },
        ]
    }
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.list_objects_v2 = MagicMock(return_value=mock_s3_objects)

    result: Dict[str, Any] = s3_exporter.list_exports()

    assert result["status"] == "success"
    assert len(result["files"]) == 2
    assert result["files"][0]["key"] == "exports/voltage_2026-01-11.json"
    assert result["files"][0]["size"] == 1024
    assert result["files"][1]["key"] == "exports/faults_2026-01-10.csv"


def test_list_exports_empty(s3_exporter: S3Exporter) -> None:
    """Test listing exports when no files exist"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.list_objects_v2 = MagicMock(return_value={"Contents": []})

    result: Dict[str, Any] = s3_exporter.list_exports()

    assert result["status"] == "success"
    assert result["files"] == []


def test_generate_presigned_url_success(s3_exporter: S3Exporter) -> None:
    """Test generating presigned URL for download"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.generate_presigned_url = MagicMock(return_value="https://s3.mock.url/signed")

    result: Dict[str, Any] = s3_exporter.generate_presigned_url(
        "exports/test.json", expires_in=3600
    )

    assert result["status"] == "success"
    assert result["url"] == "https://s3.mock.url/signed"
    assert mock_client.generate_presigned_url.called


def test_generate_presigned_url_default_expiration(s3_exporter: S3Exporter) -> None:
    """Test generating presigned URL with default expiration"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.generate_presigned_url = MagicMock(return_value="https://s3.mock.url/signed")

    result: Dict[str, Any] = s3_exporter.generate_presigned_url("exports/test.json")

    assert result["status"] == "success"
    call_args = mock_client.generate_presigned_url.call_args
    assert call_args is not None
    assert call_args.kwargs["ExpiresIn"] == 3600  # Default


def test_export_to_json_handles_exception(s3_exporter: S3Exporter) -> None:
    """Test JSON export handles exceptions gracefully"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.put_object.side_effect = Exception("S3 error")

    result: Dict[str, Any] = s3_exporter.export_to_json([{"test": "data"}], "test.json")

    assert result["status"] == "error"
    assert "S3 error" in result["message"]


def test_export_to_csv_handles_exception(s3_exporter: S3Exporter) -> None:
    """Test CSV export handles exceptions gracefully"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.put_object.side_effect = Exception("S3 error")

    result: Dict[str, Any] = s3_exporter.export_to_csv([{"test": "data"}], "test.csv")

    assert result["status"] == "error"
    assert "S3 error" in result["message"]


def test_generate_presigned_url_handles_exception(s3_exporter: S3Exporter) -> None:
    """Test presigned URL generation handles exceptions"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.generate_presigned_url.side_effect = Exception("URL generation failed")

    result: Dict[str, Any] = s3_exporter.generate_presigned_url("exports/test.json")

    assert result["status"] == "error"
    assert "URL generation failed" in result["message"]


def test_list_exports_handles_exception(s3_exporter: S3Exporter) -> None:
    """Test list exports handles exceptions"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.list_objects_v2.side_effect = Exception("List failed")

    result: Dict[str, Any] = s3_exporter.list_exports()

    assert result["status"] == "error"
    assert "List failed" in result["message"]


def test_ensure_bucket_exists_creates_bucket(s3_exporter: S3Exporter) -> None:
    """Test ensure_bucket_exists creates bucket when it doesn't exist"""
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    mock_client.head_bucket.side_effect = Exception("Bucket does not exist")

    s3_exporter.ensure_bucket_exists()

    assert mock_client.create_bucket.called


def test_export_with_large_dataset(s3_exporter: S3Exporter) -> None:
    """Test exporting large datasets"""
    large_data: List[Dict[str, Any]] = [{"id": i, "value": i * 1.5} for i in range(10000)]

    result: Dict[str, Any] = s3_exporter.export_to_json(large_data, "large_export.json")

    assert result["status"] == "success"
    mock_client = cast(MagicMock, s3_exporter.s3_client)
    assert mock_client.put_object.called
