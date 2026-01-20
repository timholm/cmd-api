# CMD API

Lightweight HTTP API for shell commands, SSH remote execution, and Claude Code prompts.

## Features

- **Local shell execution** - Run commands on the API server
- **SSH remote execution** - Execute commands on remote hosts via SSH
- **Claude Code integration** - Send prompts to Claude CLI
- **Multi-arch support** - Runs on amd64 and arm64
- **ArgoCD ready** - Helm chart with auto-sync

## Quick Start

### ArgoCD Deployment (Recommended)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: cmd-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/timholm/cmd-api.git
    targetRevision: HEAD
    path: chart
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

### Manual Helm Install

```bash
helm install cmd-api ./chart -n default
```

## Configuration

See `chart/values.yaml` for all options:

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image | `ghcr.io/timholm/cmd-api` |
| `image.tag` | Image tag | `latest` |
| `service.port` | Service port | `80` |
| `httpRoute.enabled` | Enable Gateway API HTTPRoute | `true` |
| `httpRoute.hostname` | Ingress hostname | `cmd.holm.chat` |
| `resources.requests.memory` | Memory request | `64Mi` |
| `resources.limits.memory` | Memory limit | `128Mi` |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check / info |
| `/run` | POST | Execute local shell command |
| `/ssh` | POST | Execute remote SSH command |
| `/claude` | POST | Send prompt to Claude Code |

### Examples

**Health check:**
```bash
curl https://cmd.holm.chat/
```

**Local command:**
```bash
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "ls -la"}'
```

**SSH command:**
```bash
curl -X POST https://cmd.holm.chat/ssh \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.1.100",
    "username": "user",
    "password": "pass",
    "command": "whoami"
  }'
```

**Claude prompt:**
```bash
curl -X POST https://cmd.holm.chat/claude \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is 2+2?"}'
```

## CI/CD Pipeline

Push to `main` branch triggers:
1. **GitHub Actions** builds multi-arch Docker image (amd64 + arm64)
2. **Image pushed** to `ghcr.io/timholm/cmd-api:latest`
3. **ArgoCD** detects image change and syncs deployment

## Development

```bash
# Install dependencies
pip install paramiko

# Run locally
python server.py

# Test
curl http://localhost:3000/
```

## Architecture

```
Client → cmd.holm.chat → Envoy Gateway → cmd-api Service → Pod
                                                            ↓
                                              ┌─────────────┴─────────────┐
                                              │                           │
                                           /run                        /ssh
                                        (local shell)            (paramiko SSH)
```

## Security Warning

This server executes arbitrary shell commands and SSH connections. Never expose to the public internet without proper authentication.

## License

MIT
