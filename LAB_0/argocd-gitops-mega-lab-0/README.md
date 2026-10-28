# Argo CD GitOps Mega Lab

**By Rahul Chaubey**

One application. One repository. A setup lab and seven labs that take you from your first Argo CD deployment to rebuilding a whole cluster from Git.

**The application: TaskFlow**
A small production-style three-tier app: an nginx frontend, a FastAPI backend, and Postgres. It uses health probes, resource limits, rolling updates, and a persistent volume.

## The labs

| Lab | Title | What you learn |
|---|---|---|
| 0 | [Prerequisites and EKS Cluster Setup](labs/lab-0-prerequisites.md) | Tools, AWS account, fork, EKS cluster, storage. Finish this before class |
| 1 | [GitOps Foundations](labs/lab-1-gitops-foundations.md) | Argo CD install, first Application, Git to Argo CD to Kubernetes |
| 2 | [Self-Healing Cluster](labs/lab-2-self-healing-cluster.md) | Drift, self-heal, automated sync, prune, full lifecycle |
| 3 | One-Command Cluster Bootstrap | App-of-Apps, sync waves, bootstrap from one root application |
| 4 | Production Sync Controls | Advanced sync options, HPA vs Argo CD with ignoreDifferences, sync windows |
| 5 | Secrets the GitOps Way | The base64 trap, Sealed Secrets, secret rotation |
| 6 | Multi-Cluster with ApplicationSet | Cluster registration, List generator, global rollout |
| 7 | Capstone: Break, Recover, Rebuild | Full GitOps factory, deliberate failures, disaster recovery |

Each lab has a Git tag for its starting point (lab-1-start, lab-2-start, and so on), so you can join at any lab.

## Repository layout

```text
app/                 TaskFlow source code (api, frontend) and Dockerfiles
cluster/             eksctl cluster config and StorageClass
k8s/taskflow/        Kubernetes manifests that Argo CD deploys
argocd/              Argo CD Application definitions
labs/                Step-by-step lab runbooks
.github/workflows/   Image build pipeline
```

## Cost note

The labs run on AWS EKS in the Mumbai region (ap-south-1): one control plane, 2 t3.large nodes, and one load balancer. Delete the cluster between sessions. Each runbook shows you how at the end.

## Keep learning with me

| Where | Link |
|---|---|
| YouTube - Build Automate Architect | https://www.youtube.com/@BuildAutomateArchitect |
| System Design playlist | https://www.youtube.com/playlist?list=PLeAHTLMwFYQ0 |
| Telegram channel | https://t.me/BuildAutomateArchitect |
| Website | https://rahulchaubeyconsulting.com/ |
