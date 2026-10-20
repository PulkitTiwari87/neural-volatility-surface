"""Phase F mechanical audit (IMPLEMENTATION_PLAN Phase F "Tests/validation"). Standard library only, read-only.

    python scripts/foundation_audit.py [--json OUT]    # OUT must not exist

Checks: required files/dirs exist and are non-trivial; relative Markdown links resolve; requirement / decision /
guardrail / ADR IDs that are referenced are defined; no obvious secrets; no data tracked by Git beyond
placeholders; decision-register status counts. Exit code 1 if any hard check fails. This is a *mechanical*
audit: it cannot judge whether documents are correct, only whether they are consistent and present.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = ["README.md", "CLAUDE.md", "architecture.md", "design.md", "decision.md", "guardrails.md", "PR.md",
                  "IMPLEMENTATION_PLAN.md", "CHANGELOG.md", "CONTRIBUTING.md",
                  "NEURAL_VOLATILITY_SURFACE_FORECASTING_LAB_MASTER_PLAN.md", "docs/README.md"]
REQUIRED_DIRS = ["docs/architecture", "docs/data", "docs/design", "docs/engineering", "docs/operations",
                 "docs/planning", "docs/project", "docs/research", "docs/templates", "backend", "frontend",
                 "configs", "data", "experiments", "notebooks", "scripts", "tests", "artifacts", ".github"]
SKIP_DIRS = {".git", "node_modules", "__pycache__", "scratch", ".venv"}
MIN_BYTES = 200
SECRET = re.compile(r"(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
                    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|"
                    r"(?i:(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9/+_\-]{16,}['\"]))")
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+?)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^(```|~~~)")


def md_files():
    for p in ROOT.rglob("*.md"):
        if not SKIP_DIRS & set(p.relative_to(ROOT).parts):
            yield p


def strip_code(text: str) -> str:
    out, fenced = [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            fenced = not fenced
            continue
        if not fenced:
            out.append(re.sub(r"`[^`]*`", "", line))
    return "\n".join(out)


def check_required():
    miss = [f for f in REQUIRED_FILES if not (ROOT / f).is_file()] + [d for d in REQUIRED_DIRS if not (ROOT / d).is_dir()]
    small = [f for f in REQUIRED_FILES if (ROOT / f).is_file() and (ROOT / f).stat().st_size < MIN_BYTES]
    return {"missing": miss, "trivial": small}


def exists_exact_case(path: Path) -> bool:
    """True if ``path`` exists with exactly this spelling, even on a case-insensitive file system (Windows, macOS):
    a link that only resolves there would break on the Linux CI runner."""
    path = Path(os.path.normpath(path))      # lexical only: resolve() would silently canonicalise the case on Windows
    if not path.exists():
        return False
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return True  # outside the repository: not our concern
    cur = ROOT
    for part in rel.parts:
        if part not in {c.name for c in cur.iterdir()}:
            return False
        cur = cur / part
    return True


def check_links():
    broken, total = [], 0
    for p in md_files():
        for t in LINK.findall(strip_code(p.read_text(encoding="utf-8", errors="replace"))):
            if re.match(r"^(https?:|mailto:|#)", t):
                continue
            total += 1
            target = t.split("#")[0]
            if target and not exists_exact_case(p.parent / target):
                broken.append(f"{p.relative_to(ROOT)} -> {t}")
    return {"checked": total, "broken": broken}


def defined_ids(path: Path, pattern: str):
    return set(re.findall(pattern, path.read_text(encoding="utf-8", errors="replace"), re.M))


def check_ids():
    pr = defined_ids(ROOT / "PR.md", r"^\|\s*((?:FR|SCI|DATA|UI|NFR|SEC)-\d{3})\s*\|")
    dec = defined_ids(ROOT / "decision.md", r"^\|\s*(DEC-\d{3})\s*\|") | defined_ids(ROOT / "decision.md", r"^## (DEC-\d{3})")
    gr = defined_ids(ROOT / "guardrails.md", r"^\|\s*(GR-[A-Z]+-\d{2})\s*\|")
    adr = {m.group(1) for f in (ROOT / "docs/architecture/ADR").glob("ADR-*.md") if (m := re.match(r"(ADR-\d{4})", f.name))}
    refs = {"req": Counter(), "dec": Counter(), "gr": Counter(), "adr": Counter()}
    where = {}
    for p in md_files():
        text = strip_code(p.read_text(encoding="utf-8", errors="replace"))
        for k, pat in (("req", r"\b((?:FR|SCI|DATA|UI|NFR|SEC)-\d{3})\b"), ("dec", r"\b(DEC-\d{3})\b"),
                       ("gr", r"\b(GR-[A-Z]+-\d{2})\b"), ("adr", r"\b(ADR-\d{4})\b")):
            for i in re.findall(pat, text):
                refs[k][i] += 1
                where.setdefault((k, i), str(p.relative_to(ROOT)))
    defined = {"req": pr, "dec": dec, "gr": gr, "adr": adr}
    undefined = {k: sorted(f"{i} (e.g. {where[(k, i)]})" for i in refs[k] if i not in defined[k]) for k in refs}
    return {"defined": {k: len(v) for k, v in defined.items()}, "undefined_references": undefined}


def check_secrets():
    hits = []
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if p.is_dir() or SKIP_DIRS & set(rel.parts) or p.stat().st_size > 5_000_000:
            continue
        if p.suffix.lower() in {".npz", ".npy", ".pt", ".parquet", ".png", ".jpg", ".gz", ".zip", ".pyc"}:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in SECRET.finditer(text):
            hits.append(f"{rel}: {m.group(0)[:12]}...")
    return {"hits": hits}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()


def check_data_and_env():
    tracked_data = [f for f in git("ls-files", "data", "artifacts") if Path(f).name not in {"README.md", ".gitkeep"}]
    ignore = (ROOT / ".gitignore").read_text() if (ROOT / ".gitignore").is_file() else ""
    return {"tracked_data_files": tracked_data, "gitignore_covers_env": ".env" in ignore,
            "tracked_env_files": [f for f in git("ls-files") if re.search(r"(^|/)\.env($|\.)", f) and not f.endswith(".example")]}


def check_decisions():
    rows = re.findall(r"^\|\s*(DEC-\d{3})\s*\|[^|]*\|\s*([^|]*?)\s*\|", (ROOT / "decision.md").read_text(encoding="utf-8"), re.M)
    plain = {i: s.replace("*", "").strip().upper() for i, s in rows}   # statuses are often bold: "**DECIDED (option A) ..."
    return {"n": len(rows), "decided": [i for i, s in plain.items() if s.startswith(("DECIDED", "OWNER DECISION"))],
            "interim": [i for i, s in plain.items() if s.startswith("INTERIM")],
            "status_by_id": {i: s for i, s in rows}}


def check_status_claims():
    """Invariants between the status documents and the repository (not just 'files exist')."""
    problems = []
    plan = (ROOT / "IMPLEMENTATION_PLAN.md").read_text(encoding="utf-8")
    phases = dict(re.findall(r"^\|\s*(F|\d)\s*\|[^|]*\|\s*([^|]*?)\s*\|", plan, re.M))
    for ph, status in phases.items():
        if ph != "F" and re.search(r"GATE_PASSED|gate\s+passed|\bgate\s+MET\b", status, re.I) and "not" not in status.lower():
            problems.append(f"phase {ph} is described as gate-passed in IMPLEMENTATION_PLAN.md; only the owner may do that")
    src = ROOT / "backend" / "src"
    has_code = src.is_dir() and any(p.stat().st_size > 0 for p in src.rglob("*.py"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if has_code and re.search(r"\(none exist\)|NOT IMPLEMENTED, NOT VALIDATED", readme):
        problems.append("README.md says product code / neural work does not exist, but backend/src contains Python code")
    ms = ROOT / "docs" / "engineering" / "MODEL_STATUS.json"
    if ms.is_file():
        data = json.loads(ms.read_text(encoding="utf-8"))
        if data.get("status") == "complete" and not data.get("confirmed_by"):
            problems.append("MODEL_STATUS.json is 'complete' without confirmed_by (owner confirmation)")
    return {"phases_in_plan": sorted(phases), "problems": problems}


def main(out):
    report = {"required": check_required(), "links": check_links(), "ids": check_ids(), "secrets": check_secrets(),
              "data_and_env": check_data_and_env(), "decisions": check_decisions(), "status_claims": check_status_claims()}
    hard = (report["required"]["missing"] or report["links"]["broken"] or report["secrets"]["hits"]
            or report["data_and_env"]["tracked_data_files"] or report["data_and_env"]["tracked_env_files"]
            or any(report["ids"]["undefined_references"].values()) or report["status_claims"]["problems"])
    report["hard_failures"] = bool(hard)
    text = json.dumps(report, indent=1)
    print(text)
    if out:
        if out.exists():
            raise SystemExit(f"refusing to overwrite {out}")
        out.write_text(text, encoding="utf-8")
    sys.exit(1 if hard else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    main(ap.parse_args().json)
