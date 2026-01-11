"""
S3 export module for Grid Monitoring API
"""

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.client import Config
from mypy_boto3_s3.client import S3Client


class S3Exporter:
    """Handle data export to S3"""

    def __init__(
        self,
        access_key: str = "test",
        secret_key: str = "test",
        endpoint_url: str = "http://localhost:4566",
        region_name: str = "us-east-1",
    ) -> None:
        """Initialize S3 client"""
        self.s3_client: S3Client = boto3.client(  # pyright: ignore[reportUnknownMemberType]
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name,
            config=Config(signature_version="s3v4"),
        )
        self.bucket_name = "grid-monitor-exports"

    def ensure_bucket_exists(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            self.s3_client.create_bucket(Bucket=self.bucket_name)
        except self.s3_client.exceptions.BucketAlreadyExists:
            pass
        except self.s3_client.exceptions.BucketAlreadyOwnedByYou:
            pass

    def export_to_json(self, data: list[dict[str, Any]], object_name: str) -> dict[str, Any]:
        """Export data to S3 as JSON"""
        self.ensure_bucket_exists()

        try:
            json_data = json.dumps(data, default=str)
            self.s3_client.put_object(Bucket=self.bucket_name, Key=object_name, Body=json_data)
            return {
                "status": "success",
                "message": f"Data exported to {object_name}",
                "location": f"s3://{self.bucket_name}/{object_name}",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def export_to_csv(self, data: list[dict[str, Any]], object_name: str) -> dict[str, Any]:
        """Export data to S3 as CSV"""
        self.ensure_bucket_exists()

        try:
            if not data:
                return {"status": "error", "message": "No data to export"}

            # Create CSV in memory
            csv_buffer = io.StringIO()
            fieldnames = data[0].keys()
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

            csv_buffer.seek(0)
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=object_name, Body=csv_buffer.getvalue()
            )

            return {
                "status": "success",
                "message": f"Data exported to {object_name}",
                "location": f"s3://{self.bucket_name}/{object_name}",
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def export_voltage_data(self, data: list[dict[str, Any]], hours: int = 24) -> dict[str, Any]:
        """Export voltage readings"""
        timestamp = datetime.now(timezone.utc).isoformat()
        object_name = f"exports/voltage_{hours}h_{timestamp}.json"
        return self.export_to_json(data, object_name)

    def export_fault_events(self, data: list[dict[str, Any]]) -> dict[str, Any]:
        """Export fault events as CSV"""
        timestamp = datetime.now(timezone.utc).isoformat()
        object_name = f"exports/faults_{timestamp}.csv"
        return self.export_to_csv(data, object_name)

    def list_exports(self) -> dict[str, Any]:
        """List all exported files"""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            files: list[dict[str, Any]] = []
            if "Contents" in response:
                for obj in response["Contents"]:
                    key = obj.get("Key")
                    if key:
                        files.append(
                            {
                                "key": key,
                                "size": obj.get("Size", 0),
                                "modified": obj.get(
                                    "LastModified", datetime.now(timezone.utc)
                                ).isoformat(),
                            }
                        )
            return {"status": "success", "files": files}
        except Exception as e:
            return {"status": "error", "message": str(e)}
