# DevSecOps Task API

Version anglaise : [README_EN.md](README_EN.md)

## Presentation

Ce projet est une API Flask que j'ai faite pour mettre en pratique une chaine DevSecOps simple.

L'idee etait de ne pas faire seulement une petite application, mais aussi de montrer tout ce qu'il y a autour :

- des tests unitaires ;
- des scans de securite ;
- une image Docker ;
- une pipeline GitHub Actions ;
- une simulation de deploiement Kubernetes.

L'API permet de gerer des taches. Chaque tache a un titre, une description, un statut et une priorite.

## Structure du projet

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

## Routes de l'API

- `GET /health` : verifier que l'API repond.
- `GET /api/tasks` : afficher toutes les taches.
- `POST /api/tasks` : creer une tache.
- `GET /api/tasks/<id>` : afficher une tache precise.
- `PUT /api/tasks/<id>` : modifier une tache.
- `DELETE /api/tasks/<id>` : supprimer une tache.

Exemple de tache :

```json
{
  "title": "Scanner l'image Docker",
  "description": "Lancer Trivy dans la CI",
  "status": "todo",
  "priority": "medium"
}
```

## Lancer le projet en local

Avec Linux ou macOS :

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

Avec PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app.app run --host 127.0.0.1 --port 5000
```

## Tests et scans

Voici les commandes que j'utilise pour verifier le projet :

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

Dans le Dockerfile, j'ai ajoute quelques points de securite :

- image de base `python:3.12-slim-bookworm` ;
- mise a jour des paquets Debian pendant le build ;
- lancement de l'application avec un utilisateur non-root ;
- pas de secret stocke dans l'image ;
- configuration possible avec des variables d'environnement.

## CI/CD

La pipeline GitHub Actions se trouve dans `.github/workflows/ci-cd.yaml`.

Elle fait les etapes suivantes :

1. installation des dependances ;
2. lint avec `flake8` ;
3. verification du formatage avec `black` ;
4. tests unitaires avec `pytest` ;
5. audit des dependances avec `pip-audit` ;
6. scan du code avec Bandit ;
7. scan SAST avec Semgrep ;
8. build de l'image Docker ;
9. scan de l'image avec Trivy ;
10. push de l'image vers GitHub Container Registry sur `main` ;
11. dry-run Kubernetes en manuel.

Pour Trivy, j'ai choisi de bloquer les vulnerabilites `HIGH` et `CRITICAL` seulement quand un correctif existe. Les vulnerabilites sans correctif disponible sont ignorees pour eviter de bloquer la CI sur quelque chose que je ne peux pas corriger directement.

## Kubernetes

Les fichiers Kubernetes sont dans le dossier `k8s/` :

- `service.yaml` : namespace, configmap, deployment et service ;
- `secret.yaml` : secret de demonstration ;
- `rbac.yaml` : service account et permissions minimales ;
- `ingress.yaml` : ingress optionnel.

Pour tester le deploiement en local :

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

J'ai ajoute plusieurs controles simples :

- validation des champs `title`, `description`, `status` et `priority` ;
- nettoyage HTML simple sur les champs texte ;
- utilisation de SQLAlchemy ORM pour eviter les requetes SQL concatenees ;
- headers de securite avec Flask-Talisman ;
- rate limiting avec Flask-Limiter ;
- scan des dependances avec `pip-audit` ;
- scan de l'image Docker avec Trivy.

## Limites

Le projet reste volontairement simple. Il n'y a pas encore :

- d'authentification ;
- de migrations de base de donnees ;
- de vraie base de donnees de production.

SQLite est utilise par defaut, et Kubernetes reste assez minimal parce que le but est surtout de montrer la logique DevSecOps.
