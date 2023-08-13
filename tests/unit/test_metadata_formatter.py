#!/usr/bin/env python3
from yaht.metadata_handling import encode_metadata, extract_metadata


def test_encode_string():
    """Test encoding a string.. into a .. string.."""
    raw_string = "some__ string"
    expected_string = "STRING:some__ string"
    encoded_string = encode_metadata(raw_string)
    assert encoded_string == expected_string


def test_extract_string():
    """Test getting the string back from the string. yeah."""
    encoded_string = "STRING:some__ string"
    expected_string = "some__ string"
    raw_string = extract_metadata(encoded_string)
    assert raw_string == expected_string


def test_encode_list():
    """Test formatting a list of sources into a string"""
    sources_list = ["source.one", "source.two", "source.three"]
    expected_sources = "LIST:source.one,source.two,source.three"
    encoded_souces = encode_metadata(sources_list)
    assert encoded_souces == expected_sources


def test_extract_list():
    """Test turning a string into a list of sources"""
    sources_string = "LIST:source.one,source.two,source.three"
    expected_sources = ["source.one", "source.two", "source.three"]
    encoded_sources = extract_metadata(sources_string)
    assert encoded_sources == expected_sources
