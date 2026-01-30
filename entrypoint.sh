#!/usr/bin/env bash
set -euo pipefail

cd /workspace/project

# Install required Python packages (if missing)
python - <<'PY'
import sys
pkgs = ["pandas","numpy","scikit-learn","shap","openpyxl"]
import importlib
missing = []
for p in pkgs:
    try:
        importlib.import_module(p)
    except Exception:
        missing.append(p)
print("Missing packages:", missing)
PY

if grep -q "Missing packages: \[\]" <(python - <<'PY'
import sys
pkgs = ["pandas","numpy","scikit-learn","shap","openpyxl"]
import importlib
missing = []
for p in pkgs:
    try:
        importlib.import_module(p)
    except Exception:
        missing.append(p)
print("Missing packages:", missing)
PY
); then
  echo "All packages present."
else
  echo "Installing missing packages..."
  pip install pandas numpy scikit-learn shap openpyxl
fi

python -m src.main
