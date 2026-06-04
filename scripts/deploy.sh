#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

IMAGE_NAME="${IMAGE_NAME:-devsecops-task-api:local}"
NAMESPACE="devsecops-task-api"

echo "[1/4] Build Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" .

echo "[2/4] Apply Kubernetes manifests"
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/rbac.yaml

if [[ "${APPLY_INGRESS:-false}" == "true" ]]; then
  kubectl apply -f k8s/ingress.yaml
fi

echo "[3/4] Wait for deployment"
kubectl -n "${NAMESPACE}" rollout status deployment/task-api

echo "[4/4] Local access"
echo "Run: kubectl -n ${NAMESPACE} port-forward svc/task-api-service 8080:80"
echo "Then open: http://localhost:8080/health"
