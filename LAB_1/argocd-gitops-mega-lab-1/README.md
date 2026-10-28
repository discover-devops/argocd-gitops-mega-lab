# Argo CD GitOps Mega Lab

One application. One repository. Seven labs that take you from your first Argo CD deploy to rebuilding a whole cluster from Git.

**App:** TaskFlow — nginx frontend · FastAPI backend · Postgres, with probes, resource limits, rolling updates and a persistent volume.

## The 7 labs

| Lab | Title | Covers |
|---|---|---|
| 1 | [GitOps Foundations](labs/lab-1-gitops-foundations.md) | EKS + Argo CD, first Application, Git → Argo CD → Kubernetes |
| 2 | Self-Healing Cluster | Drift, selfHeal, automated sync, prune, full lifecycle |
| 3 | One-Command Cluster Bootstrap | App-of-Apps, sync waves, bootstrap from one root app |
| 4 | Production Sync Controls | Advanced sync options, HPA vs Argo CD + ignoreDifferences, sync windows |
| 5 | Secrets the GitOps Way | Base64 trap, Sealed Secrets, rotation |
| 6 | Multi-Cluster with ApplicationSet | Cluster registration, List generator, global rollout |
| 7 | Capstone: Break, Recover, Rebuild | Full GitOps factory, deliberate failures, disaster recovery |

Each lab has a Git tag for its start state (`lab-1-start`, `lab-2-start`, …) so you can join at any lab.

## Repo layout

```text
app/                 TaskFlow source (api, frontend) + Dockerfiles
cluster/             eksctl cluster config, StorageClass
k8s/taskflow/        Kubernetes manifests Argo CD deploys
argocd/              Argo CD Application definitions
labs/                Step-by-step lab guides
.github/workflows/   Image build pipeline
```

## Trainer setup (once)

1. Add repo secrets `DOCKERHUB_USERNAME=discoverdevops` and `DOCKERHUB_TOKEN`.
2. Actions → **Build TaskFlow images** → Run workflow with version `1.0.0`.
3. Confirm `discoverdevops/taskflow-api:1.0.0` and `discoverdevops/taskflow-frontend:1.0.0` exist on Docker Hub.
4. Tag the start state: `git tag lab-1-start && git push --tags`.

## Cost note

The lab runs on EKS in `ap-south-1` (control plane + 2 × t3.large + one load balancer). Delete the cluster between sessions — see the end of each lab.
