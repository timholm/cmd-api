# cmd-api

A lightweight HTTP API server for executing shell commands, SSH remote commands, and Claude Code prompts. Designed for Kubernetes cluster management and remote server troubleshooting.

## Features

- **Shell command execution** via `/run` endpoint
- **SSH remote command execution** via `/ssh` endpoint (with paramiko)
- **Claude Code integration** via `/claude` endpoint
- **Kubernetes access** with kubectl pre-installed
- CORS enabled for cross-origin requests
- Simple JSON request/response format
- Helm chart for Kubernetes deployment
- ArgoCD auto-sync ready

## Quick Start

### Local Development

```bash
git clone https://github.com/timholm/cmd-api.git
cd cmd-api
pip install paramiko
python3 server.py
```

The server runs on port 3000 by default.

### Docker

```bash
docker build -t cmd-api .
docker run -p 3000:3000 cmd-api
```

### Kubernetes with Helm

```bash
helm install cmd-api ./chart
```

## API Endpoints

### `GET /`

Health check endpoint.

**Response:**
```
Command API running.
POST /run - shell commands
POST /ssh - SSH remote commands
POST /claude - Claude Code prompts
```

### `POST /run`

Execute a shell command on the container.

**Request:**
```json
{
  "cmd": "kubectl get pods -A"
}
```

**Response:**
```json
{
  "stdout": "NAMESPACE   NAME   READY   STATUS...",
  "stderr": "",
  "code": 0
}
```

### `POST /ssh`

Execute a command on a remote server via SSH.

**Request:**
```json
{
  "host": "192.168.8.230",
  "username": "tim",
  "password": "yourpassword",
  "command": "docker ps -a",
  "port": 22
}
```

**Response:**
```json
{
  "stdout": "CONTAINER ID   IMAGE   ...",
  "stderr": "",
  "code": 0
}
```

### `POST /claude`

Send a prompt to Claude Code CLI.

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

## Kubernetes Deployment

### Helm Chart Structure

```
chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── rbac.yaml
```

### Deploy with Helm

```bash
# Install
helm install cmd-api ./chart -n default

# Upgrade
helm upgrade cmd-api ./chart -n default

# Uninstall
helm uninstall cmd-api -n default
```

### ArgoCD Application

The repo is configured for ArgoCD auto-deployment:

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

## How-To Guides

### Discovering Services on Remote Servers

Use the SSH endpoint to discover what's running on remote servers:

```bash
# List running services
curl -X POST https://cmd.holm.chat/run -H "Content-Type: application/json" \
  -d '{"cmd": "python3 -c \"
import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect('192.168.8.230', username='tim', password='pass')
stdin, stdout, stderr = c.exec_command('systemctl list-units --type=service --state=running')
print(stdout.read().decode())
c.close()
\""}'
```

### Listing Kubernetes Resources

```bash
# Get all pods
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kubectl get pods -A"}'

# Get all deployments
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kubectl get deployments -A"}'

# Get ArgoCD applications
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kubectl get applications -n argocd"}'
```

### Installing Packages at Runtime

For packages not in the base image, install them temporarily:

```bash
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "pip install --quiet somepackage && python3 -c \"import somepackage; ...\""}'
```

Note: Runtime installations are lost on pod restart. Add required packages to the Dockerfile for persistence.

## Troubleshooting

### SSH Connection Issues

**Authentication failed:**
- Verify username/password are correct
- Check if username is case-sensitive (e.g., `tim` vs `Tim`)
- Ensure SSH is enabled on the target server

**Connection timeout:**
- Verify the server IP is reachable from the pod
- Check firewall rules on the target server
- Ensure port 22 is open

### API Returns 502 Errors

This usually indicates the pod is restarting or crashed:

```bash
# Check pod status
kubectl get pods -l app=cmd-api

# Check pod logs
kubectl logs -l app=cmd-api --tail=50

# Describe pod for events
kubectl describe pod -l app=cmd-api
```

### Command Timeout

Default timeout is 30 seconds. For long-running commands:
- Break into smaller commands
- Use background execution with `&` and check later
- Increase timeout in server.py

### TLS Certificate Errors

If seeing `CERTIFICATE_VERIFY_FAILED`:
- The error is intermittent with some proxy configurations
- Retry the request
- Check if the endpoint is reachable

## External Services (lenovo-services)

The `lenovo-services/` directory contains Helm charts for exposing services running on external bare-metal servers to the Kubernetes cluster.

### Discovered Services on 192.168.8.230 (lenovo)

| Service | Port | Description |
|---------|------|-------------|
| **Ollama** | 11434 | AI inference with 14+ models |
| **BookForge** | 8080 | Flask book generation app with TTS |
| **PostgreSQL** | 5432 | Database (localhost only) |

### Ollama Models Available

- llama3.1:8b, llama3.2:3b
- qwen2.5-coder:3b/7b/14b
- qwen2.5:3b-instruct, 7b-instruct
- mistral:7b, mistral-nemo
- deepseek-r1:7b
- gemma3, llava, minicpm-v

### Deploy External Service Access

```bash
helm install lenovo-services ./lenovo-services -n default
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3000 | Server listen port |
| OLLAMA_URL | http://localhost:11434 | Ollama API URL |

### Helm Values

See `chart/values.yaml` for configurable options:

```yaml
replicaCount: 1
image:
  repository: ghcr.io/timholm/cmd-api
  tag: latest
  pullPolicy: Always
service:
  type: ClusterIP
  port: 80
  targetPort: 3000
```

## CI/CD

GitHub Actions workflow builds and pushes images on:
- Push to `main` branch
- Push to `claude/*` branches

Images are pushed to:
- `ghcr.io/timholm/cmd-api:latest`
- `ghcr.io/timholm/cmd-api:<commit-sha>`

## Security Warning

This server executes arbitrary shell commands and SSH connections.
- Never expose to the public internet without authentication
- Use network policies to restrict access
- Consider adding API key authentication for production

## License

MIT
