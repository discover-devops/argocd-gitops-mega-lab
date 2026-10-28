# Lab 1 — GitOps Foundations

**Covers:** EKS + Argo CD setup · first Application · Git → Argo CD → Kubernetes
**Time:** ~90 minutes (20 of that is EKS creation)
**Outcome:** TaskFlow (frontend + API + Postgres) running on EKS, deployed by Argo CD from *your* Git repo — and a Git commit that changes the running app.

```text
 You ──git push──▶ GitHub (your fork) ◀──watches── Argo CD ──applies──▶ EKS
                                                                       │
                                               taskflow-frontend ─▶ taskflow-api ─▶ taskflow-postgres
```

---

## Part 0 — Prerequisites (check before class)

| Tool | Check |
|---|---|
| AWS CLI v2, configured | `aws sts get-caller-identity` |
| eksctl | `eksctl version` |
| kubectl | `kubectl version --client` |
| git | `git --version` |
| GitHub account | you can fork a repo |

Set your Git identity once:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

---

## Part 1 — Fork and clone the lab repo

1. Open **https://github.com/discover-devops/argocd-gitops-mega-lab** and click **Fork**.
2. Clone **your fork**:

```bash
export GH_USER=<your-github-username>
git clone https://github.com/$GH_USER/argocd-gitops-mega-lab.git
cd argocd-gitops-mega-lab
```

> Why a fork? Argo CD watches a Git repo. To see GitOps work, you must be able to push to that repo.

---

## Part 2 — Create the EKS cluster

```bash
eksctl create cluster -f cluster/eks-cluster.yaml
```

This takes 15–20 minutes. It creates a cluster `gitops-lab` in `ap-south-1` with 2 × t3.large nodes and the EBS CSI driver (Postgres needs a disk).

Verify:

```bash
kubectl get nodes
kubectl get pods -n kube-system | grep ebs-csi
```

✅ **Checkpoint:** 2 nodes `Ready`, ebs-csi pods `Running`.

Create the default gp3 StorageClass:

```bash
kubectl apply -f cluster/storageclass-gp3.yaml
kubectl get storageclass
```

✅ `gp3 (default)` appears.

---

## Part 3 — Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

> `--server-side` avoids the "annotations too long" error some Argo CD CRDs hit with plain `kubectl apply`.

Wait for everything to start:

```bash
kubectl wait --for=condition=Available deployment --all -n argocd --timeout=300s
kubectl get pods -n argocd
```

✅ **Checkpoint:** you see and understand these components:

| Pod | Job |
|---|---|
| `argocd-server` | UI + API you log in to |
| `argocd-repo-server` | Clones Git and renders manifests |
| `argocd-application-controller` | Compares Git vs cluster, applies changes |
| `argocd-applicationset-controller` | Generates Applications (Lab 6) |
| `argocd-redis` | Cache |
| `argocd-dex-server` | SSO (not used in this lab) |
| `argocd-notifications-controller` | Alerts (not used in this lab) |

---

## Part 4 — Log in to the Argo CD UI

Open a **second terminal** and keep this running:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Get the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Open **https://localhost:8080** (accept the certificate warning).
Username: `admin` · Password: the value above.

✅ **Checkpoint:** you see an empty Applications page.

---

## Part 5 — Create your first Application (UI)

Click **+ NEW APP** and fill in:

| Field | Value |
|---|---|
| Application Name | `taskflow` |
| Project | `default` |
| Sync Policy | **Manual** |
| Repository URL | `https://github.com/<your-github-username>/argocd-gitops-mega-lab.git` |
| Revision | `main` |
| Path | `k8s/taskflow` |
| Cluster URL | `https://kubernetes.default.svc` |
| Namespace | `taskflow` |

Click **CREATE**.

You'll see the app as **OutOfSync** / **Missing**. That's expected: Argo CD has read Git and knows what *should* exist, but nothing exists in the cluster yet.

> 🎯 **Teaching moment:** Argo CD never deploys by itself unless you tell it to. *Manual* sync means it detects, shows you the difference, and waits.

Click **APP DIFF** to see exactly what will be created. Then click **SYNC → SYNCHRONIZE**.

Watch the resource tree build: Namespace → Secret → StatefulSet → Deployments → Services → Pods.

---

## Part 6 — Verify TaskFlow is running

```bash
kubectl get all -n taskflow
kubectl get pvc -n taskflow
```

✅ **Checkpoint:**
- `taskflow-postgres-0` is `Running` and its PVC is `Bound`
- 2 × `taskflow-api` pods `Running` and `READY 1/1` (ready means it reached Postgres)
- 2 × `taskflow-frontend` pods `Running`

Get the app URL (the load balancer takes 2–3 minutes to come up):

```bash
kubectl get svc taskflow-frontend -n taskflow \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; echo
```

Open `http://<that-hostname>` in a browser. Add a few tasks — they're saved in Postgres.

Note the **banner**: it shows the message, version and the **pod name** that answered.

In Argo CD the app is now **Synced** and **Healthy**.

---

## Part 7 — The GitOps moment: change the app through Git

You will change the running app **without touching kubectl**.

Edit `k8s/taskflow/30-api.yaml`:

```yaml
spec:
  replicas: 3                     # was 2
  ...
          env:
            - name: APP_VERSION
              value: "1.1.0"      # was 1.0.0
            - name: APP_MESSAGE
              value: "Changed through Git - no kubectl!"
```

Commit and push:

```bash
git add k8s/taskflow/30-api.yaml
git commit -m "lab1: scale api to 3 and change banner message"
git push origin main
```

In the Argo CD UI:

1. Click **REFRESH** (Argo CD polls Git every ~3 minutes; Refresh checks now).
2. The app turns **OutOfSync**. Click **APP DIFF** — you see exactly your two changes.
3. Click **SYNC → SYNCHRONIZE**.
4. Watch a rolling update: new pods come up before old ones go (`maxUnavailable: 0`).

Verify:

```bash
kubectl get pods -n taskflow -l app.kubernetes.io/name=taskflow-api
```

✅ **Checkpoint:** 3 API pods. Reload the browser a few times — the new message appears, and the pod name changes as the load spreads across the 3 pods. Your tasks are still there (data lives in Postgres, not in the pods).

---

## Part 8 — See the history

In Argo CD, click **HISTORY AND ROLLBACK**. Each sync is recorded against a Git commit SHA.

```bash
git log --oneline -3
```

> 🎯 **Teaching moment:** the deployment history **is** the Git history. Who changed what, when, and why is in the commit log — not in someone's terminal.

---

## Part 9 — Same Application, as code

Look at `argocd/taskflow-app.yaml`. It's the exact Application you just clicked together in the UI.

```bash
kubectl get application taskflow -n argocd -o yaml | head -40
```

> From Lab 2 onwards we manage Applications as YAML files in Git, not by clicking. That's how Lab 3 bootstraps a whole cluster with one command.

---

## Lab 1 — What you proved

| Question | Answer you can now give |
|---|---|
| Where is the desired state? | In Git (`k8s/taskflow`) |
| Who applies it? | Argo CD's application-controller, not a human |
| How did the app change? | A Git commit → Argo CD diff → sync |
| What does OutOfSync mean? | Git and the cluster disagree |
| Where is the deploy history? | Git log + Argo CD history |

### ⚠️ Spotted the problem?

Open `k8s/taskflow/10-postgres-secret.yaml` and run:

```bash
echo VGFza0Zsb3dAMTIz | base64 -d; echo
```

The database password is sitting in Git, readable by anyone. **Lab 5 fixes this.**

---

## Before the next lab

**Keep the cluster** if Lab 2 is soon — it continues from here.
Otherwise delete it to stop charges (EKS control plane + 2 nodes + load balancer):

```bash
kubectl delete application taskflow -n argocd   # stop Argo CD managing it
kubectl delete namespace taskflow               # removes the load balancer + EBS volume
eksctl delete cluster -f cluster/eks-cluster.yaml
```

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `taskflow-postgres-0` stuck `Pending` | PVC unbound — check `kubectl get sc` shows `gp3 (default)` and ebs-csi pods run |
| API pods `Running` but `0/1 READY` | Postgres not ready yet — wait 1 min; check `kubectl logs deploy/taskflow-api -n taskflow` |
| `ImagePullBackOff` | Image tag in YAML doesn't exist on Docker Hub — check `discoverdevops/taskflow-api:1.0.0` |
| Argo CD shows `repository not found` | Repo URL typo, or your fork is private |
| App stays OutOfSync after push | Click **REFRESH**; confirm you pushed to `main` |
| Browser can't open the app | Load balancer still provisioning — wait 3 min |
