# DevSecOps Task API

French version: [README.md](README.md)

## Presentation

This project is a Flask API I made to practice a simple DevSecOps workflow.

The goal was not only to create a small application, but also to show the steps around it:

- unit tests;
- security scans;
- a Docker image;
- a GitHub Actions pipeline;
- a Kubernetes deployment simulation.

The API manages tasks. Each task has a title, a description, a status, and a priority.

## Project Structure

```text
.dockerignore
.gitignore
.github/workflows/ci-cd.yaml
app/app.py
app/__init__.py
scripts/deploy.sh
Dockerfile
requirements.txt
tests/test_app.py
k8s/ingress.yaml
k8s/rbac.yaml
k8s/secret.yaml
k8s/service.yaml
README.md
README_EN.md
```

## API Routes

- `GET /health`: checks if the API is running.
- `GET /api/tasks`: lists all tasks.
- `POST /api/tasks`: creates a task.
- `GET /api/tasks/<id>`: returns one task.
- `PUT /api/tasks/<id>`: updates one task.
- `DELETE /api/tasks/<id>`: deletes one task.

Example task:

```json
{
  "title": "Scan the Docker image",
  "description": "Run Trivy in the CI",
  "status": "todo",
  "priority": "medium"
}
```

## Run Locally

With Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

With PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

## Tests and Scans

These are the commands I use to check the project:

```bash
pytest -q
flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
black --check app tests
pip-audit -r requirements.txt
bandit -r app -ll
```

## Docker

```bash
docker build -t devsecops-task-api:local .
docker run --rm -p 5000:5000 devsecops-task-api:local
```

In the Dockerfile, I added a few security points:

- `python:3.12-slim-bookworm` base image;
- Debian packages are upgraded during the build;
- the application runs with a non-root user;
- no secret is stored in the image;
- configuration can be done with environment variables.

## CI/CD

The GitHub Actions pipeline is in `.github/workflows/ci-cd.yaml`.

It runs these steps:

1. dependency installation;
2. lint with `flake8`;
3. formatting check with `black`;
4. unit tests with `pytest`;
5. dependency audit with `pip-audit`;
6. code scan with Bandit;
7. SAST scan with Semgrep;
8. Docker image build;
9. Docker image scan with Trivy;
10. image push to GitHub Container Registry on `main`;
11. manual Kubernetes dry-run.

For Trivy, I decided to block `HIGH` and `CRITICAL` vulnerabilities only when a fix exists. Vulnerabilities without an available fix are ignored so the CI does not fail on something I cannot patch directly.

## Kubernetes

The Kubernetes files are in the `k8s/` folder:

- `service.yaml`: namespace, configmap, deployment, and service;
- `secret.yaml`: demo secret;
- `rbac.yaml`: service account and minimal permissions;
- `ingress.yaml`: optional ingress.

To test the deployment locally:

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
kubectl -n devsecops-task-api port-forward svc/task-api-service 8080:80
curl http://localhost:8080/health
```

To apply the ingress too:

```bash
APPLY_INGRESS=true ./scripts/deploy.sh
```

## Application Security

I added several simple controls:

- validation for `title`, `description`, `status`, and `priority`;
- basic HTML cleanup on text fields;
- SQLAlchemy ORM to avoid concatenated SQL queries;
- security headers with Flask-Talisman;
- rate limiting with Flask-Limiter;
- dependency scan with `pip-audit`;
- Docker image scan with Trivy.

## Limits

The project is intentionally simple. It does not have yet:

- authentication;
- database migrations;
- a real production database.

SQLite is used by default, and Kubernetes stays quite minimal because the main goal is to show the DevSecOps logic.
