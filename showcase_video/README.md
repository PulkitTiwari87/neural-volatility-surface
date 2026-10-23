# showcase_video

**Status:** `IMPLEMENTED` as a presentation artefact (60 s, 1920x1080, 30 fps). It is not research code and not part of the product; nothing in `backend/`, `frontend/` or the research results was changed to make it.

A cinematic showcase of the project, rendered from the repository's own data and interface. It claims nothing the project does not already record (see [README.md](../README.md#project-status), [KNOWN_LIMITATIONS](../docs/research/KNOWN_LIMITATIONS.md)).

## What is real, and what is illustrative

| On screen | Source | Label in the video |
|---|---|---|
| Hero 3D surface, axes, ticks, contours, node markers | `demo_runs/spy_store` run (derived surfaces only), SPY end-of-day options, **2022-06-16**, a date with no missing cell: 45 observed nodes and 9 interpolated in tenor (the 60-day row), 6 tenors x 9 log-moneyness nodes, IV in vol points, T = days/365 | "REAL DATA, SPY end-of-day options, 2022-06-16, backtest only", node counts, "mesh smoothed between nodes for display" |
| Mesh between the nodes | Monotone cubic (PCHIP) interpolation of the nodes, for drawing only; every node is reproduced exactly (asserted in `build_data.py`). Tenor nodes are evenly spaced, as in the application's 3D tab | same label |
| Neural network scene | **Illustrative**: layer sizes and connections are invented for the picture; the input nodes are the real surface's 54 cells; the output is a miniature copy of the same surface | "ILLUSTRATIVE, not the architecture or the output of any trained model" |
| API payload, manifest lineage, guardrail text | Verbatim excerpts of the local API's output for this date, `manifest.json`, `guardrails.md`, `CLAUDE.md` (long strings shortened with an ellipsis) | file/route named in each panel header |
| "40 passed in 81.68s" | `pytest tests/scientific` in `backend/`, run on 2026-10-21 on this machine | panel header names the suite |
| Application screens | Screenshots of `frontend/index.html` served by the local research API on the same run | "APPLICATION CAPTURE, local research API, SPY end-of-day run, backtest only" |
| Status chips (IMPLEMENTED, UNSUPPORTED, NOT VALIDATED, PENDING) | Taken from the README status table | n/a |

No forecast, accuracy, profit, speed or validation figure appears. The only model statement is that engineering readiness is not scientific validation.

The data are the hosted SPY run published under owner override DEC-002-B; the upstream licence is **not** verified (see [decision.md](../decision.md)). Publishing this video is a separate act that falls under the same unresolved licence question.

## Rebuild

Needs Node >= 22, Google Chrome, ffmpeg, and Python with numpy and scipy. Nothing is added to the project's dependencies; the capture script talks to Chrome over its DevTools protocol using Node's built-in WebSocket.

```text
# 1. start the local API on the SPY run
PYTHONPATH=backend/src python -m volatility_lab.api.server --root demo_runs/spy_store/datasets --port 8791

# 2. data for the page (reads panel.npz, manifest.json and the API)
cd showcase_video && python -I build_data.py --date 2022-06-16 --api http://127.0.0.1:8791

# 3. application screenshots (out/shots/*.png; see render.mjs `shot`)
node render.mjs shot "http://127.0.0.1:8791/#/workbench/explorer?run=<run id>&i=3111&view=3d" out/shots/explorer3d.png 1600 1450 2 4500
#    landing.png (1600x1000, click `.themebtn` for the dark theme) and heatmap.png (1600x1250, view=heatmap) likewise

# 4. frames (deterministic: a pure function of time), audio cues, audio, encode
node render.mjs frames <dir> 0 1800
node render.mjs events out/events.json && python -I audio.py out/events.json out/audio.wav
ffmpeg -framerate 30 -i <dir>/f_%05d.png -i out/audio.wav -vf "scale=in_range=full:out_range=tv:out_color_matrix=bt709,format=yuv420p" \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 -c:v libx264 -preset slow -crf 14 -x264-params aq-mode=3 \
  -c:a aac -b:a 192k -movflags +faststart out/neural-volatility-surface-showcase.mp4
```

Files: `build_data.py` (data export), `engine.js` (3D renderer on a 2D canvas), `scenes.js` (timeline of the seven scenes and the camera paths), `index.html` (page and styles), `render.mjs` (Chrome capture), `audio.py` (original soundtrack, synthesised, no samples). `out/` is git-ignored.

Not done: no voice-over (the brief made it optional), no vertical 9:16 recomposition, and the soundtrack was checked numerically and by spectrogram, not by ear.
