# DevSecOps Task API

Projet DevSecOps simple pour une Licence Professionnelle Cybersecurite :
une API Flask de gestion de taches, containerisee avec Docker, testee et
scannee dans GitHub Actions, puis deployable en local sur Kubernetes.

## Fichiers du projet

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
```

## API

- `GET /health` : etat de sante.
- `GET /api/tasks` : liste des taches.
- `POST /api/tasks` : creation d'une tache.
- `GET /api/tasks/<id>` : lecture d'une tache.
- `PUT /api/tasks/<id>` : modification d'une tache.
- `DELETE /api/tasks/<id>` : suppression d'une tache.

Exemple :

```json
{
  "title": "Scanner l'image Docker",
  "description": "Lancer Trivy dans la CI",
  "status": "todo",
  "priority": "medium"
}
```

## Lancer en local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

Sous PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

## Tests et scans locaux

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

Bonnes pratiques :

- image legere `python:3.12-slim` ;
- utilisateur non-root ;
- pas de secret dans l'image ;
- configuration par variables d'environnement.

## CI/CD GitHub Actions

Le workflow `.github/workflows/ci-cd.yaml` lance :

1. installation des dependances ;
2. lint ;
3. tests unitaires ;
4. scan `pip-audit` ;
5. scan Bandit ;
6. scan SAST Semgrep ;
7. build Docker ;
8. scan image Trivy ;
9. push vers GitHub Container Registry sur `main` ;
10. dry-run Kubernetes manuel.

## Kubernetes local

Les manifests sont dans `k8s/` :

- `service.yaml` : namespace, configmap, deployment et service ;
- `secret.yaml` : secret pedagogique a remplacer en production ;
- `rbac.yaml` : service account et role minimal ;
- `ingress.yaml` : ingress optionnel.

Deploiement local :

```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
kubectl -n devsecops-task-api port-forward svc/task-api-service 8080:80
curl http://localhost:8080/health
```

Pour appliquer aussi l'ingress :

```bash
APPLY_INGRESS=true ./scripts/deploy.sh
```

## Securite applicative

- Validation des champs `title`, `description`, `status`, `priority`.
- Sanitization HTML basique.
- SQLAlchemy ORM pour eviter les requetes SQL concatenees.
- Headers de securite avec Flask-Talisman.
- Rate limiting avec Flask-Limiter.
- Dependances scannees avec `pip-audit`.
- Image Docker scannee avec Trivy.

## Limites

- Pas d'authentification.
- SQLite par defaut.
- Pas de migrations de base de donnees.
- Kubernetes volontairement minimal pour rester realiste a niveau etudiant.
