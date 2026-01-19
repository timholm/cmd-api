# cmd-api

Lightweight HTTP API for shell commands and SSH remote execution.

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/run` | POST | Execute shell commands |
| `/ssh` | POST | Execute commands on remote hosts via SSH |

## Usage

### Run local commands
```bash
curl -X POST https://cmd.holm.chat/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "kubectl get pods -A"}'
```

### SSH remote commands
```bash
curl -X POST https://cmd.holm.chat/ssh \
  -H "Content-Type: application/json" \
  -d '{
    "host": "192.168.1.100",
    "username": "user",
    "password": "pass",
    "command": "ls -la"
  }'
```

## Deployment

### Docker
```bash
docker build -t cmd-api .
docker run -p 3000:3000 cmd-api
```

### Kubernetes with Helm
```bash
helm install cmd-api ./chart -n default
```

### ArgoCD
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
```

## Security Warning

This server executes arbitrary shell commands and SSH connections. Never expose to the public internet without authentication.

## License

MIT
