"""Upload the build files with GitHub's API, with progress and bounded waits."""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote


FILES = (
    "README.txt",
    ".gitignore",
    "scripts/verify_installer.py",
    "scripts/upload_repository.py",
    "scripts/prepare_build_kit.py",
    "Local MIDI-macOS-BuildKit_2.zip",
    ".github/workflows/build-apple-silicon.yml",
)


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()


def request(gh, arguments, timeout):
    process = subprocess.Popen(
        [gh, "api", "--hostname", "github.com", *arguments],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    deadline = time.monotonic() + timeout
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stop(process)
                raise RuntimeError(
                    "GitHub did not respond within " + str(timeout)
                    + " seconds. The build has not been started. "
                    "You can reopen the launcher to resume the upload."
                )
            try:
                stdout, stderr = process.communicate(timeout=min(15, remaining))
                return process.returncode, stdout.strip(), stderr.strip()
            except subprocess.TimeoutExpired:
                if time.monotonic() < deadline:
                    print("  Still waiting for GitHub's response...", flush=True)
    except BaseException:
        stop(process)
        raise


def upload(root, repository, gh, timeout):
    if not re.fullmatch(r"[A-Za-z0-9-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Invalid GitHub repository name")
    for index, name in enumerate(FILES, 1):
        print("Uploading " + str(index) + "/" + str(len(FILES)) + ": " + name, flush=True)
        content = (root / name).read_bytes()
        endpoint = "repos/" + repository + "/contents/" + quote(name, safe="/")
        status, existing_sha, error = request(
            gh, [endpoint, "--method", "GET", "-H", "Accept: application/vnd.github.object+json",
                 "-f", "ref=main", "--jq", ".sha"], timeout
        )
        if status:
            if "HTTP 404" not in error:
                raise RuntimeError(error or "GitHub could not check the existing file")
            existing_sha = None
        local_sha = hashlib.sha1(
            b"blob " + str(len(content)).encode("ascii") + b"\0" + content
        ).hexdigest()
        if existing_sha == local_sha:
            print("  Already uploaded.", flush=True)
            continue
        payload = {
            "message": "Prepare Apple Silicon build: " + name,
            "branch": "main",
            "content": base64.b64encode(content).decode("ascii"),
        }
        if existing_sha:
            payload["sha"] = existing_sha
        with tempfile.TemporaryDirectory(prefix="local-midi-upload-") as directory:
            body = Path(directory) / "request.json"
            body.write_text(json.dumps(payload), encoding="utf-8")
            status, _, error = request(
                gh, [endpoint, "--method", "PUT", "--input", str(body), "--jq", ".commit.sha"], timeout
            )
        if status:
            raise RuntimeError(error or "GitHub did not confirm the upload")
        print("  Uploaded.", flush=True)
    print("GitHub confirmed all build files are uploaded.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--gh", required=True)
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        upload(Path(__file__).resolve().parents[1], args.repo, args.gh, args.timeout)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, "Upload failed: " + str(error) + "\n")
    except KeyboardInterrupt:
        parser.exit(130, "\nUpload stopped. Reopen the launcher to resume.\n")
