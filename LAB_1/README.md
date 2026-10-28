# Lab 1 - GitOps Foundations

**Argo CD GitOps Mega Lab | Lab 1 of 7**
**Written by Rahul Chaubey**

---

## A note from me before you start

Hello, and welcome to the GitOps Mega Lab.

I have written this runbook for you, step by step, so you can repeat everything we did in class on your own. Do not just copy and paste the commands. Read the Concept notes, run each step, and check the result at every Checkpoint before you move on. If something breaks, that is good. Fixing it is how you actually learn this.

In Lab 0 you prepared your tools and created the EKS cluster. In this lab you will build the foundation that the next six labs grow on. By the end of it you will have a real three-tier application running on your EKS cluster. Argo CD will deploy it from your own Git repository. You will change the running application with nothing more than a Git commit.

Let us begin.

---

## What you will build

```text
 You --git push--> GitHub (your fork) <--watches-- Argo CD --applies--> EKS cluster
                                                                            |
                                  taskflow-frontend --> taskflow-api --> taskflow-postgres
```

**The application: TaskFlow**

| Tier | Technology | What it does |
|---|---|---|
| Frontend | nginx | Serves the web page and forwards /api calls to the API |
| API | Python FastAPI | Stores and lists tasks, reports its version and pod name |
| Database | Postgres | Keeps your tasks on a persistent disk |

**What this lab covers**

1. Installing Argo CD and understanding its components
2. Creating your first Argo CD Application
3. Deploying TaskFlow from Git
4. Changing the application through Git only
5. Reading deployment history from Git

**Time needed:** about 60 minutes

---

## Part 0 - Starting point

You must finish **Lab 0 - Prerequisites and EKS Cluster Setup** before this lab.

**Get the latest labs into your fork.** I add new lab folders as the course goes on. Open your fork on GitHub and click **Sync fork**, then **Update branch**. Then pull it to your laptop:

```bash
cd argocd-gitops-mega-lab
git pull origin main
cd LAB_1
```

From now on, run every command in this lab from inside the `LAB_1` folder.

Run this quick check:

```bash
kubectl get nodes
kubectl get storageclass
git remote -v
```

**Checkpoint:** 2 nodes `Ready`, `gp3 (default)` is listed, and the Git remote URLs contain your GitHub username.

If any check fails, go back to Lab 0 and fix it first.

---

## Part 1 - Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

We use `--server-side` because some Argo CD resource definitions are too large for a normal `kubectl apply`. Without it you may see an "annotations too long" error.

Wait for all components to start:

```bash
kubectl wait --for=condition=Available deployment --all -n argocd --timeout=300s
kubectl get pods -n argocd
```

**Checkpoint:** all pods are `Running`. Make sure you understand what each one does:

| Pod | What it does |
|---|---|
| argocd-server | The UI and API you log in to |
| argocd-repo-server | Clones your Git repository and reads the manifests |
| argocd-application-controller | Compares Git with the cluster and applies the difference |
| argocd-applicationset-controller | Generates many Applications from one template (Lab 6) |
| argocd-redis | Cache used by the other components |
| argocd-dex-server | Single sign-on (not used in this lab) |
| argocd-notifications-controller | Sends alerts (not used in this lab) |

**Concept: Pull model**
In a normal CI/CD pipeline, Jenkins or GitHub Actions pushes changes into the cluster. That means the pipeline needs cluster credentials. In GitOps, Argo CD runs inside the cluster and pulls from Git. The cluster credentials never leave the cluster. This is one of the main security benefits of GitOps.

---

## Part 2 - Log in to the Argo CD UI

Open a second terminal and keep this command running:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

In your first terminal, get the initial admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d; echo
```

Open https://localhost:8080 in your browser and accept the certificate warning.

- Username: `admin`
- Password: the value you just printed

**Checkpoint:** you see an empty Applications page.

---

## Part 3 - Create your first Application

Click **+ NEW APP** and fill in these values:

| Field | Value |
|---|---|
| Application Name | taskflow |
| Project | default |
| Sync Policy | Manual |
| Repository URL | https://github.com/your-github-username/argocd-gitops-mega-lab.git |
| Revision | main |
| Path | LAB_1/k8s/taskflow |
| Cluster URL | https://kubernetes.default.svc |
| Namespace | taskflow |

Click **CREATE**.

The Path is the folder inside your repository that Argo CD reads. Each lab has its own folder, so in this lab Argo CD reads only `LAB_1/k8s/taskflow`.

The application now shows **OutOfSync** and **Missing**. This is expected. Argo CD has read your Git repository and knows what should exist, but nothing exists in the cluster yet.

**Concept: Desired state vs live state**
Argo CD always compares two things. The desired state is what Git says. The live state is what is actually running in the cluster. OutOfSync simply means these two do not match. With Manual sync, Argo CD detects the difference, shows it to you, and waits for you to approve.

Click **APP DIFF** to see exactly what will be created.

Now click **SYNC**, then **SYNCHRONIZE**.

Watch the resource tree build itself: Namespace, Secret, StatefulSet, Deployments, Services, and Pods.

---

## Part 4 - Verify that TaskFlow is running

```bash
kubectl get all -n taskflow
kubectl get pvc -n taskflow
```

**Checkpoint:**

- `taskflow-postgres-0` is `Running` and its PVC is `Bound`
- 2 `taskflow-api` pods are `Running` and show `READY 1/1`
- 2 `taskflow-frontend` pods are `Running`

**Concept: Readiness probe**
The API pod shows `READY 1/1` only after its `/readyz` check can reach Postgres. Until then, Kubernetes does not send any traffic to it. This is how production applications avoid serving errors while they are still starting.

Get the application URL. The load balancer can take 2 to 3 minutes to come up:

```bash
kubectl get svc taskflow-frontend -n taskflow \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'; echo
```

Open `http://<that-hostname>` in your browser and add a few tasks. They are saved in Postgres.

Look at the banner at the top. It shows the message, the version, and the name of the pod that answered your request. Remember this, because you are about to change it.

In Argo CD the application now shows **Synced** and **Healthy**.

---

## Part 5 - Change the application through Git

This is the most important part of the lab. You will change the running application without running a single kubectl command against it.

Open `k8s/taskflow/30-api.yaml` inside the LAB_1 folder and make these three changes:

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

Now go to the Argo CD UI:

1. Click **REFRESH**. Argo CD checks Git about every 3 minutes on its own, and Refresh checks right now.
2. The application turns **OutOfSync**. Click **APP DIFF** and you will see exactly your changes.
3. Click **SYNC**, then **SYNCHRONIZE**.
4. Watch the rolling update. New pods come up before old pods are removed.

Verify:

```bash
kubectl get pods -n taskflow -l app.kubernetes.io/name=taskflow-api
```

**Checkpoint:** you see 3 API pods. Reload the browser a few times. The new message appears, and the pod name changes as requests spread across the 3 pods. Your tasks are still there because the data lives in Postgres, not in the API pods.

**Concept: Git is the single source of truth**
You did not touch the cluster. You changed a file, Git recorded the change, and Argo CD made the cluster match Git. In a real company, this is how every change reaches production. A change gets reviewed as a pull request and merged, and Argo CD deploys it.

**Concept: Zero-downtime rolling update**
Look at the `strategy` section in `30-api.yaml`. With `maxUnavailable: 0`, Kubernetes never removes an old pod until a new one is ready. Your users never see the application go down during a deployment.

---

## Part 6 - Read the deployment history

In Argo CD, click **HISTORY AND ROLLBACK**. Every sync is recorded against a Git commit ID.

Now compare it with your Git log:

```bash
git log --oneline -3
```

**Concept: Deployment history is Git history**
Who changed what, when, and why is all in the commit log. It is not hidden in someone's terminal history. This gives you a full audit trail for free, and auditors love it.

---

## Part 7 - The same Application, written as code

Open `argocd/taskflow-app.yaml`. It is exactly the Application you just created by clicking in the UI, written as a YAML file.

See what Argo CD stored:

```bash
kubectl get application taskflow -n argocd -o yaml | head -40
```

**Concept: Applications are also code**
Clicking in the UI is good for learning, but it is not repeatable. From Lab 2 onwards we will define Applications as YAML files in Git. That is what lets us rebuild a whole cluster with one command in Lab 3.

---

## Summary - What you proved in Lab 1

| Question | Your answer now |
|---|---|
| Where does the desired state live? | In Git, in the LAB_1/k8s/taskflow folder |
| Who applies it to the cluster? | The Argo CD application controller, not a person |
| How did the application change? | Git commit, then Argo CD diff, then sync |
| What does OutOfSync mean? | Git and the cluster do not match |
| Where is the deployment history? | Git log and Argo CD history |

---

## Did you spot the problem?

Open `k8s/taskflow/10-postgres-secret.yaml` and run this:

```bash
echo VGFza0Zsb3dAMTIz | base64 -d; echo
```

You just read the database password straight out of Git. Base64 is encoding, not encryption. Anyone who can see the repository can read it.

I left it this way on purpose. Keep this in mind, because in Lab 5 we will fix it properly with Sealed Secrets.

---

## Before the next lab

If Lab 2 is coming up soon, **keep your cluster running**. Lab 2 continues from exactly where you are now.

If not, delete everything to stop AWS charges. EKS, the 2 nodes, and the load balancer all cost money every hour.

```bash
kubectl delete application taskflow -n argocd
kubectl delete namespace taskflow
eksctl delete cluster -f ../LAB_0/cluster/eks-cluster.yaml
```

Delete the `taskflow` namespace before the cluster. This removes the AWS load balancer and the EBS disk cleanly, so nothing is left behind on your bill.

---

## Troubleshooting

| What you see | Cause and fix |
|---|---|
| taskflow-postgres-0 stuck in Pending | The disk was not created. Check that `kubectl get sc` shows gp3 (default) and the ebs-csi pods are running |
| API pods Running but 0/1 READY | Postgres is not ready yet. Wait one minute, then check `kubectl logs deploy/taskflow-api -n taskflow` |
| ImagePullBackOff | The image tag in the YAML does not exist. Check the image name and tag carefully |
| Argo CD says repository not found | Typo in the repository URL, or your fork is private |
| Application stays OutOfSync after push | Click REFRESH and confirm you pushed to the main branch |
| Browser cannot open the application | The load balancer is still being created. Wait 3 minutes and try again |

---

## Keep learning with me

If this lab helped you, there is a lot more where it came from.

| Where | Link |
|---|---|
| YouTube - Build Automate Architect | https://www.youtube.com/@BuildAutomateArchitect |
| System Design playlist | https://www.youtube.com/playlist?list=PLeAHTLMwFYQ0 |
| Telegram channel (lab updates and notes) | https://t.me/BuildAutomateArchitect |
| Website | https://rahulchaubeyconsulting.com/ |

Subscribe on YouTube and join the Telegram channel so you do not miss the next lab.

See you in Lab 2, where we break the cluster on purpose and watch Argo CD heal it.

**Rahul Chaubey**
