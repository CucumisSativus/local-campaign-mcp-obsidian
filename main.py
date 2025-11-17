#!/usr/bin/env python3
"""MCP Server for RPG Campaign Management.

This server provides tools to access RPG campaign location data stored in markdown files.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool


def get_locations_directory() -> Path:
    """Get the locations directory from environment variable.

    Returns:
        Path to the locations directory

    Raises:
        SystemExit: If LOCATIONS_PATH is not set or directory doesn't exist
    """
    locations_path = os.environ.get("LOCATIONS_PATH")

    if not locations_path:
        print(
            "Error: LOCATIONS_PATH environment variable is not set.\n"
            "Please set it to the path where your location markdown files are stored.\n"
            "Example: export LOCATIONS_PATH=/path/to/your/campaign/Locations",
            file=sys.stderr,
        )
        sys.exit(1)

    path = Path(locations_path).expanduser().resolve()

    if not path.exists():
        print(
            f"Error: Locations directory does not exist: {path}\n"
            f"Please create the directory or update LOCATIONS_PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not path.is_dir():
        print(
            f"Error: LOCATIONS_PATH is not a directory: {path}\n"
            f"Please provide a valid directory path.",
            file=sys.stderr,
        )
        sys.exit(1)

    return path


def get_all_locations(locations_dir: Path) -> list[str]:
    """Get a list of all location names from the Locations directory.

    Args:
        locations_dir: Path to the directory containing location markdown files

    Returns:
        List of location names (without .md extension)
    """
    if not locations_dir.exists():
        return []

    locations = []
    for file_path in locations_dir.glob("*.md"):
        locations.append(file_path.stem)

    return sorted(locations)


def get_location_details(location_name: str, locations_dir: Path) -> str:
    """Get the full markdown content of a specific location.

    Args:
        location_name: Name of the location (without .md extension)
        locations_dir: Path to the directory containing location markdown files

    Returns:
        The markdown content of the location file

    Raises:
        FileNotFoundError: If the location file doesn't exist
    """
    file_path = locations_dir / f"{location_name}.md"

    if not file_path.exists():
        raise FileNotFoundError(f"Location '{location_name}' not found")

    return file_path.read_text(encoding="utf-8")


# Global variable to store the locations directory (initialized in main)
_locations_dir: Path | None = None


# Create the MCP server
app = Server("rpg-campaign-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the RPG campaign server."""
    return [
        Tool(
            name="list_locations",
            description="Get a list of all available campaign locations",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_location",
            description="Get detailed information about a specific location by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the location to retrieve",
                    }
                },
                "required": ["name"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for the RPG campaign server.

    Args:
        name: Name of the tool to call
        arguments: Arguments passed to the tool

    Returns:
        List of text content results

    Raises:
        ValueError: If the tool name is unknown
        RuntimeError: If locations directory is not initialized
    """
    if _locations_dir is None:
        raise RuntimeError("Locations directory not initialized")

    if name == "list_locations":
        locations = get_all_locations(_locations_dir)
        if not locations:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No locations found in {_locations_dir}. "
                        "Add markdown files to this directory."
                    ),
                )
            ]

        location_list = "\n".join(f"- {loc}" for loc in locations)
        return [
            TextContent(
                type="text",
                text=f"Available locations ({len(locations)}):\n{location_list}",
            )
        ]

    elif name == "get_location":
        location_name = arguments.get("name")
        if not location_name:
            return [
                TextContent(
                    type="text",
                    text="Error: 'name' parameter is required",
                )
            ]

        try:
            content = get_location_details(location_name, _locations_dir)
            return [
                TextContent(
                    type="text",
                    text=f"# {location_name}\n\n{content}",
                )
            ]
        except FileNotFoundError as e:
            available = get_all_locations(_locations_dir)
            available_text = ", ".join(available) if available else "none"
            return [
                TextContent(
                    type="text",
                    text=f"Error: {e}\n\nAvailable locations: {available_text}",
                )
            ]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    """Run the MCP server."""
    global _locations_dir
    _locations_dir = get_locations_directory()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
