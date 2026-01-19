# cmd-api

A lightweight HTTP API server for executing shell commands and Claude Code prompts.

## Features

- **Shell command execution** via `/run` endpoint
- **Claude Code integration** via `/claude` endpoint
- CORS enabled for cross-origin requests
- Simple JSON request/response format

## Installation

```bash
git clone https://github.com/timholm/cmd-api.git
cd cmd-api
```

No dependencies required - uses Python standard library only.

## Usage

Start the server:

```bash
python3 server.py
```

The server runs on port 3000 by default.

## API Endpoints

### `GET /`

Health check endpoint.

**Response:**
```
Command API running.
POST /run - shell commands
POST /claude - Claude Code prompts
```

### `POST /run`

Execute a shell command.

**Request:**
```json
{
  "cmd": "echo hello"
}
```

**Response:**
```json
{
  "stdout": "hello\n",
  "stderr": "",
  "code": 0
}
```

### `POST /claude`

Send a prompt to Claude Code.

**Request:**
```json
{
  "prompt": "What is 2 + 2?"
}
```

**Response:**
```json
{
  "response": "4",
  "stderr": "",
  "code": 0
}
```

## Configuration

Edit `server.py` to change:

- `PORT` - Server port (default: 3000)
- Claude Code path in the `/claude` handler

## Security Warning

This server executes arbitrary shell commands. Only run it in trusted environments and never expose it to the public internet without proper authentication.

## License

MIT
