# Lab 2 - Self-Healing Cluster

**Argo CD GitOps Mega Lab | Lab 2 of 7**
**Written by Rahul Chaubey**

---

## A note from me before you start

Welcome back.

In Lab 1 you deployed TaskFlow from Git, but you still had to click Sync every time. In real companies nobody sits and clicks Sync. Also, someone will always run a quick kubectl command in production "just this once" and forget to tell anyone.

In this lab you will deliberately break your own cluster. First you will watch Argo CD notice. Then you will teach it to fix things on its own. By the end, your cluster will heal itself, deploy every Git change automatically, and clean up anything you remove from Git.

Break things freely in this lab. That is the whole point.

---

## What this lab covers

1. Managing the Argo CD Application as code
2. Configuration drift, and how Argo CD detects it
3. Automated sync: deploy on every Git change
4. Self-heal: undo manual changes automatically
5. Prune: delete what you removed from Git
6. The full GitOps lifecycle, end to end

**Time needed:** about 75 minutes

```text
            Automated sync                 Self-heal                     Prune
 Git change ------------> cluster   kubectl change ----> reverted   file removed ----> resource deleted
```

---

## Part 0 - Starting point

You need your cluster from Lab 1, with TaskFlow showing **Synced** and **Healthy**.

Check it:

```bash
kubectl get pods -n taskflow
kubectl get application taskflow -n argocd
```

**Checkpoint:** 3 API pods, 2 frontend pods, 1 Postgres pod, all Running. The application shows Synced and Healthy.

If you deleted your cluster after Lab 1, run Lab 1 Parts 2 to 6 again first.

Keep the Argo CD port-forward running in a second terminal:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Save the application URL so you can use it in commands:

```bash
export APP_URL=http://$(kubectl get svc taskflow-frontend -n taskflow \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
curl -s $APP_URL/api/version; echo
```

---

## Part 1 - Manage the Application as code

In Lab 1 you created the Application by clicking in the UI. Now you will take over the same Application with a YAML file.

Put your GitHub username into the file:

```bash
export GH_USER=<your-github-username>
sed -i "s/<YOUR_GITHUB_USER>/$GH_USER/" argocd/taskflow-app.yaml
cat argocd/taskflow-app.yaml
```

On macOS use `sed -i ''` instead of `sed -i`.

Apply it:

```bash
kubectl apply -f argocd/taskflow-app.yaml
```

Nothing changes in the UI, because the YAML describes exactly the same Application. Kubernetes simply updated the existing object.

Commit it to Git:

```bash
git add argocd/taskflow-app.yaml
git commit -m "lab2: manage taskflow application as code"
git push origin main
```

**Concept: Everything as code**
Your application manifests are in Git, and now the Argo CD configuration is in Git too. If someone asks how this app is deployed, the answer is a file, not a set of clicks someone remembers.

---

## Part 2 - Create drift and watch Argo CD notice

Right now the sync policy is still Manual. Let us see what Argo CD does when someone changes the cluster by hand.

### Drift 1: someone scales the API by hand

```bash
kubectl scale deployment taskflow-api -n taskflow --replicas=1
kubectl get pods -n taskflow -l app.kubernetes.io/name=taskflow-api
```

Go to the Argo CD UI. Within a few seconds the application turns **OutOfSync**. Click the **taskflow-api** Deployment, then **DIFF**. You see Git says 3 and the cluster says 1.

### Drift 2: someone changes the message in production

```bash
kubectl set env deployment/taskflow-api -n taskflow APP_MESSAGE="Hotfix done directly in prod"
```

Wait for the rollout, then check:

```bash
curl -s $APP_URL/api/version; echo
```

The live message changed. Look at the DIFF in Argo CD again. The env change shows up there too.

### Drift 3: someone deletes a Service

```bash
kubectl delete service taskflow-api -n taskflow
curl -s $APP_URL/api/version; echo
```

The frontend can no longer reach the API. Your browser shows "API not reachable". In Argo CD, the taskflow-api Service is marked **Missing**.

**Checkpoint:** the application is OutOfSync, and Argo CD shows all three drifts. It has fixed none of them, because the sync policy is Manual.

**Concept: What is configuration drift?**
Drift is any difference between what Git says and what is actually running. It happens through manual kubectl commands, emergency hotfixes, or other tools. Without GitOps, drift builds up silently until nobody knows what production really looks like. Argo CD detects it within seconds because it constantly compares the live state with Git.

### Fix it with one sync

Click **SYNC**, then **SYNCHRONIZE**.

```bash
kubectl get pods,svc -n taskflow
curl -s $APP_URL/api/version; echo
```

**Checkpoint:** 3 API pods again, the Service is back, and the message is the one from Git.

---

## Part 3 - Turn on automated sync

Edit `argocd/taskflow-app.yaml` and replace `syncPolicy: {}` with:

```yaml
  syncPolicy:
    automated: {}
```

Apply and commit:

```bash
kubectl apply -f argocd/taskflow-app.yaml
git add argocd/taskflow-app.yaml
git commit -m "lab2: enable automated sync"
git push origin main
```

### Test 1: a Git change deploys itself

Edit `k8s/taskflow/30-api.yaml`:

```yaml
            - name: APP_VERSION
              value: "1.2.0"
            - name: APP_MESSAGE
              value: "Deployed automatically - nobody clicked Sync"
```

```bash
git add k8s/taskflow/30-api.yaml
git commit -m "lab2: release 1.2.0"
git push origin main
```

Click **REFRESH** in the UI (or wait up to 3 minutes). Do not click Sync. Watch Argo CD sync on its own.

```bash
curl -s $APP_URL/api/version; echo
```

**Checkpoint:** version 1.2.0 is live and you never clicked Sync.

### Test 2: does automated sync fix drift?

```bash
kubectl scale deployment taskflow-api -n taskflow --replicas=1
```

Wait 30 seconds and watch the UI.

**Checkpoint:** the application stays **OutOfSync**, and the API stays at 1 replica.

**Concept: Automated sync only reacts to Git**
Automated sync means "when Git changes, deploy it". It does not mean "when the cluster changes, fix it". Those are two separate switches. The second one is called self-heal, and you turn it on next.

---

## Part 4 - Turn on self-heal

Edit `argocd/taskflow-app.yaml`:

```yaml
  syncPolicy:
    automated:
      selfHeal: true
```

```bash
kubectl apply -f argocd/taskflow-app.yaml
git add argocd/taskflow-app.yaml
git commit -m "lab2: enable self-heal"
git push origin main
```

Within a few seconds the API goes back to 3 replicas on its own. Argo CD fixed the drift you left behind in Part 3.

Open a second watch window so you can see self-heal happen live:

```bash
kubectl get pods -n taskflow -w
```

Now try to break things.

### Break 1: scale it down

```bash
kubectl scale deployment taskflow-api -n taskflow --replicas=1
```

### Break 2: change the message

```bash
kubectl set env deployment/taskflow-api -n taskflow APP_MESSAGE="Sneaky prod change"
```

### Break 3: delete the whole frontend Deployment

```bash
kubectl delete deployment taskflow-frontend -n taskflow
```

### Break 4: delete the API Service

```bash
kubectl delete service taskflow-api -n taskflow
```

**Checkpoint:** after every break, Argo CD puts things back within seconds. Check the result:

```bash
kubectl get deploy,svc -n taskflow
curl -s $APP_URL/api/version; echo
```

The message is the one from Git, not "Sneaky prod change".

Do not delete the `taskflow-frontend` Service. It is the AWS load balancer. Argo CD would recreate it, but AWS would give it a new hostname and you would need to update APP_URL.

**Concept: Self-heal**
With self-heal on, Git is not just the source of truth on paper. It is enforced. Any manual change in the cluster is reverted automatically, usually within about 5 seconds. This is what people mean by a self-healing cluster.

**Concept: So how do you make an emergency fix?**
Through Git. A hotfix is a small commit, merged quickly. It is deployed the same way as everything else, and it leaves a record of who changed what and why. If you really must stop Argo CD for a moment, you turn off self-heal in Git. You do not fight it with kubectl.

---

## Part 5 - Prune: delete what you remove from Git

### Step 1: add a debug toolbox through Git

```bash
cp extras/toolbox.yaml k8s/taskflow/50-toolbox.yaml
git add k8s/taskflow/50-toolbox.yaml
git commit -m "lab2: add debug toolbox"
git push origin main
```

Click **REFRESH**. A new `taskflow-toolbox` pod appears. Use it to call the API from inside the cluster:

```bash
kubectl exec -n taskflow deploy/taskflow-toolbox -- \
  curl -s http://taskflow-api:8000/api/version; echo
```

This is how you test service-to-service traffic inside Kubernetes.

### Step 2: remove it from Git

You are done debugging, so remove the file:

```bash
git rm k8s/taskflow/50-toolbox.yaml
git commit -m "lab2: remove debug toolbox"
git push origin main
```

Click **REFRESH**, then check:

```bash
kubectl get pods -n taskflow -l app.kubernetes.io/name=taskflow-toolbox
```

**Checkpoint:** the toolbox pod is still running. In the UI, the application is OutOfSync and the toolbox shows a **trash can** icon with the label "requires pruning".

**Concept: Why did Argo CD not delete it?**
Deleting things is dangerous, so by default Argo CD never deletes anything. Imagine someone accidentally removes the Postgres file from Git. Without this safety, the database would be deleted too. Argo CD only deletes when you clearly allow it with prune.

### Step 3: turn on prune

Edit `argocd/taskflow-app.yaml`:

```yaml
  syncPolicy:
    automated:
      selfHeal: true
      prune: true
```

```bash
kubectl apply -f argocd/taskflow-app.yaml
git add argocd/taskflow-app.yaml
git commit -m "lab2: enable prune"
git push origin main
```

**Checkpoint:** within seconds the toolbox Deployment and its pod are deleted, and the application is Synced again.

### Step 4: what about things created with kubectl?

```bash
kubectl create configmap manual-config -n taskflow --from-literal=owner=me
kubectl get configmap manual-config -n taskflow
```

Wait 30 seconds and check again. The ConfigMap is still there, and Argo CD does not show it at all.

**Concept: Argo CD only manages what it created**
Prune only deletes resources that Argo CD itself deployed from Git and that have since been removed from Git. Something created by hand was never part of the application, so Argo CD leaves it alone. This is how several teams and tools can share one namespace safely.

Clean it up:

```bash
kubectl delete configmap manual-config -n taskflow
```

---

## Part 6 - Delete the Application safely

Look at `solutions/lab-2/taskflow-app.yaml`. It has one extra block you do not have yet:

```yaml
metadata:
  finalizers:
    - resources-finalizer.argocd.argoproj.io
```

Add it to your `argocd/taskflow-app.yaml` under `metadata`, then apply and commit:

```bash
kubectl apply -f argocd/taskflow-app.yaml
git add argocd/taskflow-app.yaml
git commit -m "lab2: delete app resources when the application is deleted"
git push origin main
```

**Concept: The resources finalizer**
Without this finalizer, deleting the Application in Argo CD leaves all its Kubernetes resources running, which is the safe default. With it, deleting the Application also deletes everything it deployed. Use it when you want one clean "remove this app" action, as we do at the end of each lab.

Compare your file with the solution:

```bash
diff argocd/taskflow-app.yaml solutions/lab-2/taskflow-app.yaml
```

The only difference should be your GitHub username.

---

## Part 7 - The full GitOps lifecycle

Now put it all together, as a real team would work.

**Step 1. A developer releases version 1.3.0 through Git**

Edit `k8s/taskflow/30-api.yaml`:

```yaml
            - name: APP_VERSION
              value: "1.3.0"
            - name: APP_MESSAGE
              value: "Release 1.3.0 - fully GitOps"
```

```bash
git add k8s/taskflow/30-api.yaml
git commit -m "release: 1.3.0"
git push origin main
```

**Step 2. Argo CD deploys it automatically.** Click REFRESH and watch, without clicking Sync.

**Step 3. Someone changes production by hand**

```bash
kubectl scale deployment taskflow-api -n taskflow --replicas=5
```

**Step 4. Argo CD heals it.** Back to 3 within seconds.

**Step 5. The team decides 2 API replicas are enough**

Change `replicas: 3` to `replicas: 2` in `30-api.yaml`, then commit and push. Argo CD scales it down for you.

**Step 6. Check the history**

```bash
git log --oneline -10
```

In the UI, open **HISTORY AND ROLLBACK**.

**Checkpoint:** every change in production matches a commit in Git. Nothing that was done by hand survived.

```text
 Developer --> git commit --> Argo CD detects --> auto sync --> cluster updated
                                                                    |
     manual kubectl change ---> drift detected ---> self-heal ------+
     file removed from Git ---> prune deletes resource
```

---

## Summary - What you proved in Lab 2

| Setting | What it does | Default |
|---|---|---|
| Manual sync | Detects drift, shows it, waits for you | Yes |
| automated | Deploys every Git change on its own | Off |
| selfHeal | Reverts manual changes in the cluster | Off |
| prune | Deletes resources removed from Git | Off |
| resources finalizer | Deleting the Application deletes its resources | Off |

| Question | Your answer now |
|---|---|
| What is drift? | Any difference between Git and the live cluster |
| Does automated sync fix drift? | No, only selfHeal does |
| Why is prune off by default? | To protect against accidental deletion |
| Does prune delete things made with kubectl? | No, only resources Argo CD deployed |
| How do you make an emergency fix? | A fast Git commit, never kubectl |

---

## Looking ahead

Right now, one Application deploys everything in one folder: the database, the API and the frontend. In a real cluster you also have security policies, networking and monitoring, and they must come up in the right order. The database must be ready before the API starts.

In Lab 3 we split this into an App-of-Apps with sync waves, and we bootstrap the whole cluster from a single file.

---

## Before the next lab

If Lab 3 is coming up soon, **keep your cluster running**.

If not, clean up to stop AWS charges. Because you added the finalizer in Part 6, deleting the Application now removes everything it deployed:

```bash
kubectl delete application taskflow -n argocd
kubectl get all -n taskflow
eksctl delete cluster -f cluster/eks-cluster.yaml
```

Wait until `kubectl get all -n taskflow` shows nothing before you delete the cluster. That confirms the load balancer and the EBS disk are gone.

---

## Troubleshooting

| What you see | Cause and fix |
|---|---|
| Changes are not deployed automatically | Check that your app has `automated` with `kubectl get application taskflow -n argocd -o yaml`, then click REFRESH |
| Self-heal does not revert changes | `selfHeal: true` must be inside `automated`, not next to it. Check your indentation |
| Toolbox not deleted after removing it from Git | `prune: true` is missing, or you did not apply the updated file |
| kubectl apply on the app fails | Make sure you replaced YOUR_GITHUB_USER with your real username |
| APP_URL stopped working | The frontend Service was deleted and got a new hostname. Run the export APP_URL command again |
| Application stuck deleting | The finalizer is waiting for resources to be removed. Check `kubectl get all -n taskflow` and wait |

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

See you in Lab 3, where one single file builds your entire cluster.

**Rahul Chaubey**
