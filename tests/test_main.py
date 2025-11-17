"""Tests for main module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from main import (
    get_all_characters,
    get_all_locations,
    get_character_details,
    get_characters_directory,
    get_location_details,
    get_locations_directory,
)


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


# Character-related tests


def test_get_characters_directory_missing_env_var() -> None:
    """Test that get_characters_directory exits when CHARACTERS_PATH is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SystemExit) as exc_info:
            get_characters_directory()
        assert exc_info.value.code == 1


def test_get_characters_directory_nonexistent_path() -> None:
    """Test that get_characters_directory exits when path doesn't exist."""
    with patch.dict(os.environ, {"CHARACTERS_PATH": "/nonexistent/path"}):
        with pytest.raises(SystemExit) as exc_info:
            get_characters_directory()
        assert exc_info.value.code == 1


def test_get_characters_directory_file_instead_of_dir() -> None:
    """Test that get_characters_directory exits when path is a file."""
    with tempfile.NamedTemporaryFile() as tmp_file:
        with patch.dict(os.environ, {"CHARACTERS_PATH": tmp_file.name}):
            with pytest.raises(SystemExit) as exc_info:
                get_characters_directory()
            assert exc_info.value.code == 1


def test_get_characters_directory_valid_path() -> None:
    """Test that get_characters_directory returns path when valid."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with patch.dict(os.environ, {"CHARACTERS_PATH": tmp_dir}):
            result = get_characters_directory()
            assert result == Path(tmp_dir).resolve()


def test_get_all_characters_empty_directory() -> None:
    """Test get_all_characters with empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        characters = get_all_characters(Path(tmp_dir))
        assert characters == []


def test_get_all_characters_with_files() -> None:
    """Test get_all_characters with markdown files in subdirectories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create subdirectories with character files
        (tmp_path / "camarilla").mkdir()
        (tmp_path / "camarilla" / "Prince Sebastian.md").write_text("Prince content")
        (tmp_path / "camarilla" / "Adrian Rook.md").write_text("Adrian content")

        (tmp_path / "anarchs").mkdir()
        (tmp_path / "anarchs" / "Rico Vega.md").write_text("Rico content")

        characters = get_all_characters(tmp_path)

        # Should be sorted by organization then name
        assert characters == [
            {"name": "Rico Vega", "organization": "anarchs"},
            {"name": "Adrian Rook", "organization": "camarilla"},
            {"name": "Prince Sebastian", "organization": "camarilla"},
        ]


def test_get_all_characters_skips_dunder_files() -> None:
    """Test get_all_characters skips files starting with __."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create subdirectory with character files and __table.md
        (tmp_path / "camarilla").mkdir()
        (tmp_path / "camarilla" / "Prince Sebastian.md").write_text("Prince content")
        (tmp_path / "camarilla" / "__table.md").write_text("Table content")
        (tmp_path / "camarilla" / "__index.md").write_text("Index content")

        characters = get_all_characters(tmp_path)

        # Should only include Prince Sebastian, not the __ files
        assert len(characters) == 1
        assert characters[0]["name"] == "Prince Sebastian"


def test_get_all_characters_with_nested_directories() -> None:
    """Test get_all_characters with nested directory structure."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Create nested directory structure
        (tmp_path / "Mortals" / "second inquisition").mkdir(parents=True)
        (tmp_path / "Mortals" / "second inquisition" / "Raphael Kirby.md").write_text(
            "Raphael content"
        )
        (tmp_path / "Mortals" / "Victor Manelli.md").write_text("Victor content")

        characters = get_all_characters(tmp_path)

        # Should handle nested paths correctly
        assert len(characters) == 2
        assert any(
            c["name"] == "Raphael Kirby" and c["organization"] == "Mortals/second inquisition"
            for c in characters
        )
        assert any(
            c["name"] == "Victor Manelli" and c["organization"] == "Mortals" for c in characters
        )


def test_get_all_characters_nonexistent_directory() -> None:
    """Test get_all_characters with nonexistent directory."""
    characters = get_all_characters(Path("/nonexistent/directory"))
    assert characters == []


def test_get_character_details_valid_character() -> None:
    """Test get_character_details with valid character."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "camarilla").mkdir()

        content = "---\nClan: Ventrue\n---\n\n## Personality\n\nRegal and commanding."
        (tmp_path / "camarilla" / "Prince Sebastian.md").write_text(content)

        result = get_character_details("Prince Sebastian", "camarilla", tmp_path)
        assert result == content


def test_get_character_details_nonexistent_character() -> None:
    """Test get_character_details with nonexistent character."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "camarilla").mkdir()

        with pytest.raises(FileNotFoundError) as exc_info:
            get_character_details("NonexistentCharacter", "camarilla", tmp_path)

        assert "NonexistentCharacter" in str(exc_info.value)
        assert "camarilla" in str(exc_info.value)


def test_get_character_details_nonexistent_organization() -> None:
    """Test get_character_details with nonexistent organization."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        with pytest.raises(FileNotFoundError) as exc_info:
            get_character_details("Some Character", "nonexistent_org", tmp_path)

        assert "Some Character" in str(exc_info.value)
        assert "nonexistent_org" in str(exc_info.value)
