"""Audit a prospective Git index without touching the checkout's Git metadata.

This cannot establish the real tracked files/history when .git is inaccessible.
An optional exported snapshot supports testing the exact candidate file set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, help="Export into a new empty directory")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not (root / ".gitignore").is_file():
        raise RuntimeError("Publication audit requires the source checkout's .gitignore")
    output = root / ".local/publication"
    output.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith("GIT_"):
            environment.pop(name)
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    rules = {
        "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
        "github-fine-grained-token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{40,}\b"),
        "huggingface-token": re.compile(rb"\bhf_[A-Za-z0-9]{30,}\b"),
        "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
        "absolute-user-path": re.compile(rb"/(?:home|Users)/[A-Za-z0-9_.-]+/"),
        "absolute-removable-path": re.compile(rb"/run/media/[A-Za-z0-9_.-]+/"),
        "credential-url": re.compile(rb"https?://[^/\s:@]+:[^/\s@]+@"),
    }
    forbidden = {".pth", ".pt", ".ckpt", ".bin", ".safetensors", ".onnx", ".npy", ".npz"}
    issues = []
    with tempfile.TemporaryDirectory(prefix="aidemo-publication-git-") as temporary:
        metadata = Path(temporary) / "metadata.git"
        subprocess.run(
            ["git", "init", "--bare", "--quiet", str(metadata)], env=environment, check=True
        )
        prefix = ["git", f"--git-dir={metadata}", f"--work-tree={root}"]

        def git(*arguments: str) -> bytes:
            return subprocess.check_output([*prefix, *arguments], cwd=root, env=environment)

        git("add", "--all", "--", ".")
        paths = [Path(os.fsdecode(p)) for p in git("ls-files", "-z").split(b"\0") if p]
        records = []
        for relative in paths:
            path = root / relative
            if path.is_symlink():
                issues.append({"path": str(relative), "rule": "symlink-needs-review"})
                continue
            data = path.read_bytes()
            records.append(
                {
                    "path": relative.as_posix(),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            if path.suffix in forbidden or len(data) > 5 * 1024 * 1024:
                issues.append({"path": str(relative), "rule": "model-or-large-artifact"})
            if b"\0" not in data:
                for name, pattern in rules.items():
                    if pattern.search(data):
                        # Never print potential credentials or the matched line.
                        issues.append({"path": str(relative), "rule": name})
        probes = [
            ".env",
            ".env.production",
            ".aws/credentials",
            ".codex/auth.json",
            ".agents/private.md",
            "weights/model.pth",
            "weights/model.ckpt",
            "weights/model.safetensors",
            ".local/models/model.bin",
            "outputs/result.png",
            "uploads/private.wav",
            "galleries/example/metadata.json",
            "dist/example.whl",
            ".venv/lib/python.py",
            ".coverage",
            "coverage.xml",
            "private.pem",
        ]
        check = subprocess.run(
            [*prefix, "check-ignore", "--stdin", "-z"],
            input=b"\0".join(os.fsencode(p) for p in probes) + b"\0",
            cwd=root,
            env=environment,
            capture_output=True,
            check=False,
        )
        if check.returncode not in {0, 1}:
            raise RuntimeError("git check-ignore failed")
        ignored = {os.fsdecode(p) for p in check.stdout.split(b"\0") if p}
        for path in probes:
            if path not in ignored:
                issues.append({"path": path, "rule": "missing-ignore"})
        report = {
            "scope": "prospective index; actual .git/history unavailable",
            "candidate_count": len(records),
            "candidate_bytes": sum(r["bytes"] for r in records),
            "files": records,
            "ignore_probes": len(probes),
            "issues": issues,
            "limitations": [
                "pattern scanning is not a full secret-history audit",
                "real tracked ignored files cannot be checked without real Git metadata",
            ],
        }
        (output / "files.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "files.txt").write_text("\n".join(r["path"] for r in records) + "\n")
        if args.snapshot:
            snapshot = args.snapshot.resolve()
            if snapshot == root or root.is_relative_to(snapshot):
                raise ValueError("Snapshot must not contain the source checkout")
            snapshot.mkdir(parents=True, exist_ok=True)
            if any(snapshot.iterdir()):
                raise ValueError("Snapshot destination must be empty")
            if issues:
                raise RuntimeError("Refusing snapshot with unresolved publication issues")
            git("checkout-index", "--all", f"--prefix={snapshot}{os.sep}")
        print(f"Candidates: {len(records)}; ignore probes: {len(probes)}; issues: {len(issues)}")
        for issue in issues:
            print(f"{issue['rule']}: {issue['path']}")
        if issues:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
