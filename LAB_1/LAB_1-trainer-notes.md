# LAB_1 - Trainer Notes (private, do not push to the student repo)

Lab: GitOps Foundations | Class time: about 90 minutes

---

## The one idea students must leave with

"The developer changes Git. A tool inside the cluster makes the cluster match Git. Nobody runs kubectl on production."

Everything in this session builds towards Part 8, where they prove that sentence themselves. Open with the question, close with the answer.

---

## Opening hook (3 minutes)

Ask the room, and wait for answers before you say anything:

"A developer pushes a bug fix. Twenty minutes later it is live in production. Nobody ran kubectl. Nobody even has the production kubeconfig. How?"

Collect guesses on the board ("Jenkins", "a script", "the pipeline"). Do not correct them yet. You will come back to this list in Part 4 and again in Part 8.

---

## Board plan

Build this left to right, one box at a time, as the lab moves. Do not draw it all at the start.

```text
 [ app/ code ] --> [ GitHub Actions ] --> [ Docker Hub ]          <- draw in Part 2
                                               |
                                    [ Git: image: line ]           <- draw in Part 3
                                               |
                               [ Argo CD inside cluster ]          <- draw in Part 4
                                               |
                                      [ EKS: TaskFlow ]            <- draw in Part 6
```

Then draw a vertical line between Docker Hub and Git, and label the two sides CI and CD. That line is the most important thing on the board.

In Part 4, draw the "push model" next to it: Pipeline --kubectl--> Cluster, with a padlock and "keys to prod?" written on the arrow.

---

## Timing

| Part | What | Minutes |
|---|---|---|
| Hook | Monday morning question | 3 |
| 0 | Starting point check | 3 |
| 1 | Meet TaskFlow | 5 |
| 2 | CI: token, secrets, run the workflow | 15 |
| 3 | Point YAML at own images, push | 7 |
| 4 | Push vs pull, install Argo CD | 12 |
| 5 | Log in | 5 |
| 6 | First Application, OutOfSync | 10 |
| 7 | TaskFlow running | 8 |
| 8 | Change through Git, the payoff | 12 |
| 9-10 | History, Application as code | 7 |
| Close | The secret problem, teaser for Lab 2 | 3 |

**Time-saver:** start the workflow run (Part 2 Step 4) first, then talk through the workflow file while it builds. The build takes 2 to 4 minutes.

**Time-saver:** while waiting for the load balancer in Part 7, do Part 9 (history). Come back to the browser after.

---

## Questions to ask, not answer

Ask, then pause for at least 5 seconds before giving the answer.

| Part | Question | What you want to hear |
|---|---|---|
| 1 | "Can Kubernetes run main.py?" | No, it needs an image |
| 2 | "Where does the Docker Hub password come from? It is not in the file." | GitHub secrets |
| 2 | "You forked my repo. Did my secrets come with it? Should they?" | No, that would leak passwords |
| 2 | "Did the pipeline touch the cluster?" | No, CI stops at the registry |
| 3 | "Whose image is in this YAML?" | Yours (the trainer's), so change it |
| 4 | "Why not just add kubectl apply to the pipeline?" | Pipeline would hold prod keys, and nobody watches drift |
| 6 | "Nothing failed. Why OutOfSync?" | Git and the cluster disagree |
| 8 | "So, how did the fix reach production?" | Git changed, Argo CD applied it |
| 9 | "What changed last Tuesday, and who did it?" | Git log |

---

## What NOT to teach in this lab

These are real topics, but they belong later or nowhere. If a student asks, park it on a "later" list on the board.

- **Dockerfile line by line, FastAPI code.** Students know Docker. Show the files exist, move on.
- **Argo CD architecture in depth** (redis, dex, notifications internals). Three pods matter today: repo-server, application-controller, server.
- **Automated sync, self-heal, prune.** That is the whole of Lab 2. Keep sync Manual today so they feel the difference later.
- **Secrets solutions** (Sealed Secrets, Vault, External Secrets). Only raise the problem at the end. Solution is Lab 5.
- **Helm and Kustomize with Argo CD.** Not used in this course yet. Plain YAML keeps the focus on GitOps.
- **Argo CD CLI.** UI first. The CLI distracts from the concept.
- **Image updater / auto tag bumping.** Advanced. Today a human changes the image line on purpose.
- **Ingress, TLS, DNS.** The LoadBalancer Service is enough to see the app.

---

## Likely student questions

**"Why not build the image on my laptop with docker build and docker push?"**
You can, and it gives the same image. But in real teams, images are built by CI so every build is repeatable, logged and not dependent on one person's laptop.

**"Why does the repo have to be public?"**
So Argo CD can read it without credentials. Private repos work too, you add a repo credential in Argo CD. That is outside today's scope.

**"Why did we change the image to our own? Yours already works."**
Because in real life you deploy what your own CI built. It also shows that the image line in Git is the handoff point between CI and CD.

**"Can the pipeline update the image line automatically?"**
Yes, many teams do exactly that as the last CI step (commit a new tag to the config repo). Mention it as a real pattern, do not build it today.

**"Why port-forward? How does a real team reach Argo CD?"**
Usually through an Ingress with SSO. Port-forward keeps the lab simple and safe.

**"What if two people change Git at the same time?"**
Same as any code: pull requests and reviews. Git is the gate, which is a feature.

---

## Your own dry run note

Your Docker Hub user is `discoverdevops`, so the `sed` in Part 3 changes nothing for you. That is expected. Students will see their own usernames appear.

The workflow file now tags images with the `DOCKERHUB_USERNAME` secret and builds amd64 only (faster, matches the t3 nodes). Your existing `discoverdevops` images are unaffected.

After your dry run, reset the student-facing files before class (your Part 8 edits change `LAB_1/k8s/taskflow/30-api.yaml` in the main repo).
