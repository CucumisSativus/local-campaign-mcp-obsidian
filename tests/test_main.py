"""Tests for main module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from main import get_all_locations, get_location_details, get_locations_directory


def test_get_locations_directory_missing_env_var() -> None:
    """Test that get_locations_directory exits when LOCATIONS_PATH is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            get_locations_directory()
        assert exc_info.value.code == 1


def test_get_locations_directory_nonexistent_path() -> None:
    """Test that get_locations_directory exits when path doesn't exist."""
    with patch.dict(os.environ, {"LOCATIONS_PATH": "/nonexistent/path"}):
        with pytest.raises(SystemExit) as exc_info:
            get_locations_directory()
        assert exc_info.value.code == 1


def test_get_locations_directory_file_instead_of_dir() -> None:
    """Test that get_locations_directory exits when path is a file."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        with patch.dict(os.environ, {"LOCATIONS_PATH": tmp_file.name}):
            with pytest.raises(SystemExit) as exc_info:
                get_locations_directory()
            assert exc_info.value.code == 1


def test_get_locations_directory_valid_path() -> None:
    """Test that get_locations_directory returns path when valid."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"LOCATIONS_PATH": tmp_dir}):
            result = get_locations_directory()
            assert result == Path(tmp_dir).resolve()


def test_get_all_locations_empty_directory() -> None:
    """Test get_all_locations with empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        locations = get_all_locations(Path(tmp_dir))
        assert locations == []


def test_get_all_locations_with_files() -> None:
    """Test get_all_locations with markdown files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create some markdown files
        (tmp_path / "Location1.md").write_text("Content 1")
        (tmp_path / "Location2.md").write_text("Content 2")
        (tmp_path / "not_markdown.txt").write_text("Not markdown")

        locations = get_all_locations(tmp_path)

        # Should only include .md files, sorted alphabetically
        assert locations == ["Location1", "Location2"]


def test_get_all_locations_nonexistent_directory() -> None:
    """Test get_all_locations with nonexistent directory."""
    locations = get_all_locations(Path("/nonexistent/directory"))
    assert locations == []


def test_get_location_details_valid_location() -> None:
    """Test get_location_details with valid location."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        content = "# Test Location\n\nThis is a test location."
        (tmp_path / "TestLocation.md").write_text(content)

        result = get_location_details("TestLocation", tmp_path)
        assert result == content


def test_get_location_details_nonexistent_location() -> None:
    """Test get_location_details with nonexistent location."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            get_location_details("NonexistentLocation", tmp_path)

        assert "NonexistentLocation" in str(exc_info.value)


def test_get_location_details_with_special_characters() -> None:
    """Test get_location_details with location names containing spaces."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        content = "# Dark Forest\n\nA spooky place."
        (tmp_path / "Dark Forest.md").write_text(content)

        result = get_location_details("Dark Forest", tmp_path)
        assert result == content
