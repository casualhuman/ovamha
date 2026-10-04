"""Publish the hosted demo to Hugging Face Spaces (needs `hf auth login` and a PRO account).

    .venv/bin/python scripts/deploy_spaces.py            # app + FHIR hub

Guards, so a broken build (e.g. Yoruba) never reaches the live demo:
1. only a clean checkout of exactly origin/main is deployed;
2. the full test suite (Yoruba speech guard, keywords, translations, read-back) must pass first;
3. after upload, scripts/smoke_hosted.py runs a Yoruba visit against the live app.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
USER = "r8086"
api = HfApi()


def run(*cmd: str) -> str:
    return subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


# 1. Exactly origin/main, nothing uncommitted.
run("git", "fetch", "-q", "origin", "main")
if run("git", "status", "--porcelain", "--untracked-files=no"):
    raise SystemExit("Uncommitted changes: commit and merge to main first. The live demo must match main.")
if run("git", "rev-parse", "HEAD") != run("git", "rev-parse", "origin/main"):
    raise SystemExit("This checkout is not origin/main: merge the PR, then deploy from main.")
# 2. Tests, including every Yoruba test.
if subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT).returncode != 0:
    raise SystemExit("Tests failed: not deploying.")

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
    clf = ROOT / "ml/models/danger-sign-clf"
    if not (clf / "labels.json").exists():
        raise SystemExit("Classifier not trained: run ml/textclf/train.py first (the hosted app must match the local one).")
    shutil.copytree(clf, stage / "ml/models/danger-sign-clf")
    yo = ROOT / "ml/models/whisper-small-yoruba-ct2"
    if not (yo / "model.bin").exists():
        raise SystemExit("Yoruba speech model missing: run scripts/convert_yoruba_asr.sh first (hosted Yoruba would fall back to base Whisper).")
    shutil.copytree(yo, stage / "ml/models/whisper-small-yoruba-ct2")
    api.create_repo(f"{USER}/ovamha", repo_type="space", space_sdk="docker", exist_ok=True)
    info = api.upload_folder(repo_id=f"{USER}/ovamha", repo_type="space", folder_path=str(stage),
                             commit_message=f"Deploy MaternaSave demo ({run('git', 'rev-parse', '--short', 'HEAD')})")
print(f"App:  https://{USER}-ovamha.hf.space\nFHIR: https://{USER}-ovamha-fhir.hf.space/fhir/metadata")
# 3. Smoke test the live app once the new image is up (a Yoruba visit end to end).
import time  # noqa: E402

# Wait until the Space runs the image built from this upload (not the previous one).
for _ in range(90):
    rt = api.get_space_runtime(f"{USER}/ovamha")
    if rt.stage == "RUNNING" and rt.raw.get("sha") == info.oid:
        break
    if rt.stage in ("BUILD_ERROR", "RUNTIME_ERROR"):
        raise SystemExit(f"Space failed: {rt.stage}. Check the build logs on Hugging Face.")
    time.sleep(20)
else:
    raise SystemExit("The new build did not start within 30 minutes.")
print("New build running; smoke testing the live app")
sys.exit(subprocess.run([sys.executable, str(ROOT / "scripts/smoke_hosted.py"), f"https://{USER}-ovamha.hf.space"]).returncode)
