# Deploy AI Agent to Local Kubernetes - Step by Step

> **Goal:** Run your complete AI agent stack on local Kubernetes with auto-scaling, monitoring, and logging. Takes ~10-15 minutes.

---

## 📋 Prerequisites Check

### Step 1: Verify Docker Desktop is Running

**Windows:**
```powershell
docker --version
# Output: Docker version 20.10.x or higher ✅

docker ps
# Should show no errors ✅
```

### Step 2: Check kubectl is Available

```powershell
kubectl version --client
# Output: Client Version: v1.27.x or higher ✅

# If not found, download:
# https://kubernetes.io/docs/tasks/tools/install-kubectl-on-windows/
```

---

## 🎯 Enable Kubernetes in Docker Desktop

### Step 3: Enable Kubernetes Cluster

**Windows with Docker Desktop:**

1. **Open Docker Desktop Settings**
   - Click Docker icon in system tray
   - Select "Settings" (or "Preferences")

2. **Enable Kubernetes**
   - Navigate to: Settings → Kubernetes
   - Check box: "Enable Kubernetes"
   - Click "Apply & Restart"
   - ⏳ Wait 5-10 minutes (downloading K8s components)

3. **Verify Kubernetes is Running**
   ```powershell
   kubectl cluster-info
   # Output: Kubernetes control plane is running...
   
   kubectl get nodes
   # Output: 
   # NAME             STATUS   ROLES           AGE
   # docker-desktop   Ready    control-plane   2m
   ```

✅ **Kubernetes is now running locally!**

---

## 🚀 Deploy Your AI Agent

### Step 4: Create Kubernetes Namespace

A namespace isolates your app from other workloads.

```powershell
kubectl create namespace ai-agent
# Output: namespace/ai-agent created

# Verify
kubectl get namespaces
# Should show: ai-agent
```

---

### Step 5: Build Docker Image

```powershell
# Navigate to project directory
cd c:\Users\eml2s\Session\ai-agent-deployment

# Build image for Kubernetes
docker build -t ai-agent:latest .
# Output: Successfully tagged ai-agent:latest

# Verify image exists
docker images | grep ai-agent
# Should show: ai-agent    latest    ...
```

✅ **Docker image ready for Kubernetes**

---

### Step 6: Create Kubernetes ConfigMap (Configuration)

ConfigMap stores configuration separate from code.

```powershell
# Create ConfigMap with app configuration
kubectl create configmap ai-agent-config `
  -n ai-agent `
  --from-literal=PORT=8000 `
  --from-literal=LLM_PROVIDER=mock `
  --from-literal=LOG_LEVEL=INFO `
  --from-literal=ENVIRONMENT=development

# Verify
kubectl get configmaps -n ai-agent
# Output: ai-agent-config
```

---

### Step 7: Apply Kubernetes Manifests

These files define how your app should run.

```powershell
# Apply in order (dependencies)

# 1. Namespace (already done, but safe to apply again)
kubectl apply -f kubernetes/namespace.yaml
# Output: namespace/ai-agent configured

# 2. ConfigMap (already created, update from file)
kubectl apply -f kubernetes/configmap.yaml
# Output: configmap/ai-agent-config configured

# 3. ServiceAccount (RBAC configuration)
kubectl apply -f kubernetes/rbac.yaml
# Output: serviceaccount/ai-agent created / clusterrole.rbac.authorization.k8s.io/ai-agent created / ...

# 4. Main Deployment (the app itself)
kubectl apply -f kubernetes/deployment.yaml
# Output: deployment.apps/ai-agent created

# 5. Service (networking, load balancing)
kubectl apply -f kubernetes/service.yaml
# Output: service/ai-agent created

# 6. HPA (Horizontal Pod Autoscaler)
kubectl apply -f kubernetes/hpa.yaml
# Output: horizontalpodautoscaler.autoscaling/ai-agent created

# 7. PDB (Pod Disruption Budget - high availability)
kubectl apply -f kubernetes/pdb.yaml
# Output: poddisruptionbudget.policy/ai-agent-pdb created
```

✅ **All Kubernetes manifests applied!**

---

### Step 8: Verify Deployment is Running

```powershell
# Check namespace
kubectl get namespace ai-agent
# Output: ai-agent    Active    1m

# Check pods (containers)
kubectl get pods -n ai-agent
# Output (wait for READY=1/1, STATUS=Running):
# NAME                        READY   STATUS    RESTARTS   AGE
# ai-agent-5d8f7c4b7c-abc123  1/1     Running   0          30s
# ai-agent-5d8f7c4b7c-def456  1/1     Running   0          30s
# ai-agent-5d8f7c4b7c-ghi789  1/1     Running   0          25s

# If STATUS=Pending or CrashLoopBackOff, wait 30 seconds and retry
# Check logs if stuck:
kubectl logs deployment/ai-agent -n ai-agent
```

---

### Step 9: Verify Service (Load Balancer)

```powershell
kubectl get svc -n ai-agent
# Output:
# NAME       TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)
# ai-agent   LoadBalancer   10.96.0.123    localhost     80:30234/TCP

# Check endpoints (actual pod IPs)
kubectl get endpoints ai-agent -n ai-agent
# Output shows the 3 running pods are registered
```

---

### Step 10: Port Forward to Access Locally

For local development, forward traffic to the service:

```powershell
# Open new PowerShell/Terminal window #2
kubectl port-forward -n ai-agent svc/ai-agent 8000:80

# Output:
# Forwarding from 127.0.0.1:8000 -> 8000
# Forwarding from [::1]:8000 -> 8000
# 
# ✅ Keep this terminal open!
```

---

## 🧪 Test Your Deployment

### Step 11: Test the API (Use Terminal #1)

```powershell
# Health check
curl http://localhost:8000/health
# Output: {"status":"healthy"}

# Send a chat message
$body = '{"message":"hello from k8s"}'
Invoke-WebRequest -Uri http://localhost:8000/chat -Method Post `
  -Body $body `
  -Headers @{"Content-Type"="application/json"} `
  -UseBasicParsing | Select-Object StatusCode, Content

# Output:
# StatusCode : 200
# Content    : {"response":"Mock AI response...","tokens_used":100}

✅ Your app is running on Kubernetes!
```

---

### Step 12: Monitor Pods

```powershell
# Watch pods in real-time
kubectl get pods -n ai-agent -w

# You'll see:
# NAME                        READY   STATUS    RESTARTS   AGE
# ai-agent-5d8f7c4b7c-abc123  1/1     Running   0          2m
# ai-agent-5d8f7c4b7c-def456  1/1     Running   0          2m
# ai-agent-5d8f7c4b7c-ghi789  1/1     Running   0          2m

# (Press Ctrl+C to exit watch mode)
```

---

### Step 13: Check HPA (Auto-Scaling) Status

```powershell
kubectl get hpa -n ai-agent
# Output:
# NAME       REFERENCE             TARGETS           MINPODS   MAXPODS   REPLICAS   AGE
# ai-agent   Deployment/ai-agent   12%/70%, 15%/80%  3         20        3          2m

# Detailed HPA info
kubectl describe hpa ai-agent -n ai-agent
# Shows scaling history and current metrics
```

---

### Step 14: Check Logs

```powershell
# Logs from all pods (last 50 lines)
kubectl logs -f deployment/ai-agent -n ai-agent --tail=50

# Output shows: Application startup, health checks, chat messages

# Logs from specific pod
kubectl logs -f pod/ai-agent-5d8f7c4b7c-abc123 -n ai-agent
```

---

## 📊 Test Auto-Scaling (Optional but Educational!)

### Step 15: Generate Load to Trigger Scaling

```powershell
# Open NEW Terminal #3 - Start load generator
kubectl create deployment loadgen -n ai-agent `
  --image=alpine:latest `
  --replicas=1 `
  -- sh -c "apk add curl && while true; do for i in {1..100}; do curl -X POST http://ai-agent/8000/chat -H 'Content-Type: application/json' -d '{\"message\":\"load-test\"}' & done; wait; sleep 1; done"

# Output: deployment.apps/loadgen created
```

### Step 16: Watch HPA Scale Up

```powershell
# Terminal #1: Watch HPA in real-time
kubectl get hpa -n ai-agent -w

# You'll see REPLICAS column increase:
# REPLICAS: 3 → 5 → 8 → 10 (scaling up as CPU rises)
# 
# Then after load stops:
# REPLICAS: 10 → 8 → 5 → 3 (scaling down)

# (Press Ctrl+C to exit)
```

### Step 17: Stop Load Generator

```powershell
# Delete the load generator
kubectl delete deployment loadgen -n ai-agent
# Output: deployment.apps "loadgen" deleted

# Wait 5 minutes, then check HPA scales back to 3
kubectl get hpa -n ai-agent
# REPLICAS will gradually return to: 3
```

---

## 🔍 Useful Monitoring Commands

### Check Resource Usage

```powershell
# Pod resource usage (CPU, memory)
kubectl top pods -n ai-agent
# Output:
# NAME                        CPU(m)   MEMORY(Mi)
# ai-agent-5d8f7c4b7c-abc123  50m      120Mi
# ai-agent-5d8f7c4b7c-def456  45m      118Mi
# ai-agent-5d8f7c4b7c-ghi789  48m      122Mi

# Node resource usage
kubectl top nodes
# OUTPUT:
# NAME             CPU(m)   CPU%     MEMORY(Mi)   MEMORY%
# docker-desktop   200m     10%      1200Mi       30%
```

### Get Detailed Pod Info

```powershell
kubectl describe pod ai-agent-5d8f7c4b7c-abc123 -n ai-agent
# Shows: IP address, events, volumes, health status

# Including events like:
# Type    Reason     Age    From               Message
# ----    ------     ----   ----               -------
# Normal  Scheduled  2m10s  default-scheduler  Successfully assigned
# Normal  Pulled     2m8s   kubelet            Container image "ai-agent:latest" already present
# Normal  Created    2m8s   kubelet            Created container ai-agent
# Normal  Started    2m8s   kubelet            Started container ai-agent
```

### List All Resources

```powershell
# Everything in ai-agent namespace
kubectl get all -n ai-agent

# Output shows:
# Deployments, Pods, Services, StatefulSets, HPAs, etc.
```

---

## 🛑 Cleanup & Teardown

### Stop Port Forward

In Terminal #2 where port-forward is running:
```powershell
# Press Ctrl+C to stop
# Output: ^C

# Close terminal window
```

---

### Delete Deployment (Keep Data)

```powershell
# Delete only the deployment (data stays)
kubectl delete deployment ai-agent -n ai-agent
# Output: deployment.apps "ai-agent" deleted

# Pods will terminate gracefully (30-second grace period)
kubectl get pods -n ai-agent
# Output: No resources found in ai-agent namespace.
```

---

### Delete Entire Namespace (DELETES EVERYTHING)

```powershell
# ⚠️ WARNING: This deletes everything in ai-agent namespace!
kubectl delete namespace ai-agent
# Output: namespace "ai-agent" deleted

# Verify it's gone
kubectl get namespaces
# ai-agent should NOT be in list

# Disable Kubernetes in Docker Desktop (optional)
# Settings → Kubernetes → Uncheck "Enable Kubernetes" → Apply
```

---

## 🐛 Troubleshooting

### Problem: Pods stuck in Pending

```powershell
kubectl describe pod <pod-name> -n ai-agent
# Look for "Events" section at bottom

# Common causes:
# - Insufficient CPU/memory: Scale down image memory in deployment.yaml
# - Image not found: Rebuild docker image: docker build -t ai-agent:latest .
# - Volume issues: Not applicable for local K8s
```

### Problem: CrashLoopBackOff Status

```powershell
# Check logs for errors
kubectl logs pod/<pod-name> -n ai-agent

# Common causes:
# - Application crash: Check SPLUNK_HEC_URL is set
# - Port conflict: Change port in deployment.yaml
# - Missing environment variables: Update configmap.yaml
```

### Problem: API Not Responding

```powershell
# Verify service endpoint
kubectl get endpoints ai-agent -n ai-agent

# Verify port-forward is still running
# (Check Terminal #2)

# Try direct pod access (bypass service)
kubectl port-forward pod/ai-agent-<id> 8001:8000 -n ai-agent
curl http://localhost:8001/health
```

### Problem: Cannot Connect to Kubernetes

```powershell
# Verify Docker Desktop Kubernetes is enabled
kubectl cluster-info
# If fails: Go to Docker Desktop Settings → Enable Kubernetes

# Restart Kubernetes
kubectl delete node docker-desktop
# Then restart Docker Desktop
```

---

## ✅ Verification Checklist

- [ ] Docker Desktop running
- [ ] Kubernetes enabled in Docker Desktop
- [ ] `kubectl cluster-info` shows control plane
- [ ] `kubectl get nodes` shows docker-desktop
- [ ] Namespace created: `kubectl get namespaces | grep ai-agent`
- [ ] Deployment running: `kubectl get deployment -n ai-agent`
- [ ] 3 pods running: `kubectl get pods -n ai-agent`
- [ ] Service created: `kubectl get svc -n ai-agent`
- [ ] Port-forward active: `kubectl port-forward svc/ai-agent 8000:80`
- [ ] API responding: `curl http://localhost:8000/health`
- [ ] HPA configured: `kubectl get hpa -n ai-agent`

---

## 📚 Next Steps

### 1. **Integrate with Observability Stack** (Optional)
   ```powershell
   # Deploy Prometheus + Grafana in same K8s cluster
   kubectl apply -f monitoring/prometheus-deployment.yaml
   kubectl apply -f monitoring/grafana-deployment.yaml
   
   # Port forward to Grafana
   kubectl port-forward -n ai-agent svc/grafana 3000:3000
   # Then open: http://localhost:3000
   ```

### 2. **Deploy to AWS EKS** (When Ready)
   See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
   ```bash
   cd aws
   bash create-eks-cluster.sh
   kubectl apply -f ../kubernetes/
   ```

### 3. **Add CI/CD Pipeline**
   Push changes → GitHub Actions → Auto-deploy to K8s

---

## 💡 Key Learnings

✅ **Kubernetes orchestration principles:**
- Declarative configuration (manifests define desired state)
- Automatic pod scheduling across nodes
- Self-healing (restart failed pods)
- Auto-scaling based on metrics

✅ **Why it's different from Docker Compose:**
- Multi-host ready (scales to 100s of nodes)
- Automatic replica management
- Built-in health checks
- Service discovery
- Rolling updates with zero downtime

---

## 🎓 Educational Value

By completing this, you've learned:
1. **Kubernetes architecture** (control plane, nodes, pods)
2. **Declarative infrastructure** (manifests as code)
3. **Container orchestration** (how K8s manages containers)
4. **Auto-scaling** (HPA responding to metrics)
5. **Service networking** (load balancing, DNS)
6. **Production-grade deployment** (real-world patterns)

This is what DevOps engineers do daily! 🚀

---

**Need Help?**
- Check logs: `kubectl logs -f deployment/ai-agent -n ai-agent`
- Describe resource: `kubectl describe <resource-type>/<name> -n ai-agent`
- Ask in GitHub Issues
- Review [Kubernetes Official Docs](https://kubernetes.io/docs/)

**Good Luck!** 🎉
