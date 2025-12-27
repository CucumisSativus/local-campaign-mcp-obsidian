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

### Running the Server (Local Mode)

The server can run in two modes: local stdio mode or HTTP mode with authentication.

For **local usage** with stdio transport (e.g., Claude Desktop):

```bash
LOCATIONS_PATH=/path/to/your/locations CHARACTERS_PATH=/path/to/your/characters SESSIONS_PATH=/path/to/your/sessions python main.py
```

### Running the Server (Internet Mode with Authentication)

For **internet-facing deployment** with HTTP/SSE transport and API key authentication:

```bash
# First, generate a secure API key
export API_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Then run the HTTP server
LOCATIONS_PATH=/path/to/your/locations \
CHARACTERS_PATH=/path/to/your/characters \
SESSIONS_PATH=/path/to/your/sessions \
API_KEY=$API_KEY \
HOST=0.0.0.0 \
PORT=8000 \
python main_http.py
```

Or with uv:

```bash
export API_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')
uv run main_http.py
```

**Environment Variables for HTTP Mode:**
- `API_KEY` (required): API key for authentication
- `HOST` (optional): Host to bind to (default: `0.0.0.0`)
- `PORT` (optional): Port to bind to (default: `8000`)
- `LOCATIONS_PATH` (required): Path to locations directory
- `CHARACTERS_PATH` (required): Path to characters directory
- `SESSIONS_PATH` (required): Path to sessions directory

**Authentication:**
All requests (except `/health`) must include the API key in the `Authorization` header:

```bash
# Using curl
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/sse

# Or without Bearer prefix
curl -H "Authorization: YOUR_API_KEY" http://localhost:8000/sse
```

**Endpoints:**
- `GET /health` - Health check endpoint (no authentication required)
- `GET /sse` - SSE endpoint for MCP communication (authentication required)
- `POST /messages` - Message endpoint for MCP communication (authentication required)

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

### Connecting to HTTP Server with Authentication

If you're running the server in HTTP mode with authentication, MCP clients can connect using the SSE endpoint:

**Server URL:** `http://your-server:8000/sse`

**Authentication:** Include the API key in the `Authorization` header

When deploying to the internet, make sure to:
1. Use HTTPS (via reverse proxy like nginx or Caddy)
2. Keep your API key secure and private
3. Consider using a firewall to restrict access
4. Monitor server logs for unauthorized access attempts

### Claude Desktop Configuration (Local Mode)

Add to your `claude_desktop_config.json` for local stdio mode:

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

## Security Considerations

When exposing the server to the internet:

### API Key Security
- **Generate strong API keys**: Use `python -c 'import secrets; print(secrets.token_urlsafe(32))'`
- **Keep keys secret**: Never commit API keys to version control
- **Rotate regularly**: Change API keys periodically
- **Use environment variables**: Store keys in `.env` files (see `.env.example`)

### Network Security
- **Use HTTPS**: Always use TLS/SSL in production (via reverse proxy)
- **Firewall rules**: Restrict access to known IP addresses if possible
- **Rate limiting**: Consider adding rate limiting to prevent abuse
- **Monitor logs**: Watch for unusual access patterns

### Deployment Best Practices
1. Run behind a reverse proxy (nginx, Caddy, Traefik)
2. Enable HTTPS with valid SSL certificates (Let's Encrypt)
3. Use a process manager (systemd, supervisor, pm2)
4. Set up proper logging and monitoring
5. Keep dependencies updated

### Example Reverse Proxy Configuration (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }
}
```

## Development

### Running Tests

```bash
uv run pytest
```

### Type Checking

```bash
uv run mypy main.py main_http.py
```

### Linting

```bash
uv run ruff check .
```

## License

MIT
