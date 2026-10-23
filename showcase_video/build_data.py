"""Build showcase_video/data.js from the committed SPY demo run (derived surfaces only).

Reads panel.npz of one run, picks one date with no missing cell, and writes
  - the 6 x 9 node grid (vol points) with its cell status, unchanged;
  - a display mesh: monotone (PCHIP) interpolation between the nodes, for drawing only;
  - short, verbatim excerpts of project files/API output shown in the engineering scene.
Usage: python -I build_data.py [--date 2022-06-16] [--api http://127.0.0.1:8791]
"""
import argparse, datetime as dt, json, pathlib, urllib.request
import numpy as np
from scipy.interpolate import PchipInterpolator

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUN = ROOT / "demo_runs/spy_store/datasets/187dba0b770a3976e3448cf91f49a1adc8ad5f3f1796e1aab7bb41647c6cc7d7"
EPOCH = dt.date(1970, 1, 1)

ap = argparse.ArgumentParser()
ap.add_argument("--date", default="2022-06-16")
ap.add_argument("--api", default="http://127.0.0.1:8791")
a = ap.parse_args()

p = np.load(RUN / "panel.npz", allow_pickle=False)
dates = [str(EPOCH + dt.timedelta(days=int(d))) for d in p["dates"]]
i = dates.index(a.date)
status = p["status"][i]
assert (status != 0).all(), "chosen date has a missing cell"
iv = p["iv"][i] * 100.0  # decimal -> vol points, display boundary only
k_nodes = p["k_nodes"].astype(float)
tenors = [int(t) for t in p["tenor_days"]]

k_fine = np.round(np.linspace(k_nodes[0], k_nodes[-1], 113), 6)
rows = np.stack([PchipInterpolator(k_nodes, iv[j])(k_fine) for j in range(iv.shape[0])])
t_fine = np.linspace(0, iv.shape[0] - 1, 61)
mesh = np.stack([PchipInterpolator(np.arange(iv.shape[0]), rows[:, c])(t_fine) for c in range(rows.shape[1])], axis=1)
# every node must be reproduced exactly by the display mesh
for j in range(iv.shape[0]):
    for c, k in enumerate(k_nodes):
        cc = int(np.argmin(abs(k_fine - k)))
        assert abs(mesh[j * 12, cc] - iv[j, c]) < 1e-9 and abs(k_fine[cc] - k) < 1e-9

def get(path):
    with urllib.request.urlopen(a.api + path, timeout=10) as r:
        return json.load(r)

rid = RUN.name
runs = get("/api/runs")
surf = get(f"/api/runs/{rid}/surface/{i}")
detail = get(f"/api/runs/{rid}")
man = json.load(open(RUN / "manifest.json"))

def short(h): return h[:12] + "…"
excerpt_api = {
    "GET": f"/api/runs/{short(rid)}/surface/{i}",
    "origin": surf["origin"], "description": surf["description"], "index": surf["index"], "date": surf["date"],
    "spot": surf["spot"], "n_quotes": surf["n_quotes"], "tenor_days": surf["tenor_days"], "k_nodes": surf["k_nodes"],
    "iv_units": surf["iv_units"], "status_labels": detail["status_labels"],
}
excerpt_lineage = {
    "version_id": short(detail["lineage"]["version_id"]), "config_sha256": short(detail["lineage"]["config_sha256"]),
    "inputs": [{"name": x["name"], "bytes": x["bytes"], "sha256": short(x["sha256"])} for x in detail["lineage"]["inputs"][:3]] + ["… 14 files"],
    "split": man["config"]["split"], "surface": {"tenor_days": man["config"]["surface"]["tenor_days"], "tol_obs_days": man["config"]["surface"]["tol_obs_days"]},
}
assert len(detail["lineage"]["inputs"]) == 14

out = {
    "date": a.date, "index": i, "spot": float(p["spot"][i]), "nQuotes": int(p["n_quotes"][i]),
    "tenorDays": tenors, "kNodes": k_nodes.tolist(), "iv": np.round(iv, 4).tolist(), "status": status.astype(int).tolist(),
    "mesh": {"kGrid": k_fine.tolist(), "nj": int(mesh.shape[0]), "ni": int(mesh.shape[1]), "z": np.round(mesh, 4).tolist()},
    "statusCounts": detail["status_counts"], "nDates": len(dates), "firstDate": dates[0], "lastDate": dates[-1],
    "excerpts": {"api": excerpt_api, "lineage": excerpt_lineage, "runs": runs},
}
(pathlib.Path(__file__).parent / "data.js").write_text("window.NVS = " + json.dumps(out, separators=(",", ":")) + ";\n", encoding="utf-8")
print("wrote data.js", a.date, "idx", i, "iv", round(iv.min(), 2), round(iv.max(), 2), "obs", int((status == 3).sum()), "interpT", int((status == 1).sum()))
