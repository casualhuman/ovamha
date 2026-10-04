"""Publish the hosted demo to Hugging Face Spaces (needs `hf auth login` and a PRO account).

    .venv/bin/python scripts/deploy_spaces.py            # app + FHIR hub
"""
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
USER = "r8086"
api = HfApi()

# FHIR hub (HAPI)
api.create_repo(f"{USER}/ovamha-fhir", repo_type="space", space_sdk="docker", exist_ok=True)
api.upload_folder(repo_id=f"{USER}/ovamha-fhir", repo_type="space", folder_path=str(ROOT / "deploy/hf-fhir"),
                  commit_message="Deploy HAPI FHIR demo hub")

# App: stage only what the image needs (no tests, data, audio or tools)
with tempfile.TemporaryDirectory() as tmp:
    stage = Path(tmp)
    for f in ("Dockerfile", "README.md"):
        shutil.copy(ROOT / "deploy/hf-app" / f, stage / f)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "_*.wav", "*.wav")
    shutil.copytree(ROOT / "apps/prototype/src", stage / "apps/prototype/src", ignore=ignore)
    shutil.copytree(ROOT / "apps/prototype/web", stage / "apps/prototype/web", ignore=ignore)
    shutil.copytree(ROOT / "content", stage / "content", ignore=ignore)
    api.create_repo(f"{USER}/ovamha", repo_type="space", space_sdk="docker", exist_ok=True)
    api.upload_folder(repo_id=f"{USER}/ovamha", repo_type="space", folder_path=str(stage), commit_message="Deploy Ovamha demo")
print(f"App:  https://{USER}-ovamha.hf.space\nFHIR: https://{USER}-ovamha-fhir.hf.space/fhir/metadata")
