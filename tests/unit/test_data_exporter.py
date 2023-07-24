#!/usr/bin/env python3
from yaht.data_exporter import DataExporter


def test_pass_data_to_base_exporter():
    """Test passing data to the base exporter class"""
    exporter = DataExporter()
    example_data = "example data"
    exporter.export_data(example_data)
