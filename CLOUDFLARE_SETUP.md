# Cloudflare Integration Setup Guide

This guide explains how to configure Cloudflare Tunnel and External-DNS on your Kubernetes cluster.

## Overview

Your cluster uses two Cloudflare integrations:

1. **Cloudflare Tunnel** - Provides secure ingress without exposing public IPs
2. **External-DNS** - Automatically manages DNS records in Cloudflare

## Current Status

Both services are deployed but using **placeholder credentials**. They need to be updated with actual Cloudflare credentials to function.

### Quick Status Check

```bash
# SSH to the cluster
ssh rpi1@192.168.8.197

# Check pod status
kubectl get pods -n cloudflare
kubectl get pods -n external-dns

# Check ArgoCD application health
kubectl get applications -n argocd cloudflared external-dns
```

## Setup Steps

### Step 1: Update Cloudflare Tunnel Credentials

1. Get your tunnel credentials from [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
   - Navigate to **Networks** > **Tunnels**
   - Find tunnel: `k8s` (ID: `8fa14fa7-0c0f-4c5f-aa4b-02a53692538d`)
   - Download credentials or copy tunnel token

2. Update the secret on the cluster:

```bash
# SSH to cluster
ssh rpi1@192.168.8.197

# Create credentials file
cat > /tmp/cloudflare-tunnel-creds.json <<'EOF'
{
  "AccountTag": "287d6126ed25707eeca1ee18d263d21b",
  "TunnelSecret": "<YOUR_ACTUAL_TUNNEL_SECRET>",
  "TunnelID": "8fa14fa7-0c0f-4c5f-aa4b-02a53692538d"
}
EOF

# Update the secret
kubectl delete secret cloudflare-tunnel-credentials -n cloudflare
kubectl create secret generic cloudflare-tunnel-credentials \
  --from-file=credentials.json=/tmp/cloudflare-tunnel-creds.json \
  -n cloudflare

# Restart pods
kubectl rollout restart deployment cloudflared-cloudflare-tunnel -n cloudflare

# Clean up
rm /tmp/cloudflare-tunnel-creds.json
```

3. Verify:
```bash
kubectl get pods -n cloudflare
kubectl logs -n cloudflare -l app.kubernetes.io/name=cloudflare-tunnel
```

### Step 2: Create Cloudflare API Token

1. Create an API token in [Cloudflare Dashboard](https://dash.cloudflare.com/)
   - Go to **My Profile** > **API Tokens** > **Create Token**
   - Use **Edit zone DNS** template
   - Permissions:
     - Zone > DNS > Edit
     - Zone > Zone > Read
   - Zone Resources:
     - Include > Specific zone > `holm.chat`
   - Create and **copy the token** (shown only once!)

2. Update the secret on the cluster:

```bash
# SSH to cluster
ssh rpi1@192.168.8.197

# Update the secret
kubectl delete secret cloudflare-api-token -n external-dns
kubectl create secret generic cloudflare-api-token \
  --from-literal=token=<YOUR_CLOUDFLARE_API_TOKEN> \
  -n external-dns

# Restart pod
kubectl rollout restart deployment external-dns -n external-dns
```

3. Verify:
```bash
kubectl get pods -n external-dns
kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns
```

## Verification

After updating both secrets:

1. **Check pod status:**
```bash
kubectl get pods -n cloudflare -n external-dns
```
Expected: All pods in `Running` state with 1/1 READY

2. **Check ArgoCD applications:**
```bash
kubectl get applications -n argocd cloudflared external-dns
```
Expected: Both showing `Synced` and `Healthy`

3. **Check logs for errors:**
```bash
kubectl logs -n cloudflare -l app.kubernetes.io/name=cloudflare-tunnel
kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns
```

4. **Verify tunnel connectivity:**
   - Check [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
   - Navigate to Networks > Tunnels
   - Tunnel should show as "Healthy" with 2 connectors

5. **Verify DNS management:**
   - Check [Cloudflare DNS Dashboard](https://dash.cloudflare.com/)
   - Look for `holm.chat` zone
   - Should see DNS records being managed by external-dns

## What These Services Do

### Cloudflare Tunnel

Routes traffic from Cloudflare's edge to your cluster:

- `uptime.holm.chat` → Uptime Kuma monitoring
- `cmd.holm.chat` → CMD API service
- `holm.chat`, `www.holm.chat`, `dev.holm.chat` → Envoy Gateway

Benefits:
- No public IP exposure needed
- Built-in DDoS protection
- Automatic SSL/TLS termination
- Traffic analytics

### External-DNS

Automatically manages DNS records:
- Creates records for LoadBalancer services
- Creates records for Ingresses
- Creates records for Gateway HTTPRoutes
- Deletes records when resources are removed
- Uses TXT records to track ownership

Benefits:
- No manual DNS management
- DNS stays in sync with cluster
- GitOps-friendly

## Troubleshooting

### Cloudflare Tunnel Issues

**Pods in CrashLoopBackOff:**
- Check credentials are correct
- Verify tunnel exists in Cloudflare dashboard
- Check logs: `kubectl logs -n cloudflare <pod-name>`

**Tunnel shows as disconnected:**
- Verify network connectivity from cluster
- Check Cloudflare service status
- Ensure credentials haven't been rotated

### External-DNS Issues

**"Invalid access token" error:**
- Verify API token hasn't expired
- Check token has correct permissions
- Recreate token if needed

**DNS records not created:**
- Check external-dns logs for errors
- Verify resources have correct annotations/hostnames
- Ensure hostnames match `*.holm.chat` domain filter

## Additional Documentation

- Cloudflare Tunnel: `k8s-manifests/cloudflare/README.md`
- External-DNS: `k8s-manifests/external-dns/README.md`

## Security Notes

- **Never commit secrets to Git** - secrets are managed directly on the cluster
- Rotate API tokens periodically
- Use least-privilege permissions for API tokens
- Consider using Sealed Secrets or External Secrets Operator for production

## Sealed Secrets (Optional)

A sealed-secrets controller has been deployed to the cluster for future use. This allows you to encrypt secrets and store them in Git safely.

To use sealed secrets:

1. Install kubeseal CLI: `brew install kubeseal`
2. Create a regular secret manifest
3. Encrypt it: `kubeseal < secret.yaml > sealedsecret.yaml`
4. Commit the sealed secret to Git
5. ArgoCD will deploy it and sealed-secrets controller will decrypt it

Note: The sealed-secrets controller may have issues on ARM64 architecture. If it doesn't start properly, continue using regular secrets managed directly on the cluster.
