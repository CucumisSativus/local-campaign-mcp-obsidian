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

The server supports two transport modes:

| Mode | Use case | How to enable |
|------|----------|---------------|
| **stdio** (default) | Local Claude Desktop | No extra config needed |
| **HTTP** | Remote/cloud hosting | Set `MCP_TRANSPORT=http` |

### Local: Claude Desktop (stdio)

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

---

## Remote Deployment (HTTP mode)

You can host the server on any machine and connect to it from Claude over the network.

### 1. Generate an API key

The server requires a secret key of at least 32 characters. Generate one:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Keep this value — you will need it in every Claude client configuration below.

### 2. Start the server

```bash
export LOCATIONS_PATH=/path/to/campaign/Locations
export CHARACTERS_PATH=/path/to/campaign/Characters
export SESSIONS_PATH=/path/to/campaign/sessions
export MCP_TRANSPORT=http
export MCP_API_KEY=<your-generated-key>
export MCP_PORT=8000        # optional, default 8000
export MCP_HOST=0.0.0.0     # optional, default 0.0.0.0

python main.py
# or: uv run python main.py
```

The server listens at `http://<host>:<port>/mcp`.  
Put it behind a TLS-terminating reverse proxy (nginx, Caddy, etc.) for production use.

### 3. Connect Claude

#### Claude Code (CLI)

```bash
claude mcp add \
  --transport http \
  --header "Authorization: Bearer YOUR_API_KEY" \
  rpg-campaign \
  http://your-server:8000/mcp
```

#### Claude.ai (web)

> **Limitation**: The web UI connector form only supports OAuth — it has no field for a
> static Bearer token. The steps below use the **Claude API** instead, which does accept
> a Bearer token directly. If you want the Connectors UI to work, you would need to add
> OAuth support to the server.

**Via the Claude API** (works with the Bearer token this server uses):

```python
import anthropic

client = anthropic.Anthropic(api_key="YOUR_ANTHROPIC_API_KEY")
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=1000,
    messages=[{"role": "user", "content": "List all campaign locations."}],
    mcp_servers=[{
        "type": "url",
        "url": "https://your-server:8000/mcp",
        "name": "rpg-campaign",
        "authorization_token": "your-mcp-api-key",
    }],
    betas=["mcp-client-2025-11-20"],
)
print(response.content)
```

**Via the Connectors UI** (for reference, requires OAuth on the server):

1. Go to **https://claude.ai/settings/connectors**
2. Click **Add custom connector**
3. Enter the server URL: `https://your-server:8000/mcp`
4. Under **Advanced settings**, fill in OAuth **Client ID** and **Client Secret**
5. Click **Add**

Your server must be publicly reachable over **HTTPS** (not plain HTTP) from the internet.

#### Claude Desktop (via `mcp-remote` proxy)

Claude Desktop does not support remote HTTP servers natively. Install the proxy first:

```bash
npm install -g mcp-remote
```

Then add to `claude_desktop_config.json`  
(macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rpg-campaign": {
      "command": "npx",
      "args": [
        "mcp-remote@latest",
        "http://your-server:8000/mcp",
        "--header",
        "Authorization:Bearer ${MCP_API_KEY}"
      ],
      "env": {
        "MCP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

#### Claude API (programmatic)

```python
import anthropic

client = anthropic.Anthropic()
response = client.beta.messages.create(
    model="claude-opus-4-7",
    max_tokens=1000,
    messages=[{"role": "user", "content": "List all campaign locations."}],
    mcp_servers=[{
        "type": "url",
        "url": "http://your-server:8000/mcp",
        "name": "rpg-campaign",
        "authorization_token": "your-api-key-here",
    }],
    betas=["mcp-client-2025-11-20"],
)
```

### Security notes

- **TLS**: Wrap the server with a reverse proxy that terminates HTTPS before exposing it publicly. The API key is sent in plain text over HTTP.
- **Rate limiting**: The server allows 60 requests per minute per IP. Adjust `_RateLimiter` in `main.py` if needed.
- **API key length**: The minimum enforced length is 32 characters. Use `secrets.token_hex(32)` (64 hex chars) or longer.

---

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
