# RPG Campaign MCP Server

A Model Context Protocol (MCP) server for managing RPG campaign data (locations and characters) stored in Obsidian-compatible markdown files.

## Features

- **List Locations**: Get a list of all available campaign locations
- **Get Location Details**: Retrieve detailed information about a specific location
- **List Characters**: Get a list of all characters organized by faction/organization
- **Get Character Details**: Retrieve detailed information about a specific character
- **Get Story So Far**: Retrieve session notes and campaign progress from previous sessions

## Installation

1. Clone this repository
2. Install dependencies using uv:

```bash
uv sync
```

## Configuration

### Setting Up Your Directories

The server requires three environment variables to be set:

- `LOCATIONS_PATH`: Directory containing your location markdown files
- `CHARACTERS_PATH`: Directory containing your character markdown files organized by faction/organization
- `SESSIONS_PATH`: Directory containing your session notes

```bash
export LOCATIONS_PATH=/path/to/your/campaign/Locations
export CHARACTERS_PATH=/path/to/your/campaign/Characters
export SESSIONS_PATH=/path/to/your/campaign/sessions
```

For example, if you use Obsidian and have a vault at `/Users/you/Documents/Campaign`:

```bash
export LOCATIONS_PATH=/Users/you/Documents/Campaign/Locations
export CHARACTERS_PATH=/Users/you/Documents/Campaign/Characters
export SESSIONS_PATH=/Users/you/Documents/Campaign/sessions
```

## Usage

### Running the Server

The server uses stdio for communication with MCP clients. You must set all environment variables:

```bash
LOCATIONS_PATH=/path/to/your/locations CHARACTERS_PATH=/path/to/your/characters SESSIONS_PATH=/path/to/your/sessions python main.py
```

### Adding Locations

Simply add markdown files to your configured locations directory. Each markdown file represents a location in your campaign.

Example structure:
```
/your/campaign/Locations/
├── Tavern.md
├── Forest.md
└── Castle.md
```

The filename (without `.md` extension) becomes the location name that you use to retrieve it.

### Adding Characters

Characters should be organized in subdirectories by faction/organization. Files starting with `__` (like `__table.md`) are automatically ignored.

Example structure:
```
/your/campaign/Characters/
├── anarchs/
│   ├── __table.md          # Ignored
│   └── Rico "Roadhouse" Vega.md
├── camarilla/
│   ├── __table.md          # Ignored
│   ├── Prince Sebastian Veyron.md
│   └── Adrian Rook.md
└── Mortals/
    ├── Victor Manelli.md
    └── second inquisition/
        ├── Raphael Kirby.md
        └── Sister Clara Ibarra.md
```

The subdirectory structure determines the character's organization, and the filename (without `.md` extension) becomes the character name.

### Adding Session Notes

Session notes should be stored in a `__result` file in your sessions directory. This file contains the story so far from previous sessions.

Example structure:
```
/your/campaign/sessions/
└── __result
```

The `__result` file should contain markdown-formatted notes about what has happened in previous game sessions.

### Available Tools

#### list_locations

Lists all available campaign locations from your configured directory.

```json
{
  "name": "list_locations"
}
```

#### get_location

Retrieves detailed information about a specific location by name.

```json
{
  "name": "get_location",
  "arguments": {
    "name": "Tavern"
  }
}
```

#### list_characters

Lists all available characters grouped by their organization/faction.

```json
{
  "name": "list_characters"
}
```

#### get_character

Retrieves detailed information about a specific character by name and organization.

```json
{
  "name": "get_character",
  "arguments": {
    "name": "Prince Sebastian Veyron",
    "organization": "camarilla"
  }
}
```

For nested organizations, use the path format:

```json
{
  "name": "get_character",
  "arguments": {
    "name": "Raphael Kirby",
    "organization": "Mortals/second inquisition"
  }
}
```

#### get_story_so_far

Retrieves the story so far from previous session notes.

```json
{
  "name": "get_story_so_far"
}
```

## MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add the following to your client configuration.

### Claude Desktop Configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rpg-campaign": {
      "command": "python",
      "args": ["/absolute/path/to/local-campaign-mcp-obsidian/main.py"],
      "env": {
        "LOCATIONS_PATH": "/absolute/path/to/your/campaign/Locations",
        "CHARACTERS_PATH": "/absolute/path/to/your/campaign/Characters",
        "SESSIONS_PATH": "/absolute/path/to/your/campaign/sessions"
      }
    }
  }
}
```

Or if using uv:

```json
{
  "mcpServers": {
    "rpg-campaign": {
      "command": "uv",
      "args": ["run", "/absolute/path/to/local-campaign-mcp-obsidian/main.py"],
      "env": {
        "LOCATIONS_PATH": "/absolute/path/to/your/campaign/Locations",
        "CHARACTERS_PATH": "/absolute/path/to/your/campaign/Characters",
        "SESSIONS_PATH": "/absolute/path/to/your/campaign/sessions"
      }
    }
  }
}
```

**Important**: Use absolute paths in the configuration file, not relative paths.

## Development

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy main.py
```

### Linting

```bash
uv run ruff check .
```

## License

MIT
