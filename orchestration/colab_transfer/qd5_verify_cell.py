# Q-D5 verification cell for Google Colab (SYNTHETIC data only; nothing here reads real data).
# Paste into one Colab cell and run; it asks you to upload qd5_backend_2026-10-21.tar.gz from orchestration/colab_transfer/.
import hashlib, os, subprocess, tarfile, pathlib
from google.colab import files

EXPECTED = "4c3e2e5ad6f73e4d3a7f0da9ef99e983534adff306919937bad1f749969fdefb"
up = files.upload()
name = next(iter(up))
digest = hashlib.sha256(up[name]).hexdigest()
print("archive sha256", digest, "MATCH" if digest == EXPECTED else "MISMATCH - stop")
assert digest == EXPECTED
work = pathlib.Path("/content/qd5"); work.mkdir(exist_ok=True)
pathlib.Path(work / name).write_bytes(up[name])
with tarfile.open(work / name) as t:
    t.extractall(work, filter="data")

def run(*args):
    r = subprocess.run(["python", "-W", "error::ResourceWarning", "-m", "unittest", *args],
                       cwd=work / "backend", env={**os.environ, "PYTHONPATH": "src"}, capture_output=True, text=True)
    print(" ".join(args), "-> exit", r.returncode); print(r.stderr[-4000:])

run("tests.unit.test_quote_store", "-v")                 # targeted: the 13 new Q-D5 tests
run("tests.unit.test_architecture_imports")              # import direction (storage stays downstream)
run("discover", "-s", "tests", "-t", ".")                # full backend suite (278 before Q-D5 + 13 new = 291 expected)
