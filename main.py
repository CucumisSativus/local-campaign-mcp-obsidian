#!/usr/bin/env python3
"""MCP Server for RPG Campaign Management.

This server provides tools to access RPG campaign location data stored in markdown files.
"""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Directory where location markdown files are stored
LOCATIONS_DIR = Path(__file__).parent / "Locations"


def get_all_locations() -> list[str]:
    """Get a list of all location names from the Locations directory.

    Returns:
        List of location names (without .md extension)
    """
    if not LOCATIONS_DIR.exists():
        return []

    locations = []
    for file_path in LOCATIONS_DIR.glob("*.md"):
        locations.append(file_path.stem)

    return sorted(locations)


def get_location_details(location_name: str) -> str:
    """Get the full markdown content of a specific location.

    Args:
        location_name: Name of the location (without .md extension)

    Returns:
        The markdown content of the location file

    Raises:
        FileNotFoundError: If the location file doesn't exist
    """
    file_path = LOCATIONS_DIR / f"{location_name}.md"

    if not file_path.exists():
        raise FileNotFoundError(f"Location '{location_name}' not found")

    return file_path.read_text(encoding="utf-8")


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
    """
    if name == "list_locations":
        locations = get_all_locations()
        if not locations:
            return [
                TextContent(
                    type="text",
                    text="No locations found. The Locations directory is empty or doesn't exist.",
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
            content = get_location_details(location_name)
            return [
                TextContent(
                    type="text",
                    text=f"# {location_name}\n\n{content}",
                )
            ]
        except FileNotFoundError as e:
            available = get_all_locations()
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
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
