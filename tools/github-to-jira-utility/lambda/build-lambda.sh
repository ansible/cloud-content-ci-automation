#!/bin/bash
# Build Lambda deployment package for github-jira: Python 3.14, Arm64.
# Uses Podman or Docker so native deps are built for Lambda's Linux ARM64 environment.
set -e
cd "$(dirname "$0")"
rm -rf package deploy.zip

CONTAINER_CMD=""
command -v podman &>/dev/null && CONTAINER_CMD=podman
command -v docker &>/dev/null && CONTAINER_CMD="${CONTAINER_CMD:-docker}"

if [ -n "$CONTAINER_CMD" ]; then
  echo "Building with $CONTAINER_CMD (Python 3.14, linux/arm64) for Lambda..."
  # --platform linux/arm64: build for Lambda Arm64
  if ! $CONTAINER_CMD run --rm --platform linux/arm64 --entrypoint bash -v "$(pwd)":/out -w /out public.ecr.aws/lambda/python:3.14 \
    -c 'pip install -r requirements.txt -t package && python3 -c "
import zipfile, os
with zipfile.ZipFile(\"deploy.zip\", \"w\", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(\"package\"):
        for f in files:
            path = os.path.join(root, f)
            zf.write(path, os.path.relpath(path, \"package\"))
    zf.write(\"handler.py\", \"handler.py\")
"'; then
    if [ "$CONTAINER_CMD" = podman ]; then
      echo "Tip: On macOS, ensure the Podman VM is running: podman machine start"
    fi
    exit 1
  fi
else
  echo "Building locally (must be Linux arm64 for this Lambda; or use Podman/Docker)."
  pip install -r requirements.txt -t package
  cd package && zip -r ../deploy.zip . && cd ..
  zip -g deploy.zip handler.py
fi

echo "Built deploy.zip ($(wc -c < deploy.zip) bytes)"
