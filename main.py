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


def get_characters_directory() -> Path:
    """Get the characters directory from environment variable.

    Returns:
        Path to the characters directory

    Raises:
        SystemExit: If CHARACTERS_PATH is not set or directory doesn't exist
    """
    characters_path = os.environ.get("CHARACTERS_PATH")

    if not characters_path:
        print(
            "Error: CHARACTERS_PATH environment variable is not set.\n"
            "Please set it to the path where your character markdown files are stored.\n"
            "Example: export CHARACTERS_PATH=/path/to/your/campaign/Characters",
            file=sys.stderr,
        )
        sys.exit(1)

    path = Path(characters_path).expanduser().resolve()

    if not path.exists():
        print(
            f"Error: Characters directory does not exist: {path}\n"
            f"Please create the directory or update CHARACTERS_PATH.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not path.is_dir():
        print(
            f"Error: CHARACTERS_PATH is not a directory: {path}\n"
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


def get_all_characters(characters_dir: Path) -> list[dict[str, str]]:
    """Get a list of all characters with their organizations.

    Args:
        characters_dir: Path to the directory containing character subdirectories

    Returns:
        List of dictionaries with 'name' and 'organization' keys, sorted by organization then name
    """
    if not characters_dir.exists():
        return []

    characters = []

    # Recursively walk through all subdirectories
    for subdir in characters_dir.rglob("*"):
        if subdir.is_dir():
            # Get the relative path from characters_dir to determine organization
            rel_path = subdir.relative_to(characters_dir)
            organization = str(rel_path)

            # Find all .md files in this directory
            for file_path in subdir.glob("*.md"):
                # Skip files starting with __
                if file_path.name.startswith("__"):
                    continue

                characters.append({
                    "name": file_path.stem,
                    "organization": organization,
                })

    # Sort by organization first, then by name
    return sorted(characters, key=lambda x: (x["organization"], x["name"]))


def get_character_details(
    character_name: str, organization: str, characters_dir: Path
) -> str:
    """Get the full markdown content of a specific character.

    Args:
        character_name: Name of the character (without .md extension)
        organization: Organization/subfolder the character belongs to
        characters_dir: Path to the directory containing character subdirectories

    Returns:
        The markdown content of the character file

    Raises:
        FileNotFoundError: If the character file doesn't exist
    """
    file_path = characters_dir / organization / f"{character_name}.md"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Character '{character_name}' in organization '{organization}' not found"
        )

    return file_path.read_text(encoding="utf-8")


# Global variables to store directories (initialized in main)
_locations_dir: Path | None = None
_characters_dir: Path | None = None


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
        Tool(
            name="list_characters",
            description="Get a list of all available characters with their organizations",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_character",
            description=(
                "Get detailed information about a specific character by name and organization"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the character to retrieve",
                    },
                    "organization": {
                        "type": "string",
                        "description": "The organization/faction the character belongs to",
                    },
                },
                "required": ["name", "organization"],
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
    if _locations_dir is None or _characters_dir is None:
        raise RuntimeError("Directories not initialized")

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

    elif name == "list_characters":
        characters = get_all_characters(_characters_dir)
        if not characters:
            return [
                TextContent(
                    type="text",
                    text=(
                        f"No characters found in {_characters_dir}. "
                        "Add markdown files to subdirectories."
                    ),
                )
            ]

        # Group characters by organization for better readability
        current_org = None
        character_list = []
        for char in characters:
            if char["organization"] != current_org:
                current_org = char["organization"]
                character_list.append(f"\n**{current_org}**")
            character_list.append(f"  - {char['name']}")

        character_text = "\n".join(character_list)
        return [
            TextContent(
                type="text",
                text=f"Available characters ({len(characters)}):{character_text}",
            )
        ]

    elif name == "get_character":
        character_name = arguments.get("name")
        organization = arguments.get("organization")

        if not character_name:
            return [
                TextContent(
                    type="text",
                    text="Error: 'name' parameter is required",
                )
            ]

        if not organization:
            return [
                TextContent(
                    type="text",
                    text="Error: 'organization' parameter is required",
                )
            ]

        try:
            content = get_character_details(character_name, organization, _characters_dir)
            return [
                TextContent(
                    type="text",
                    text=f"# {character_name} ({organization})\n\n{content}",
                )
            ]
        except FileNotFoundError as e:
            characters = get_all_characters(_characters_dir)
            # Show characters from the same organization if available
            same_org = [c["name"] for c in characters if c["organization"] == organization]
            if same_org:
                available_text = f"Available in {organization}: {', '.join(same_org)}"
            else:
                all_orgs = sorted(set(c["organization"] for c in characters))
                available_text = f"Available organizations: {', '.join(all_orgs)}"
            return [
                TextContent(
                    type="text",
                    text=f"Error: {e}\n\n{available_text}",
                )
            ]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    """Run the MCP server."""
    global _locations_dir, _characters_dir
    _locations_dir = get_locations_directory()
    _characters_dir = get_characters_directory()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
