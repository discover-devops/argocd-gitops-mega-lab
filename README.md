# Argo CD GitOps Mega Lab

**By Rahul Chaubey**

One application. One repository. A setup lab and seven labs that take you from your first Argo CD deployment to rebuilding a whole cluster from Git.

**The application: TaskFlow**
A small production-style three-tier app: an nginx frontend, a FastAPI backend, and Postgres. It uses health probes, resource limits, rolling updates, and a persistent volume.

## The labs

| Lab | Title | What you learn |
|---|---|---|
| 0 | [Prerequisites and EKS Cluster Setup](LAB_0/) | Tools, AWS account, fork, EKS cluster, storage. Finish this before class |
| 1 | [GitOps Foundations](LAB_1/) | Argo CD install, first Application, Git to Argo CD to Kubernetes |
| 2 | [Self-Healing Cluster](LAB_2/) | Drift, self-heal, automated sync, prune, full lifecycle |
| 3 | One-Command Cluster Bootstrap | App-of-Apps, sync waves, bootstrap from one root application |
| 4 | Production Sync Controls | Advanced sync options, HPA vs Argo CD with ignoreDifferences, sync windows |
| 5 | Secrets the GitOps Way | The base64 trap, Sealed Secrets, secret rotation |
| 6 | Multi-Cluster with ApplicationSet | Cluster registration, List generator, global rollout |
| 7 | Capstone: Break, Recover, Rebuild | Full GitOps factory, deliberate failures, disaster recovery |

Every lab has its own folder with its own runbook (README.md) and Kubernetes files. Each folder starts exactly where the previous lab ended, so you can open and follow any lab on its own. Start with LAB_0.

## Diagrams

Every lab has an architecture diagram in the `diagrams` folder. The PNG is for viewing. The `.excalidraw` file opens and edits at https://excalidraw.com (menu, then **Open**).

| Lab | View | Edit |
|---|---|---|
| 0 | [lab-0-architecture.png](diagrams/lab-0-architecture.png) | [lab-0-architecture.excalidraw](diagrams/lab-0-architecture.excalidraw) |
| 1 | [lab-1-architecture.png](diagrams/lab-1-architecture.png) | [lab-1-architecture.excalidraw](diagrams/lab-1-architecture.excalidraw) |
| 2 | [lab-2-architecture.png](diagrams/lab-2-architecture.png) | [lab-2-architecture.excalidraw](diagrams/lab-2-architecture.excalidraw) |

## Repository layout

```text
LAB_0/               Prerequisites, tools and EKS cluster (cluster/ has the eksctl config)
LAB_1/               GitOps Foundations: runbook, k8s/ manifests, argocd/ Application
LAB_2/               Self-Healing Cluster: runbook, k8s/, argocd/, extras/, solutions/
LAB_3/ ... LAB_7/    Added as the course goes on
diagrams/            Architecture diagram for every lab (PNG and editable Excalidraw)
app/                 TaskFlow source code (api, frontend) and Dockerfiles
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
