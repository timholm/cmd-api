# External-DNS Configuration

This directory contains configuration for external-dns on the Kubernetes cluster.

## Overview

External-DNS automatically creates and manages DNS records in Cloudflare based on Kubernetes resources (Services, Ingresses, and Gateway HTTPRoutes). It ensures that DNS records stay in sync with your cluster's ingress configuration.

## Current Status

External-DNS is currently using a **placeholder API token** and will not function until updated with an actual Cloudflare API token.

## Required Secrets

### 1. Cloudflare API Token

**Secret Name:** `cloudflare-api-token`
**Namespace:** `external-dns`
**Format:** Simple key-value pair

#### How to Create a Cloudflare API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to **My Profile** > **API Tokens**
3. Click **Create Token**
4. Use the **Edit zone DNS** template
5. Configure permissions:
   - **Zone** > **DNS** > **Edit**
   - **Zone** > **Zone** > **Read**
6. Set Zone Resources:
   - **Include** > **Specific zone** > `holm.chat`
7. Click **Continue to summary** then **Create Token**
8. **IMPORTANT:** Copy the token immediately - it will only be shown once!

#### Update the Secret

**On the cluster (SSH to rpi1@192.168.8.197):**

```bash
# Delete the old secret
kubectl delete secret cloudflare-api-token -n external-dns

# Create the new secret with your actual API token
kubectl create secret generic cloudflare-api-token \
  --from-literal=token=<YOUR_CLOUDFLARE_API_TOKEN> \
  -n external-dns

# Restart the pod to pick up the new secret
kubectl rollout restart deployment external-dns -n external-dns
```

## Configuration

External-DNS is configured with the following settings:

- **Provider:** Cloudflare
- **Domain Filter:** `holm.chat`
- **Sources:** Service, Ingress, Gateway HTTPRoute
- **Policy:** sync (automatically create/delete records)
- **TXT Owner ID:** `k8s-cluster`
- **Cloudflare Proxied:** Enabled (traffic goes through Cloudflare)
- **DNS Records Per Page:** 5000

## How It Works

External-DNS will automatically:

1. Watch for Services with `external-dns.alpha.kubernetes.io/hostname` annotation
2. Watch for Ingress resources
3. Watch for Gateway HTTPRoute resources
4. Create DNS A/CNAME records in Cloudflare for the `holm.chat` zone
5. Create TXT records to track ownership
6. Update records when resources change
7. Delete records when resources are removed

## Example Usage

### Service with LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myapp.holm.chat
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: my-app
```

### HTTPRoute (Gateway API)

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: my-route
  namespace: default
spec:
  hostnames:
    - myapp.holm.chat
  parentRefs:
    - name: main-gateway
  rules:
    - backendRefs:
        - name: my-service
          port: 80
```

External-DNS will automatically create a DNS record for `myapp.holm.chat` pointing to the LoadBalancer IP or gateway.

## Verification

After updating the API token, verify external-dns is working:

```bash
# Check pod status
kubectl get pods -n external-dns

# Check logs
kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns

# Verify DNS records are being created
# (Check Cloudflare dashboard DNS section for holm.chat)
```

Expected output:
- Pod in `Running` state with 1/1 READY
- Logs showing successful API calls to Cloudflare
- DNS records appearing in Cloudflare dashboard

## Troubleshooting

### "Invalid access token" error
- Verify the API token is correct and hasn't expired
- Check token permissions include DNS Edit for holm.chat zone
- Recreate the secret if needed

### DNS records not being created
- Check external-dns logs: `kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns`
- Verify the service/ingress/route has proper annotations or hostnames
- Ensure hostnames match the domain filter (*.holm.chat)
- Check that the source resource types are enabled (service, ingress, gateway-httproute)

### DNS records not being deleted
- External-DNS uses TXT records to track ownership
- Only records with matching TXT owner ID will be managed
- Check TXT records in Cloudflare to verify ownership

### Rate limiting
- Cloudflare free tier has rate limits
- External-DNS respects these limits automatically
- Consider increasing the interval if hitting limits frequently

## Advanced Configuration

The external-dns configuration is managed via ArgoCD application at:
`argocd-apps/external-dns.yaml`

Key settings that can be adjusted:
- `interval`: How often to sync (default: 1m)
- `policy`: sync (manage records) or upsert-only (never delete)
- `txtPrefix`: Prefix for TXT records
- `cloudflare-proxied`: Enable/disable Cloudflare proxy
