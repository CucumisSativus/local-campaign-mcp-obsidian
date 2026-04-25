"""Tests for main module."""

import os
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from main import (
    DYSCRASIA_OPTIONS,
    Mood,
    ResonanceLevel,
    ResonanceResult,
    _APIKeyMiddleware,
    _RateLimiter,
    _safe_join,
    _validate_flat_name,
    _validate_nested_name,
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


def test_calculate_victims_resonance_only_acute_has_dyscrasia() -> None:
    """Test that only Acute level has dyscrasia."""
    import random

    random.seed(42)  # Set seed for reproducibility

    for _ in range(100):
        result = calculate_victims_resonance(Mood.CHOLERIC)
        if result.level == ResonanceLevel.ACUTE:
            assert result.dyscrasia is not None
        else:
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


# ---------------------------------------------------------------------------
# Security: path-component validation
# ---------------------------------------------------------------------------


class TestValidateFlatName:
    def test_rejects_dotdot(self) -> None:
        with pytest.raises(ValueError):
            _validate_flat_name("../etc/passwd", "name")

    def test_rejects_forward_slash(self) -> None:
        with pytest.raises(ValueError):
            _validate_flat_name("sub/dir", "name")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(ValueError):
            _validate_flat_name("foo\\bar", "name")

    def test_rejects_null_byte(self) -> None:
        with pytest.raises(ValueError):
            _validate_flat_name("foo\x00bar", "name")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError):
            _validate_flat_name("", "name")

    def test_allows_spaces(self) -> None:
        _validate_flat_name("Dark Forest", "name")  # must not raise

    def test_allows_normal_name(self) -> None:
        _validate_flat_name("Prince Sebastian", "name")  # must not raise


class TestValidateNestedName:
    def test_rejects_dotdot(self) -> None:
        with pytest.raises(ValueError):
            _validate_nested_name("../etc", "org")

    def test_rejects_null_byte(self) -> None:
        with pytest.raises(ValueError):
            _validate_nested_name("guild\x00evil", "org")

    def test_rejects_empty(self) -> None:
        with pytest.raises(ValueError):
            _validate_nested_name("", "org")

    def test_allows_forward_slash(self) -> None:
        _validate_nested_name("Mortals/second inquisition", "org")  # must not raise

    def test_allows_normal_name(self) -> None:
        _validate_nested_name("camarilla", "org")  # must not raise


class TestSafeJoin:
    def test_normal_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir).resolve()
            result = _safe_join(base, "location.md")
            assert result == base / "location.md"

    def test_nested_normal_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir).resolve()
            result = _safe_join(base, "org", "char.md")
            assert result == base / "org" / "char.md"

    def test_rejects_dotdot_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir).resolve()
            with pytest.raises(ValueError, match="Access denied"):
                _safe_join(base, "../outside.md")

    def test_rejects_absolute_path_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir).resolve()
            # Path("/etc") as a component replaces the base on POSIX
            with pytest.raises(ValueError, match="Access denied"):
                _safe_join(base, "/etc/passwd")

    def test_rejects_deep_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base = Path(tmp_dir).resolve()
            with pytest.raises(ValueError, match="Access denied"):
                _safe_join(base, "sub", "../../etc/passwd")


class TestGetLocationDetailsPathSafety:
    def test_rejects_dotdot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_location_details("../evil", Path(tmp_dir))

    def test_rejects_slash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_location_details("sub/dir", Path(tmp_dir))

    def test_rejects_null_byte(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_location_details("foo\x00bar", Path(tmp_dir))

    def test_valid_name_still_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(FileNotFoundError):
                get_location_details("NonExistent", Path(tmp_dir))


class TestGetCharacterDetailsPathSafety:
    def test_rejects_dotdot_in_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_character_details("../evil", "camarilla", Path(tmp_dir))

    def test_rejects_dotdot_in_organization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_character_details("Character", "../etc", Path(tmp_dir))

    def test_rejects_null_byte_in_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_character_details("foo\x00bar", "camarilla", Path(tmp_dir))

    def test_rejects_null_byte_in_org(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_character_details("Character", "org\x00evil", Path(tmp_dir))

    def test_rejects_slash_in_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError):
                get_character_details("sub/evil", "camarilla", Path(tmp_dir))

    def test_nested_org_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            (tmp_path / "Mortals" / "second inquisition").mkdir(parents=True)
            (tmp_path / "Mortals" / "second inquisition" / "Raphael.md").write_text("content")
            result = get_character_details("Raphael", "Mortals/second inquisition", tmp_path)
            assert result == "content"

    def test_valid_inputs_still_raise_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with pytest.raises(FileNotFoundError):
                get_character_details("Nobody", "camarilla", Path(tmp_dir))


# ---------------------------------------------------------------------------
# Security: rate limiter
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_allows_requests_under_limit(self) -> None:
        limiter = _RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.is_allowed("client") is True

    def test_blocks_when_limit_exceeded(self) -> None:
        limiter = _RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.is_allowed("client")
        assert limiter.is_allowed("client") is False

    def test_different_clients_tracked_independently(self) -> None:
        limiter = _RateLimiter(max_requests=2, window_seconds=60)
        limiter.is_allowed("alice")
        limiter.is_allowed("alice")
        assert limiter.is_allowed("alice") is False
        assert limiter.is_allowed("bob") is True

    def test_window_expiry_allows_new_requests(self) -> None:
        import time

        limiter = _RateLimiter(max_requests=2, window_seconds=1)
        limiter.is_allowed("client")
        limiter.is_allowed("client")
        assert limiter.is_allowed("client") is False
        time.sleep(1.05)
        assert limiter.is_allowed("client") is True


# ---------------------------------------------------------------------------
# Security: API key middleware (async)
# ---------------------------------------------------------------------------


def _make_http_scope(
    headers: list[tuple[bytes, bytes]] | None = None,
    client_ip: str = "127.0.0.1",
) -> MutableMapping[str, Any]:
    return {
        "type": "http",
        "method": "GET",
        "path": "/mcp",
        "headers": headers or [],
        "client": (client_ip, 12345),
    }


async def _collect_response(
    middleware: _APIKeyMiddleware,
    scope: MutableMapping[str, Any],
) -> dict[str, Any]:
    """Run middleware and collect the first http.response.start message."""
    sent: list[MutableMapping[str, Any]] = []

    async def receive() -> MutableMapping[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: MutableMapping[str, Any]) -> None:
        sent.append(message)

    await middleware(scope, receive, send)
    return dict(sent[0]) if sent else {}


@pytest.mark.anyio
async def test_middleware_rejects_missing_token() -> None:
    app_reached = False

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        nonlocal app_reached
        app_reached = True

    mw = _APIKeyMiddleware(inner, "a" * 32)
    response = await _collect_response(mw, _make_http_scope())
    assert response["status"] == 401
    assert not app_reached


@pytest.mark.anyio
async def test_middleware_rejects_wrong_token() -> None:
    app_reached = False

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        nonlocal app_reached
        app_reached = True

    mw = _APIKeyMiddleware(inner, "correct-key" + "x" * 21)
    headers = [(b"authorization", b"Bearer wrong-key" + b"x" * 21)]
    response = await _collect_response(mw, _make_http_scope(headers))
    assert response["status"] == 401
    assert not app_reached


@pytest.mark.anyio
async def test_middleware_accepts_correct_token() -> None:
    api_key = "mysecretkey" + "x" * 21

    app_reached = False

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        nonlocal app_reached
        app_reached = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    mw = _APIKeyMiddleware(inner, api_key)
    headers = [(b"authorization", f"Bearer {api_key}".encode())]
    response = await _collect_response(mw, _make_http_scope(headers))
    assert response["status"] == 200
    assert app_reached


@pytest.mark.anyio
async def test_middleware_returns_429_when_rate_limited() -> None:
    api_key = "validkey" + "x" * 24
    headers = [(b"authorization", f"Bearer {api_key}".encode())]

    call_count = 0

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        nonlocal call_count
        call_count += 1
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    mw = _APIKeyMiddleware.__new__(_APIKeyMiddleware)
    mw._app = inner
    mw._api_key_bytes = api_key.encode()
    mw._limiter = _RateLimiter(max_requests=2, window_seconds=60)

    scope = _make_http_scope(headers)
    await _collect_response(mw, scope)
    await _collect_response(mw, scope)
    response = await _collect_response(mw, scope)  # 3rd request — over limit

    assert response["status"] == 429
    assert call_count == 2  # inner app only reached for the first two


@pytest.mark.anyio
async def test_middleware_passes_lifespan_events_without_auth() -> None:
    """Non-HTTP scopes (lifespan) must bypass the auth check."""
    lifespan_reached = False

    async def inner(scope: Any, receive: Any, send: Any) -> None:
        nonlocal lifespan_reached
        lifespan_reached = True

    mw = _APIKeyMiddleware(inner, "a" * 32)
    lifespan_scope: MutableMapping[str, Any] = {"type": "lifespan"}

    async def receive() -> MutableMapping[str, Any]:
        return {"type": "lifespan.startup"}

    async def send(message: MutableMapping[str, Any]) -> None:
        pass

    await mw(lifespan_scope, receive, send)
    assert lifespan_reached
