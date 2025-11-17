"""Tests for main module."""

import sys
from io import StringIO
from unittest.mock import patch

from main import main


def test_main_prints_message() -> None:
    """Test that main() prints the expected message."""
    # Capture stdout
    captured_output = StringIO()
    with patch("sys.stdout", captured_output):
        main()

    # Verify the output
    assert captured_output.getvalue() == "Hello from local-campaign-mcp-obsidian!\n"


def test_main_returns_none() -> None:
    """Test that main() returns None."""
    result = main()
    assert result is None
