"""Tests for main module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from main import (
    DYSCRASIA_OPTIONS,
    Mood,
    ResonanceLevel,
    ResonanceResult,
    calculate_victims_resonance,
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


# Victims Resonance tests


def test_mood_enum_values() -> None:
    """Test that Mood enum has correct values."""
    assert Mood.CHOLERIC.value == "Choleric"
    assert Mood.MELANCHOLIC.value == "Melancholic"
    assert Mood.PHLEGMATIC.value == "Phlegmatic"
    assert Mood.SANGUINE.value == "Sanguine"


def test_resonance_level_enum_values() -> None:
    """Test that ResonanceLevel enum has correct values."""
    assert ResonanceLevel.NEGLIGIBLE.value == "Negligible"
    assert ResonanceLevel.FLEETING.value == "Fleeting"
    assert ResonanceLevel.INTENSE.value == "Intense"
    assert ResonanceLevel.ACUTE.value == "Acute"


def test_resonance_result_dataclass() -> None:
    """Test ResonanceResult dataclass."""
    result = ResonanceResult(level=ResonanceLevel.FLEETING)
    assert result.level == ResonanceLevel.FLEETING
    assert result.dyscrasia is None

    result_with_dyscrasia = ResonanceResult(level=ResonanceLevel.INTENSE, dyscrasia="vengeful")
    assert result_with_dyscrasia.level == ResonanceLevel.INTENSE
    assert result_with_dyscrasia.dyscrasia == "vengeful"


def test_dyscrasia_options_all_moods_present() -> None:
    """Test that all moods have dyscrasia options."""
    assert Mood.CHOLERIC in DYSCRASIA_OPTIONS
    assert Mood.MELANCHOLIC in DYSCRASIA_OPTIONS
    assert Mood.PHLEGMATIC in DYSCRASIA_OPTIONS
    assert Mood.SANGUINE in DYSCRASIA_OPTIONS


def test_dyscrasia_options_choleric() -> None:
    """Test choleric dyscrasia options."""
    expected = [
        "bully",
        "cycle of violence",
        "envy",
        "principled",
        "vengeful",
        "vicious",
        "driving",
    ]
    assert DYSCRASIA_OPTIONS[Mood.CHOLERIC] == expected


def test_dyscrasia_options_melancholic() -> None:
    """Test melancholic dyscrasia options."""
    expected = [
        "in mourning",
        "lost love",
        "lost relative",
        "massive failure",
        "nostalgic",
        "recalling",
    ]
    assert DYSCRASIA_OPTIONS[Mood.MELANCHOLIC] == expected


def test_dyscrasia_options_phlegmatic() -> None:
    """Test phlegmatic dyscrasia options."""
    expected = [
        "chill",
        "comfortably numb",
        "eating your emotions",
        "given up",
        "lone wolf",
        "procrastinate",
        "reflection",
    ]
    assert DYSCRASIA_OPTIONS[Mood.PHLEGMATIC] == expected


def test_dyscrasia_options_sanguine() -> None:
    """Test sanguine dyscrasia options."""
    expected = [
        "contagious enthusiasm",
        "smell game",
        "high on life",
        "manic high",
        "true love",
        "stirring",
    ]
    assert DYSCRASIA_OPTIONS[Mood.SANGUINE] == expected


def test_calculate_victims_resonance_returns_resonance_result() -> None:
    """Test that calculate_victims_resonance returns a ResonanceResult."""
    result = calculate_victims_resonance(Mood.CHOLERIC)
    assert isinstance(result, ResonanceResult)
    assert isinstance(result.level, ResonanceLevel)


def test_calculate_victims_resonance_negligible_no_dyscrasia() -> None:
    """Test that Negligible level never has dyscrasia."""
    import random

    random.seed(42)  # Set seed for reproducibility

    # Run multiple times to ensure Negligible never has dyscrasia
    for _ in range(100):
        result = calculate_victims_resonance(Mood.CHOLERIC)
        if result.level == ResonanceLevel.NEGLIGIBLE:
            assert result.dyscrasia is None


def test_calculate_victims_resonance_all_moods_work() -> None:
    """Test that all mood types work with calculate_victims_resonance."""
    for mood in Mood:
        result = calculate_victims_resonance(mood)
        assert isinstance(result, ResonanceResult)
        assert result.level in ResonanceLevel


def test_calculate_victims_resonance_dyscrasia_matches_mood() -> None:
    """Test that when dyscrasia occurs, it matches the mood type."""
    import random

    random.seed(123)  # Set seed for reproducibility

    for mood in Mood:
        for _ in range(100):
            result = calculate_victims_resonance(mood)
            if result.dyscrasia is not None:
                assert result.dyscrasia in DYSCRASIA_OPTIONS[mood]


def test_calculate_victims_resonance_acute_always_has_dyscrasia() -> None:
    """Test that Acute level always has dyscrasia."""
    import random

    random.seed(999)  # Set seed for reproducibility

    for mood in Mood:
        for _ in range(100):
            result = calculate_victims_resonance(mood)
            if result.level == ResonanceLevel.ACUTE:
                assert result.dyscrasia is not None
                assert result.dyscrasia in DYSCRASIA_OPTIONS[mood]
