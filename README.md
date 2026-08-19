# DevOps Intern Final Assessment

**Name:** Yajat Prabhakar
**Date:** August 18, 2026

## Project Description

This repository contains the DevOps pipeline for the assessment.

The pipeline covers:

`Git repo` → `shell script` → `Docker image` → `CI pipeline` → `Nomad job` → `Loki logs`
---

## 1. Git & GitHub Setup

The repository contains this README and `hello.py`.

`hello.py` prints:

```text
Hello, DevOps!
```

Run it directly:

```bash
python3 hello.py
```

Output:

```text
Hello, DevOps!
```

![GitHub repository](docs/01-github-repo.png)

---

## 2. Linux & Scripting Basics

`scripts/sysinfo.sh` prints the current user, date, and disk usage.

Make it executable:

```bash
chmod +x scripts/sysinfo.sh
./scripts/sysinfo.sh
```

**Actual output:**

```text
yajat
Wed Aug 19 05:57:59 UTC 2026
Filesystem   Size  Used Avail Use% Mounted on
none         4.9G     0  4.9G   0% /usr/lib/modules/...
/dev/sdf     1007G  1.7G  954G   1% /
C:\          475G  378G   98G  80% /mnt/c
...
```

![sysinfo.sh output](docs/02-sysinfo.png)

---

## 3. Docker Basics

The `Dockerfile` uses Python 3.12-slim as the base image and runs `hello.py`.

Build the image:

```bash
docker build -t hello-devops:v1 .
```

Run it:

```bash
docker run --rm hello-devops:v1
```

Output:

```text
Hello, DevOps!
```

The image uses the `v1` tag instead of `latest`. This was required for the local Nomad setup because the Docker driver attempted to pull the `latest` image from a registry.

![Docker build and run](docs/03-docker-run.png)

---

## 4. CI/CD with GitHub Actions

The workflow is located at:

```text
.github/workflows/ci.yml
```

It runs on pushes and pull requests to `main`.

The workflow:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Runs `python hello.py`.
4. Runs `scripts/sysinfo.sh`.

The workflow status can be checked from the **Actions** tab on GitHub.

![GitHub Actions workflow runs](docs/04-ci-actions-list.png)

![CI run detail showing hello.py output](docs/04b-ci-run-detail.png)

---

## 5. Job Deployment with Nomad

The Nomad job is defined in:

```text
nomad/hello.nomad
```

It runs the Docker image created in the previous step.

### Environment

The project was initially run on Windows. The native Windows Nomad agent could not communicate with Docker Desktop when Docker Desktop was using Linux containers. The Docker driver reported as unhealthy because it was looking for the Windows-container `npipe` endpoint.

The setup was moved to WSL2 with Docker Desktop's WSL integration. Nomad could then access Docker through:

```text
unix:///var/run/docker.sock
```

No additional Docker driver configuration was needed.

### Job Type: `batch`

The assessment brief suggests:

```hcl
type = "service"
```

However, `hello.py` runs once and exits. A service job expects a long-running process, so Nomad restarted the task after each successful exit and eventually marked the allocation as failed after the restart attempts were exhausted.

The job therefore uses:

```hcl
type = "batch"
```

A successful run exits with code `0` and the allocation is reported as `complete`.

### Image Tag

The first version of the job used:

```text
hello-devops:latest
```

Nomad attempted to pull that image from a registry and returned:

```text
pull access denied ... repository does not exist
```

The image was changed to:

```text
hello-devops:v1
```

with:

```hcl
force_pull = false
```

This allowed Nomad to use the locally built image.

### Final Job File

```hcl
job "hello" {
  datacenters = ["dc1"]
  type        = "batch"

  group "hello-group" {
    count = 1

    task "hello-task" {
      driver = "docker"

      config {
        image      = "hello-devops:v1"
        force_pull = false
      }

      resources {
        cpu    = 100
        memory = 128
      }

      restart {
        attempts = 0
        mode     = "fail"
      }
    }
  }
}
```

### Prerequisites

Start a Nomad development agent:

```bash
nomad agent -dev
```

When running on Windows, the agent should be started from WSL2 so that it can access Docker Desktop.

The Docker image must also exist locally:

```bash
docker build -t hello-devops:v1 .
```

### Run the Job

```bash
nomad job run nomad/hello.nomad
nomad job status hello
```

Get the allocation ID from the job status:

```bash
nomad alloc status <alloc-id>
nomad alloc logs <alloc-id>
```

### Actual Output

```text
Client Status        = complete
Client Description   = All tasks have completed
...
Recent Events:
Time                   Type        Description
2026-08-19T06:02:19Z  Terminated  Exit Code: 0
2026-08-19T06:02:19Z  Started     Task started by client
2026-08-19T06:02:18Z  Task Setup  Building Task Directory
2026-08-19T06:02:18Z  Received    Task received by client
```

```text
$ nomad alloc logs ab069b41
Hello, DevOps!
```

![Nomad alloc status and logs](docs/05-nomad-run.png)

---

## 6. Monitoring with Grafana Loki

Loki was run locally in Docker.

The first log collection attempt used Promtail with Docker auto-discovery. It failed because of a Docker API version mismatch:

```text
client version 1.42 is too old
```

The working setup uses Docker's native Loki logging driver. Container stdout/stderr is sent directly to Loki.

The detailed setup is in:

```text
monitoring/loki_setup.txt
```

The Promtail configuration used during the initial attempt is kept in:

```text
monitoring/promtail-config.yaml
```

### Working Setup

Start Loki:

```bash
docker run -d --name=loki -p 3100:3100 grafana/loki:2.9.0 \
  -config.file=/etc/loki/local-config.yaml
```

Install the Docker logging driver:

```bash
docker plugin install grafana/loki-docker-driver:latest \
  --alias loki --grant-all-permissions
```

Run the container with the Loki logging driver:

```bash
docker run --rm --name hello-run \
  --log-driver=loki \
  --log-opt loki-url="http://host.docker.internal:3100/loki/api/v1/push" \
  hello-devops:v1
```

### Query the Logs

```bash
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={container_name="hello-run"}' \
  --data-urlencode 'limit=20' | python3 -m json.tool
```

### Actual Result

```json
"stream": {
    "container_name": "hello-run",
    "filename": "/var/log/docker/8e1940e67ea57d010f807fb5715069ad6ad3363726c0fa12655198aab5cb127d/json.log",
    "host": "docker-desktop",
    "source": "stdout"
},
"values": [
    ["1787121271009687203", "Hello, DevOps!"]
]
```

![Loki query result](docs/07-loki-query.png)

---

## 7. Extra Credit

### MLflow Tracking

`mlflow/log_experiment.py` logs:

* `learning_rate`
* `epochs`
* Accuracy for each epoch
* Loss for each epoch
* `hello.py` as an artifact

MLflow data is stored under:

```text
~/mlflow-runs/devops-intern-final
```

The storage is kept on the native Linux filesystem instead of `/mnt/c/...`. This avoids the file-copying permission issue encountered when MLflow was run from a Windows-mounted WSL2 path.

Run it with:

```bash
cd mlflow
sudo apt install -y python3-pip
pip3 install -r requirements.txt --break-system-packages
python3 log_experiment.py
```

**Actual output:**

```text
epoch=1 accuracy=0.561 loss=0.8564
epoch=2 accuracy=0.6577 loss=0.694
epoch=3 accuracy=0.7553 loss=0.5627
epoch=4 accuracy=0.8262 loss=0.398
epoch=5 accuracy=0.8891 loss=0.2358
MLflow run complete.
```

![MLflow run output](docs/06-mlflow-run.png)

View the run:

```bash
mlflow ui --backend-store-uri sqlite:///$HOME/mlflow-runs/devops-intern-final/mlflow.db
```

Then open:

```text
http://localhost:5000
```

and select:

```text
devops-intern-final-demo
```

### VM Deployment (VirtualBox)

A VirtualBox VM was created with Vagrant to run the Docker/Nomad job separately from WSL2.

The Vagrant configuration is in:

```text
vm/Vagrantfile
```

The VM setup notes and troubleshooting details are in:

```text
vm/vm_setup_notes.txt
```

One issue encountered during a rebuild was a VirtualBox/Hyper-V virtualization conflict that caused boot/SSH timeouts. Enabling VirtualBox's Hyper-V paravirtualization interface resolved the issue.

**Actual output from the VM:**

```text
Task Events:
Time                   Type        Description
2026-08-19T07:30:14Z  Terminated  Exit Code: 0
2026-08-19T07:30:14Z  Started     Task started by client
2026-08-19T07:30:12Z  Task Setup  Building Task Directory
2026-08-19T07:30:12Z  Received    Task received by client

$ nomad alloc logs 9600fd36
Hello, DevOps!
```

![Nomad run inside the Vagrant/VirtualBox VM](docs/08-vm-nomad-run.png)

---

## Repository Structure

```text
.
├── README.md
├── hello.py
├── Dockerfile
├── scripts/
│   └── sysinfo.sh
├── .github/
│   └── workflows/
│       └── ci.yml
├── nomad/
│   └── hello.nomad
├── monitoring/
│   ├── loki_setup.txt
│   └── promtail-config.yaml
├── mlflow/
│   ├── log_experiment.py
│   └── requirements.txt
├── vm/
│   ├── Vagrantfile
│   └── vm_setup_notes.txt
└── docs/
    ├── 01-github-repo.png
    ├── 02-sysinfo.png
    ├── 03-docker-run.png
    ├── 04-ci-actions-list.png
    ├── 04b-ci-run-detail.png
    ├── 05-nomad-run.png
    ├── 06-mlflow-run.png
    ├── 07-loki-query.png
    └── 08-vm-nomad-run.png
```
