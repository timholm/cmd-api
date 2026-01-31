# Cloudflare Tunnel Configuration

This directory contains configuration for Cloudflare Tunnel on the Kubernetes cluster.

## Overview

Cloudflare Tunnel is deployed via ArgoCD and provides secure ingress to the cluster without exposing public IP addresses. The tunnel connects to Cloudflare's edge network and routes traffic to internal services.

## Current Status

The Cloudflare tunnel pods are currently using **placeholder credentials** and will not function until updated with actual credentials.

## Required Secrets

### 1. Cloudflare Tunnel Credentials

**Secret Name:** `cloudflare-tunnel-credentials`
**Namespace:** `cloudflare`
**Format:** JSON file containing tunnel credentials

#### How to Get Cloudflare Tunnel Credentials

1. Log in to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. Navigate to **Networks** > **Tunnels**
3. Find your tunnel (Name: `k8s`, ID: `8fa14fa7-0c0f-4c5f-aa4b-02a53692538d`)
4. Download the tunnel credentials JSON file or copy the tunnel token

The credentials file should have this format:
```json
{
  "AccountTag": "287d6126ed25707eeca1ee18d263d21b",
  "TunnelSecret": "<base64-encoded-secret>",
  "TunnelID": "8fa14fa7-0c0f-4c5f-aa4b-02a53692538d"
}
```

#### Update the Secret

**On the cluster (SSH to rpi1@192.168.8.197):**

```bash
# Create the credentials JSON file
cat > /tmp/cloudflare-tunnel-creds.json <<EOF
{
  "AccountTag": "287d6126ed25707eeca1ee18d263d21b",
  "TunnelSecret": "<YOUR_ACTUAL_TUNNEL_SECRET>",
  "TunnelID": "8fa14fa7-0c0f-4c5f-aa4b-02a53692538d"
}
EOF

# Delete the old secret
kubectl delete secret cloudflare-tunnel-credentials -n cloudflare

# Create the new secret
kubectl create secret generic cloudflare-tunnel-credentials \
  --from-file=credentials.json=/tmp/cloudflare-tunnel-creds.json \
  -n cloudflare

# Clean up
rm /tmp/cloudflare-tunnel-creds.json

# Restart the pods to pick up the new secret
kubectl rollout restart deployment cloudflared-cloudflare-tunnel -n cloudflare
```

## Tunnel Configuration

The tunnel is configured to route the following domains to internal services:

- `uptime.holm.chat` → `uptime-kuma.monitoring.svc.cluster.local:3001`
- `cmd.holm.chat` → `cmd-api.default.svc.cluster.local:80`
- `holm.chat` → Envoy Gateway
- `www.holm.chat` → Envoy Gateway
- `dev.holm.chat` → Envoy Gateway

## Verification

After updating the credentials, verify the pods are running:

```bash
kubectl get pods -n cloudflare
kubectl logs -n cloudflare -l app.kubernetes.io/name=cloudflare-tunnel
```

Expected output:
- 2 pods in `Running` state with 1/1 READY
- Logs showing successful connection to Cloudflare edge

## Troubleshooting

### Pods stuck in CrashLoopBackOff
- Verify the tunnel credentials are correct
- Check logs: `kubectl logs -n cloudflare <pod-name>`
- Ensure the tunnel exists in Cloudflare dashboard

### "Invalid access token" error
- This error is from external-dns, not cloudflared
- See external-dns documentation for API token setup

### Tunnel not routing traffic
- Verify DNS records in Cloudflare point to the tunnel
- Check tunnel configuration in Cloudflare Zero Trust dashboard
- Ensure target services are running and accessible
