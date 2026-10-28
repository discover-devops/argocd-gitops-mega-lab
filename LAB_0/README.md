# Lab 0 - Prerequisites and EKS Cluster Setup

**Argo CD GitOps Mega Lab | Lab 0 - Before we start**
**Written by Rahul Chaubey**

---

## A note from me before you start

Hello, and welcome to the GitOps Mega Lab.

Before we touch Argo CD, your laptop and your AWS account must be ready. Most problems students face in GitOps classes are not about GitOps at all. A tool is missing, AWS credentials are wrong, or the cluster was never fully created. This lab removes all of that, so from Lab 1 onwards you can focus only on learning.

Please finish this lab before the first class. Do every step, and do not skip the Checkpoints. If all the checks at the end pass, you are ready.

Let us begin.

---

## What this lab covers

1. Installing the tools: git, AWS CLI, kubectl and eksctl
2. Preparing your AWS account and credentials
3. Forking and cloning the lab repository
4. Creating the EKS cluster
5. Creating the default storage class
6. A final readiness check
7. Deleting the cluster to save money

**Time needed:** about 60 minutes (20 minutes of this is waiting for EKS)

```text
 Your laptop                         AWS (Mumbai, ap-south-1)
 +-----------------------+           +-----------------------------------+
 | git                   |           |  EKS cluster: gitops-lab          |
 | aws cli   ------------+---------->|    2 worker nodes (t3.large)      |
 | eksctl                |           |    EBS CSI driver (disks)         |
 | kubectl               |           |    gp3 default StorageClass       |
 +-----------------------+           +-----------------------------------+
```

---

## Part 1 - Install the tools

You need four tools. Follow the section for your operating system only.

| Tool | Why you need it |
|---|---|
| git | Clone the repository and push your changes. In GitOps, every change is a Git commit |
| AWS CLI v2 | Talk to your AWS account |
| eksctl | Create and delete the EKS cluster with one command |
| kubectl | Talk to the Kubernetes cluster |

### Option A - Windows

Use **Git Bash** as your terminal for every lab. All commands in this course are written for a bash shell.

**Step 1. Install Git for Windows (this gives you Git Bash)**

Open PowerShell and run:

```powershell
winget install -e --id Git.Git
```

If winget is not available, download the installer from https://git-scm.com/download/win and keep the default options.

**Step 2. Install AWS CLI v2 and kubectl**

In the same PowerShell window:

```powershell
winget install -e --id Amazon.AWSCLI
winget install -e --id Kubernetes.kubectl
```

**Step 3. Install eksctl**

Close PowerShell and open **Git Bash**. Run:

```bash
mkdir -p ~/bin
cd ~/bin
curl -sLO https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Windows_amd64.zip
unzip -o eksctl_Windows_amd64.zip
rm eksctl_Windows_amd64.zip
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
cd ~
```

**Step 4. Close Git Bash and open it again**, so the new tools are picked up.

### Option B - macOS

Install Homebrew from https://brew.sh if you do not have it, then run:

```bash
brew install git awscli kubectl eksctl
```

### Option C - Linux (Ubuntu, Amazon Linux, or similar)

```bash
# AWS CLI v2
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
unzip -q awscliv2.zip
sudo ./aws/install
rm -rf aws awscliv2.zip

# kubectl
curl -sLO "https://dl.k8s.io/release/$(curl -sL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

# eksctl
curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"
tar -xzf eksctl_Linux_amd64.tar.gz
sudo mv eksctl /usr/local/bin/
rm eksctl_Linux_amd64.tar.gz
```

Install git with your package manager if it is missing, for example `sudo apt install -y git` or `sudo dnf install -y git`.

### Check the tools (all operating systems)

```bash
git --version
aws --version
kubectl version --client
eksctl version
```

**Checkpoint:** all four commands print a version number. If one says "command not found", close and reopen your terminal, then try again.

---

## Part 2 - Prepare your AWS account

### Step 1. Use a lab-friendly AWS account

Use your own personal AWS account, or a separate account created only for learning. Do not use your company's production account for these labs.

### Step 2. Create a budget alert

Do this first. It protects you from a surprise bill if you forget to delete the cluster.

1. Open the AWS Console and search for **Budgets**.
2. Click **Create budget**, then choose **Use a template** and **Monthly cost budget**.
3. Enter an amount you are comfortable with and your email address.
4. Click **Create budget**.

**Concept: Why a budget alert matters**
EKS is not free. You pay every hour for the cluster control plane, the 2 worker nodes, and the load balancer, whether you use them or not. A budget alert emails you when spending crosses your limit. Every cloud engineer should have one on every account.

### Step 3. Create an IAM user for the labs

1. In the AWS Console, open **IAM**, then **Users**, then **Create user**.
2. User name: `gitops-lab-admin`
3. On the permissions page choose **Attach policies directly** and select **AdministratorAccess**.
4. Create the user.
5. Open the user, go to **Security credentials**, and click **Create access key**.
6. Choose **Command Line Interface (CLI)**, accept the confirmation, and create the key.
7. Copy the **Access key ID** and **Secret access key**. You will not see the secret again.

**Concept: Why AdministratorAccess here?**
eksctl creates many AWS resources: a VPC, subnets, IAM roles, EC2 nodes, and CloudFormation stacks. Giving exact minimum permissions for all of that is a lesson of its own. For a personal lab account, admin access keeps you focused on GitOps. In a real company you would get a role with only the permissions you need. Never share these keys and never commit them to Git.

### Step 4. Configure the AWS CLI

```bash
aws configure
```

Enter:

| Prompt | Value |
|---|---|
| AWS Access Key ID | the key you copied |
| AWS Secret Access Key | the secret you copied |
| Default region name | ap-south-1 |
| Default output format | json |

Test it:

```bash
aws sts get-caller-identity
```

**Checkpoint:** you see your account number and an ARN ending in `user/gitops-lab-admin`.

---

## Part 3 - Set up Git and the lab repository

### Step 1. Set your Git identity

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

Use the same email as your GitHub account.

### Step 2. Fork the repository

Open https://github.com/discover-devops/argocd-gitops-mega-lab and click **Fork**. Keep the repository name as `argocd-gitops-mega-lab` and keep it **Public**.

**Concept: Why do you need a fork?**
Argo CD watches a Git repository and makes the cluster match it. To see GitOps work, you must be able to push changes to that repository. My repository is read-only for you, so you work on your own copy. It stays public so Argo CD can read it without a password.

### Step 3. Clone your fork

```bash
export GH_USER=<your-github-username>
git clone https://github.com/$GH_USER/argocd-gitops-mega-lab.git
cd argocd-gitops-mega-lab
ls
```

**Checkpoint:** you see the folders `LAB_0`, `LAB_1`, `LAB_2` and `app`.

**Concept: How this repository is organised**
Every lab has its own folder: `LAB_0`, `LAB_1`, `LAB_2`, and so on. Each folder has its own runbook (the README.md you are reading now) and its own Kubernetes files. Each lab folder starts exactly where the previous lab ended, so you can open any lab and follow it on its own. You run every lab's commands from inside that lab's folder. The `app` folder holds the TaskFlow source code. You only need to read it, never change it.

### Step 4. Check that you can push

```bash
git commit --allow-empty -m "lab0: my first push"
git push origin main
```

The first push opens a browser window asking you to sign in to GitHub. Sign in and allow access.

**Checkpoint:** the push succeeds, and you see the commit "lab0: my first push" on your fork's GitHub page.

**Concept: Why test the push now?**
Everything in GitOps happens through `git push`. If your push does not work, nothing in Lab 1 will work. It is much better to find that out today than in the middle of class.

---

## Part 4 - Create the EKS cluster

Go into the LAB_0 folder, then create the cluster:

```bash
cd LAB_0
eksctl create cluster -f cluster/eks-cluster.yaml
```

This takes 15 to 20 minutes. Do not close the terminal.

While you wait, open `cluster/eks-cluster.yaml` and read it.

| Setting | Meaning |
|---|---|
| name: gitops-lab | The cluster name |
| region: ap-south-1 | Mumbai region |
| withOIDC: true | Lets Kubernetes service accounts use AWS IAM roles |
| aws-ebs-csi-driver | Lets pods get real AWS EBS disks. Postgres needs this |
| t3.large, 2 nodes | Enough memory for Argo CD and TaskFlow together |

**Concept: What eksctl is doing for you**
Behind this one command, eksctl creates CloudFormation stacks that build a VPC, public and private subnets, IAM roles, the EKS control plane, and a managed node group. Creating all of that by hand in the AWS Console would take an hour and dozens of screens. Open **CloudFormation** in the AWS Console while you wait to watch the stacks being created.

When the command finishes, eksctl also writes your kubeconfig, so kubectl already points at the new cluster.

Verify:

```bash
kubectl config current-context
kubectl get nodes
kubectl get pods -n kube-system
```

**Checkpoint:**

- The current context contains `gitops-lab`
- 2 nodes show `Ready`
- The pods `coredns`, `aws-node`, `kube-proxy` and `ebs-csi` show `Running`

---

## Part 5 - Create the default storage class

```bash
kubectl apply -f cluster/storageclass-gp3.yaml
kubectl get storageclass
```

**Checkpoint:** you see `gp3 (default)`.

**Concept: Why do we need a StorageClass?**
Postgres asks Kubernetes for a disk using a PersistentVolumeClaim. Newer EKS clusters do not mark any storage class as default, so that request would stay `Pending` forever. The gp3 StorageClass tells Kubernetes how to create an AWS EBS gp3 volume when a pod asks for storage.

### Prove that storage works

Create a small test disk and a pod that uses it:

```bash
kubectl apply -f - <<'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: storage-test
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: storage-test
spec:
  containers:
    - name: test
      image: busybox:1.36
      command: ["sh", "-c", "echo storage works > /data/test.txt && cat /data/test.txt && sleep 3600"]
      volumeMounts:
        - name: data
          mountPath: /data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: storage-test
EOF
```

Wait about 30 seconds, then check:

```bash
kubectl get pvc storage-test
kubectl logs storage-test
```

**Checkpoint:** the PVC shows `Bound` and the log says `storage works`.

Delete the test resources:

```bash
kubectl delete pod storage-test
kubectl delete pvc storage-test
```

---

## Part 6 - Final readiness check

Run all of these. Every line must pass before Lab 1.

| Check | Command | Expected result |
|---|---|---|
| AWS access | `aws sts get-caller-identity` | Your account and lab user |
| Cluster access | `kubectl get nodes` | 2 nodes Ready |
| Storage | `kubectl get storageclass` | gp3 (default) |
| Git push | `git push origin main` | Everything up-to-date |
| Your fork | `git remote -v` | URLs contain your GitHub username, not discover-devops |

If every check passes, you are ready for Lab 1.

---

## Part 7 - Delete the cluster when you are not using it

If your next class is not today, delete the cluster to stop charges. Run this from the `LAB_0` folder:

```bash
eksctl delete cluster -f cluster/eks-cluster.yaml
```

This takes about 10 minutes. Before class, create it again with Part 4 and Part 5. It is the same command every time, which is exactly why we keep the cluster definition in a file.

After deleting, open **CloudFormation** in the AWS Console and make sure no stacks starting with `eksctl-gitops-lab` are left. Also check **EC2**, then **Volumes**, and delete any leftover volumes that show `available`.

**Concept: Cattle, not pets**
We delete and recreate the cluster freely because nothing important lives only inside it. The cluster setup is in `LAB_0/cluster/eks-cluster.yaml`, and from Lab 1 onwards the applications live in Git. This is the core idea behind GitOps, and in Lab 7 you will rebuild a full environment from Git alone.

---

## Optional - Use an EC2 machine as your workstation

Use this only if you cannot install tools on your laptop, for example on a locked-down office machine.

1. In the AWS Console, open **IAM**, then **Roles**, then **Create role**. Choose **AWS service** and **EC2**, attach **AdministratorAccess**, and name it `gitops-lab-workstation`.
2. Open **EC2** and click **Launch instance**.
   - Name: `gitops-workstation`
   - Image: Amazon Linux 2023
   - Instance type: t3.small
   - Key pair: create a new one or choose an existing one
   - Network: allow SSH
   - Advanced details, IAM instance profile: `gitops-lab-workstation`
3. Launch the instance, select it, and click **Connect**, then **EC2 Instance Connect**.
4. In the browser terminal, run `sudo dnf install -y git`, then the Linux commands from Part 1 Option C.
5. Skip `aws configure`. The IAM role gives the machine AWS access. Run `aws configure set region ap-south-1` only.
6. Continue from Part 3.

**Concept: IAM role instead of access keys**
An EC2 instance with an IAM role gets short-lived credentials automatically. There are no keys to copy, leak or rotate. This is the recommended way for anything running inside AWS to call AWS.

Stop this instance when you are not using it, and terminate it when the course is finished.

---

## Troubleshooting

| What you see | Cause and fix |
|---|---|
| command not found after installing | Close and reopen the terminal. On Windows, make sure you are in Git Bash |
| eksctl not found on Windows | Check that `~/bin/eksctl.exe` exists and run `source ~/.bashrc` |
| An error occurred (InvalidClientTokenId) | Wrong access key. Run `aws configure` again |
| eksctl fails with an AWS limit error | Your account has hit an AWS service limit, often on VPCs or Elastic IPs. Delete unused ones or try another region in `cluster/eks-cluster.yaml` |
| eksctl stopped halfway | Run `eksctl delete cluster -f cluster/eks-cluster.yaml`, wait for it to finish, then create again |
| kubectl says connection refused or localhost:8080 | kubeconfig is missing. Run `aws eks update-kubeconfig --name gitops-lab --region ap-south-1` |
| PVC stays Pending | Check that the ebs-csi pods are Running and gp3 shows as default |
| git push asks for a password and fails | GitHub no longer accepts passwords. Sign in through the browser window, or use a personal access token |
| git push says permission denied to discover-devops | You cloned my repository instead of your fork. Clone your fork again |

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

See you in Lab 1, where Argo CD deploys your first application straight from Git.

**Rahul Chaubey**
