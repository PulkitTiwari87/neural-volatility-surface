"use strict";
// Timeline of the 60 s showcase. renderFrame(t) is a pure function of t (seconds); no clocks, no randomness.
//  0-8 emergence | 8-20 mathematics | 20-30 neural (illustrative) | 30-40 engineering | 40-48 interface | 48-55 evidence | 55-60 hero + title
(function () {
  const { W, H, ctx, clamp, lerp, sstep, eio, eout, K, camAt, makeCam, drawBackground, post, drawBox, drawAxisLabels, drawSurface, hash, NODE_T, label, proj, N, nodeW, LUT } = E;
  const ui = document.getElementById("ui");
  const ALL = [];
  function mk(id, cls, html, css) { const d = document.createElement("div"); d.id = id; d.className = cls; d.innerHTML = html; if (css) d.style.cssText = css; ui.appendChild(d); ALL.push(d); return d; }
  const trap = (t, a, b, fi = .7, fo = .7) => clamp((t - a) / fi) * clamp((b - t) / fo);
  const put = (el, o, dy = 0, dx = 0) => { el.style.opacity = o.toFixed(3); el.style.transform = `translate3d(${dx.toFixed(1)}px,${dy.toFixed(1)}px,0)`; };
  const nObs = N.status.flat().filter(s => s === 3).length, nIntT = N.status.flat().filter(s => s === 1).length;
  const MUTED = "left:64px;bottom:44px;font-size:16px;letter-spacing:.08em;color:#8db4d2;line-height:1.6;text-shadow:0 1px 8px #000";

  // ---------- cue times shared with the audio synth ----------
  const EVENTS = { nodeTimes: NODE_T, impacts: [7.0, 56.4], beats: [30.0, 32.5, 35.0, 37.5], scenes: [0, 8, 20, 30, 40, 48, 55, 60], bpm: 96 };
  window.EVENTS = EVENTS;

  // ================= DOM: scenes 1, 2, 7 =================
  const lab = mk("lab", "t", `<b>REAL DATA</b> &nbsp;·&nbsp; SPY END-OF-DAY OPTIONS &nbsp;·&nbsp; ${N.date} &nbsp;·&nbsp; BACKTEST ONLY<br>${nObs} observed + ${nIntT} interpolated-in-tenor nodes &nbsp;·&nbsp; mesh smoothed between nodes for display`);
  const legend = mk("legend", "t", `<span class="dot"></span>OBSERVED NODE<br><span class="ring"></span>INTERPOLATED IN TENOR`);
  const l1 = mk("l1", "t hl", "Markets are not<br>one-dimensional.", "left:1140px;top:84px;font-size:44px");
  const l1b = mk("l1b", "t sub", "Volatility varies across strikes<br>and maturities.", "left:1140px;top:250px");
  const axT = {
    x: mk("axx", "t", `<div class="hl cy" style="font-size:40px">Strike</div><div class="sub" style="font-size:25px;margin-top:8px">forward log-moneyness k = ln(K/F), −0.20 to +0.08</div>`, "left:1140px;top:84px"),
    y: mk("axy", "t", `<div class="hl cy" style="font-size:40px">Maturity</div><div class="sub" style="font-size:25px;margin-top:8px">constant-maturity tenors 7 to 182 days, T = days / 365</div>`, "left:1140px;top:84px"),
    z: mk("axz", "t", `<div class="hl cy" style="font-size:40px">Implied volatility</div><div class="sub" style="font-size:25px;margin-top:8px">Black-76 implied vol, shown in vol points</div>`, "left:1140px;top:84px"),
  };
  const l2 = mk("l2", "t hl", "A structured view<br>of market uncertainty", "left:1140px;top:84px;font-size:40px");
  const tTitle = mk("tt", "t", `<div class="hl" style="font-size:66px;letter-spacing:.14em;line-height:1.14">Neural<br>Volatility<br>Surface</div>`, "left:96px;top:270px");
  const tSub = mk("ts", "t", `<div class="cy" style="font-weight:500;font-size:25px;letter-spacing:.2em;text-transform:uppercase;text-shadow:0 2px 14px #000">Machine Learning ×<br>Quantitative Finance ×<br>Research Engineering</div>`, "left:96px;top:640px;width:560px;line-height:1.7");
  const tFin = mk("tf", "t sub", "Building the infrastructure for rigorous volatility research.", "left:96px;top:830px;width:540px;font-size:28px;line-height:1.4");

  // ================= DOM: scene 3 =================
  const n1 = mk("n1", "t hl", "Neural volatility<br>modeling", "left:96px;top:84px;font-size:44px");
  const n1b = mk("n1b", "t sub", "Exploring forecasts across a structured surface", "left:96px;top:236px;width:760px");
  const nlab = mk("nlab", "t", `<b>ILLUSTRATIVE</b> &nbsp;·&nbsp; conceptual network diagram, not the architecture or the output of any trained model<br>input: the 54 cells of the SPY surface shown before (${N.date}, backtest only)`);

  // ================= DOM: scene 4 (verbatim excerpts of project files and API output) =================
  const X = N.excerpts;
  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
  const cut = (s, n) => (s.length > n ? s.slice(0, n - 1) + "…" : s);
  const pj1 = v => (typeof v === "string" ? `<span class="s">"${esc(cut(v, 44))}"</span>` : typeof v === "number" ? `<span class="n">${v}</span>` : `<span class="d">${v}</span>`);
  function pj(o, ind) {
    const pad = "  ".repeat(ind), pad2 = "  ".repeat(ind + 1);
    if (Array.isArray(o)) return o.every(v => typeof v !== "object") ? "[" + o.map(pj1).join(", ") + "]" : "[\n" + o.map(v => pad2 + pj(v, ind + 1)).join(",\n") + "\n" + pad + "]";
    if (o && typeof o === "object" && Object.keys(o).length <= 2 && Object.values(o).every(v => typeof v !== "object")) return "{" + Object.entries(o).map(([k, v]) => `<span class="k">"${esc(k)}"</span>: ` + pj1(v)).join(", ") + "}";
    if (o && typeof o === "object") return "{\n" + Object.entries(o).map(([k, v]) => pad2 +`<span class="k">"${esc(k)}"</span>: ` + pj(v, ind + 1)).join(",\n") + "\n" + pad + "}";
    return pj1(o);
  }
  const bar = t => `<div class="bar"><i></i><i></i><i></i><span style="margin-left:10px">${t}</span></div>`;
  const apiObj = Object.assign({}, X.api); delete apiObj.GET;
  const panel = (id, x, y, w, barTxt, body) => mk(id, "panel", bar(barTxt) + `<pre>${body}</pre>`, `left:${x}px;top:${y}px;width:${w}px`);
  const ck = '<span class="g">✓</span>', ng = '<span class="r">○</span>';
  const pAPI = panel("pa", 96, 236, 900, `GET ${esc(X.api.GET)}`, pj(apiObj, 0));
  const pRoutes = panel("pb", 1030, 236, 794, "research API · implemented routes (API_CONTRACTS §8)",
    `<span class="k">GET</span> /                          <span class="d">static viewer</span>\n<span class="k">GET</span> /api/runs                 <span class="d">run list, origin</span>\n<span class="k">GET</span> /api/runs/{id}            <span class="d">axes, status counts</span>\n<span class="k">GET</span> …/surface/{index}         <span class="d">iv[T][K] + status</span>\n<span class="k">GET</span> …/forecasts/{model}/{i}   <span class="d">forecast, diff</span>\n<span class="k">GET</span> …/tables/{name}           <span class="d">result tables</span>\n\n<span class="r">HEAD · POST · …</span>  →  <span class="n">405</span> read-only API\n\n<span class="d">status</span>  <span class="n">0</span> missing   <span class="n">1</span> interpolated_T\n        <span class="n">2</span> interpolated_k  <span class="n">3</span> observed\n<span class="d">no "extrapolated": nothing is extrapolated</span>`);
  const linEx = JSON.parse(JSON.stringify(X.lineage)); delete linEx.surface;
  linEx.inputs = [...linEx.inputs.slice(0, 2).map(x => ({ name: x.name, sha256: x.sha256 })), linEx.inputs[linEx.inputs.length - 1]];
  const pLin = panel("pc", 96, 236, 900, "manifest.json · lineage of this run", pj(linEx, 0));
  const pProv = panel("pd", 1030, 236, 794, "what a run records",
    `${ck} <span class="k">inputs</span>        name · bytes · sha256\n${ck} <span class="k">config_sha256</span> quote filter, grid,\n                 features, split, training\n${ck} <span class="k">version_id</span>    content hash of the dataset\n${ck} <span class="k">origin</span>        real | synthetic label\n${ng} per-cell quote lineage\n  <span class="d">not stored (documented gap G4)</span>\n\n<span class="d">requirement SCI-013: every artifact</span>\n<span class="d">traceable to source, processing,</span>\n<span class="d">split windows, model, seed</span>`);
  const T = n => `${ck} <span class="s">${n}</span>`;
  const pTests = panel("pe", 96, 236, 900, "backend/tests/scientific · pytest",
    [T("test_every_ok_status_reprices_the_input"), T("test_scale_invariance"), T("test_put_call_parity_of_the_undiscounted_prices"), T("test_inversion_is_deterministic"), T("test_report_is_deterministic"), T("test_held_out_quotes_are_interior…"), T("test_every_fold_keeps_the_test_year_out…"), T("test_the_sentinel_can_fail_training_on_post…"), "", `<span class="g">40 passed</span> <span class="d">in 81.68s</span>`].join("\n"));
  const pCounts = panel("pf", 1030, 236, 794, "known answers · leakage sentinels",
    `<span class="k">iv_recovery</span>               <span class="n">10</span>\n<span class="k">iv_edge_cases</span>             <span class="n">14</span>\n<span class="k">interpolation_comparison</span>  <span class="n">13</span>\n<span class="k">leakage_sentinels</span>          <span class="n">3</span>\n<span class="d">──────────────────────────────</span>\n<span class="g">40 passed</span>\n\n<span class="d">IV priced from a known</span>\n<span class="d">volatility must be recovered;</span>\n<span class="d">scrambled future must not</span>\n<span class="d">change fitted baselines</span>`);
  const pGuard = panel("pg", 96, 236, 900, "guardrails.md · enforceable rules",
    `<span class="k">GR-LEAK-01</span>  Time-series data is split\n            chronologically; label horizon\n            overlap is handled.\n<span class="k">GR-LEAK-02</span>  Scalers/transforms/imputers are\n            fit only on eligible training\n            data, re-fit per fold.\n<span class="k">GR-LEAK-03</span>  Features at origin t use only\n            information available at t.\n<span class="k">GR-DATA-04</span>  Never fabricate market\n            observations; synthetic data\n            is always labelled.`);
  const pPrin = panel("ph", 1030, 236, 794, "CLAUDE.md · quantitative research guardrails",
    `<span class="s">A neural model is</span>\n<span class="s">never presumed better</span>\n<span class="s">than persistence or</span>\n<span class="s">regression.</span>\n\n<span class="d">No "improvement" claim without</span>\n<span class="d">out-of-sample, chronologically</span>\n<span class="d">split evidence with sample</span>\n<span class="d">counts.</span>`);
  const BEATS = [
    { a: 30.0, kw: "Data contracts", sub: "a read-only API with explicit cell status", L: pAPI, R: pRoutes },
    { a: 32.5, kw: "Experiment traceability", sub: "every run records its inputs and configuration", L: pLin, R: pProv },
    { a: 35.0, kw: "Engineering verification", sub: "known-answer tests and leakage sentinels", L: pTests, R: pCounts },
    { a: 37.5, kw: "Research integrity", sub: "rules written to be enforced, not admired", L: pGuard, R: pPrin },
  ];
  BEATS.forEach((b, i) => { b.el = mk("kw" + i, "kw", `${b.kw}<small>${b.sub}</small>`, "left:96px;top:84px"); });
  const prog = mk("prog", "t", BEATS.map((b, i) => `<span id="pg${i}" style="margin-right:46px">${b.kw}</span>`).join(""), "left:96px;top:1000px;font-size:17px;letter-spacing:.2em;text-transform:uppercase;color:#7d9bb8");

  // ================= DOM: scene 5 (real captures of the research workbench) =================
  const SHOTS = [
    { id: "landing", a: 39.9, b: 43.3, w: 1300, h: 812, x: 310, y: 150, iw: 1300, from: { z: 1.0, px: 0, py: 0, ry: -7 }, to: { z: 1.06, px: -20, py: -10, ry: -2 } },
    { id: "explorer3d", a: 42.8, b: 46.2, w: 1300, h: 812, x: 310, y: 150, iw: 1300, from: { z: 1.0, px: 0, py: 0, ry: 4 }, to: { z: 1.0, px: 0, py: -430, ry: 1 } },
    { id: "heatmap", a: 45.7, b: 48.2, w: 1300, h: 812, x: 310, y: 150, iw: 1300, from: { z: 1.0, px: 0, py: 0, ry: -4 }, to: { z: 1.1, px: -60, py: -50, ry: 0 } },
  ];
  SHOTS.forEach(s => { s.el = mk("sh_" + s.id, "shot", `<img src="out/shots/${s.id}.png" alt="">`, `left:${s.x}px;top:${s.y}px;width:${s.w}px;height:${s.h}px`); s.img = s.el.firstChild; s.img.style.cssText = `position:absolute;left:0;top:0;width:${s.iw}px;height:auto;transform-origin:0 0`; });
  const s5k = mk("s5k", "kw", `Research workbench<small>inspect every surface cell and how it was obtained</small>`, "left:96px;top:46px;font-size:26px");
  const s5c = mk("s5c", "t", `<b>APPLICATION CAPTURE</b> &nbsp;·&nbsp; local research API &nbsp;·&nbsp; SPY end-of-day run &nbsp;·&nbsp; backtest only`, MUTED);

  // ================= DOM: scene 6 =================
  const s6v = mk("s6v", "t", "", "left:0;top:0;width:1920px;height:1080px;background:radial-gradient(ellipse 62% 58% at 50% 56%, rgba(4,7,14,.82), rgba(4,7,14,0) 100%)");
  const s6a = mk("s6a", "t hl", "A model is only as credible<br>as its evidence.", "left:0;width:1920px;text-align:center;top:150px;font-size:54px;letter-spacing:.14em");
  const s6b = mk("s6b", "t sub", "Engineering readiness is not scientific validation.", "left:0;width:1920px;text-align:center;top:350px;font-size:40px");
  const CHAIN = ["Source & snapshot", "Quote filter", "IV solve", "Surface grid", "Features", "Chronological split", "Model", "Evaluation"];
  const chain = mk("chain", "t", CHAIN.map((c, i) => `<span class="cn" id="cn${i}">${c}</span>`).join('<span class="ca">›</span>'), "left:0;width:1920px;text-align:center;top:470px;font-size:19px;letter-spacing:.12em;text-transform:uppercase;color:#9fc4df");
  const chips = [
    ["c-ok", "IMPLEMENTED", "Chronological splits and leakage tests"], ["c-ok", "IMPLEMENTED", "Persistence and ridge baselines before any neural model"],
    ["c-no", "UNSUPPORTED", "Statistical significance and inference claims"], ["c-no", "NOT VALIDATED", "Neural forecasting on real options data"], ["c-wait", "PENDING", "Licensed real-data feasibility"],
  ].map((c, i) => mk("chip" + i, "t", `<span class="chip ${c[0]}">${c[1]}</span><span style="font-size:25px;color:#d3e6f6;letter-spacing:.03em">${c[2]}</span>`, `left:430px;top:${600 + i * 66}px`));
  const fade = document.getElementById("fade");

  // ================= cameras =================
  const CAM_A = [
    K(0.0, 22, 4, 2.7, .12, .15, .20, 30), K(3.0, 27, 9, 3.6, .05, .06, .30, 30), K(7.0, 34, 22, 5.2, 0, 0, .36, 30, 0, -45), K(8.0, 35, 24, 5.2, 0, 0, .36, 30, 0, -45), K(9.4, 33, 23, 5.1, 0, 0, .36, 30, 0, -45),
    K(11.0, 8, 19, 3.3, -.15, .35, .45), K(12.6, 14, 17, 3.2, .1, .4, .44), K(14.2, 66, 17, 3.6, .1, 0, .40), K(15.8, 72, 15, 3.5, 0, .1, .42),
    K(16.8, 22, 9, 3.9, -.85, .30, .50), K(17.9, 30, 12, 4.2, -.2, .1, .45), K(20.0, 52, 27, 5.2, 0, 0, .36, 30, 0, -45),
  ];
  const CAM_C = [K(20.0, 52, 27, 5.2, 0, 0, .36, 30, 0, -45), K(22.0, 44, 20, 8.0, -1.2, 0, .5, 30, 0, -10), K(24.6, 38, 13, 11.6, .5, 0, .5), K(27.5, 34, 11, 11.0, 1.2, 0, .5), K(30.0, 30, 10, 9.0, 2.6, 0, .5)];
  const CAM_B = [K(30.0, 30, 24, 5.4, 0, 0, .36, 30, 0, -30), K(48.0, 41, 26, 4.5, 0, 0, .38), K(55.0, 43, 25, 4.6, 0, 0, .38), K(56.4, 40, 25, 5.7, 0, 0, .38, 30, 290, 10), K(60.0, 36, 24, 5.9, 0, 0, .38, 30, 290, 10)];

  function slice(cam, kind, a) { // highlighted curve on the surface: the 30-day tenor row, or the k = 0 column
    if (a <= 0) return; const M = N.mesh, pts = [];
    if (kind === "row") for (let i = 0; i < M.ni; i++) pts.push([E.kx(M.kGrid[i]), E.ty(2), E.vz(M.z[24][i]) + .02]);
    else for (let j = 0; j < M.nj; j++) pts.push([E.kx(0), E.ty(j * 5 / (M.nj - 1)), E.vz(M.z[j][80]) + .02]);
    const P = pts.map(p => proj(cam, p)); ctx.save(); ctx.lineJoin = "round"; ctx.lineCap = "round";
    for (const [w, al, col] of [[7, .16, "120,220,255"], [3, 1, "205,250,255"]]) { ctx.globalAlpha = a * al; ctx.strokeStyle = `rgb(${col})`; ctx.lineWidth = w; ctx.beginPath(); P.forEach((p, n) => (n ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke(); }
    ctx.restore();
  }
  function surfaceScene(t, keys, o, extra) { const cam = makeCam(camAt(keys, t)); drawBox(cam, o); drawSurface(cam, o); if (extra) extra(cam); drawAxisLabels(cam, o); return cam; }

  // ================= scene 3: illustrative network =================
  const LAYERS = [{ x: -4.8, cols: 9, rows: 6 }, { x: -2.4, cols: 8, rows: 5 }, { x: 0, cols: 6, rows: 4 }, { x: 2.4, cols: 4, rows: 4 }]; // sheets of nodes, seen obliquely
  const lp = (li, c, r) => { const l = LAYERS[li]; return [l.x, -.95 + 1.9 * c / (l.cols - 1), .92 - .84 * r / (l.rows - 1)]; };
  const OUT = { s: .6, ox: 5.4, oy: 0, oz: .04 };
  const outNode = (j, c) => { const w = nodeW(j, c); return [w[0] * OUT.s + OUT.ox, w[1] * OUT.s + OUT.oy, w[2] * OUT.s + OUT.oz]; };
  const EDGES = [];
  for (let li = 0; li < 4; li++) {
    const A = LAYERS[li], tc = li < 3 ? LAYERS[li + 1].cols : 9, tr = li < 3 ? LAYERS[li + 1].rows : 6, want = li === 3 ? 4 : 3;
    for (let c = 0; c < A.cols; c++) for (let r = 0; r < A.rows; r++) {
      const u = A.cols > 1 ? c / (A.cols - 1) : 0, v = A.rows > 1 ? r / (A.rows - 1) : 0, base = [Math.round(u * (tc - 1)), Math.round(v * (tr - 1))], tg = [base];
      for (let k = 0; tg.length < want && k < 40; k++) {
        const h1 = hash(li * 131 + c * 17 + r * 7 + k * 3.1), h2 = hash(li * 57 + c * 5 + r * 11 + k * 1.7);
        const c2 = clamp(base[0] + (h1 < .34 ? -1 : h1 > .66 ? 1 : 0), 0, tc - 1), r2 = clamp(base[1] + (h2 < .34 ? -1 : h2 > .66 ? 1 : 0), 0, tr - 1);
        if (!tg.some(q => q[0] === c2 && q[1] === r2)) tg.push([c2, r2]);
      }
      for (const [c2, r2] of tg) EDGES.push({ li, a: lp(li, c, r), b: li === 3 ? outNode(r2, c2) : lp(li + 1, c2, r2), h: hash(EDGES.length * 1.3 + 5) });
    }
  }
  const LINK_T0 = [22.6, 23.0, 23.4, 26.2], LINK_RGB = ["120,230,255", "165,140,255", "190,150,255", "130,235,255"], LAYER_T0 = [0, 22.3, 22.7, 23.1];
  function glowDot(x, y, r, rgb, al, ring) {
    if (al <= 0.01) return; const g = ctx.createRadialGradient(x, y, 0, x, y, r * 3.4); g.addColorStop(0, `rgba(${rgb},${.5 * al})`); g.addColorStop(1, `rgba(${rgb},0)`);
    ctx.globalAlpha = 1; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 3.4, 0, 7); ctx.fill();
    ctx.globalAlpha = al; if (ring) { ctx.strokeStyle = `rgb(${rgb})`; ctx.lineWidth = 1.8; ctx.beginPath(); ctx.arc(x, y, r * 1.05, 0, 7); ctx.stroke(); ctx.fillStyle = "rgba(5,10,24,.9)"; ctx.beginPath(); ctx.arc(x, y, r * .6, 0, 7); ctx.fill(); } else { ctx.fillStyle = "rgb(235,252,255)"; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill(); }
    ctx.globalAlpha = 1;
  }
  function drawS3(t) {
    const cam = makeCam(camAt(CAM_C, t)), fadeS = 1 - sstep(20.0, 21.6, t);
    if (fadeS > 0) { const o = { time: t, nodesA: t < 21.45 ? 1 : 0, alpha: fadeS, lineA: 1, contA: .75 * fadeS, floorA: .9 * fadeS, glow: .15, boxA: fadeS, axisA: fadeS }; drawBox(cam, o); drawSurface(cam, o); drawAxisLabels(cam, o); }
    ctx.save(); ctx.lineCap = "round";
    for (let li = 0; li < 4; li++) { const a = sstep(LAYER_T0[li] || 21.4, (LAYER_T0[li] || 21.4) + .9, t) * .5; if (a <= 0) continue; const x = LAYERS[li].x; ctx.strokeStyle = `rgba(150,130,255,${a * .55})`; ctx.lineWidth = 1.2; const c = [[-1.08, -.02], [1.08, -.02], [1.08, 1.0], [-1.08, 1.0]]; for (let e = 0; e < 4; e++) E.line3(cam, [x, c[e][0], c[e][1]], [x, c[(e + 1) % 4][0], c[(e + 1) % 4][1]]); }
    for (const e of EDGES) {
      const ap = sstep(LINK_T0[e.li], LINK_T0[e.li] + 1.0, t); if (ap <= 0) continue;
      ctx.strokeStyle = `rgba(${LINK_RGB[e.li]},${.16 * ap})`; ctx.lineWidth = 1; E.line3(cam, e.a, e.b);
      const ph = ((t - 24.6 - e.li * .55 - e.h * 1.6) % 3.2 + 3.2) % 3.2 / .75;
      if (t > 24.6 && ph > 0 && ph < 1) {
        const q = ph, q0 = Math.max(0, q - .16), P = s => [lerp(e.a[0], e.b[0], s), lerp(e.a[1], e.b[1], s), lerp(e.a[2], e.b[2], s)];
        ctx.strokeStyle = `rgba(${LINK_RGB[e.li]},${.9 * ap})`; ctx.lineWidth = 1.9; E.line3(cam, P(q0), P(q));
        const pp = proj(cam, P(q)); if (pp[2] > .2) glowDot(pp[0], pp[1], 2.6, LINK_RGB[e.li], ap);
      }
    }
    ctx.restore();
    const oa = sstep(26.4, 28.4, t); if (oa > 0) drawSurface(cam, { time: t, alpha: oa, nodesA: oa, lineA: 1, contA: .45 * oa, glow: .1, xf: OUT });
    let n = 0;
    for (let j = 0; j < 6; j++) for (let c = 0; c < 9; c++, n++) {
      if (t < 21.45) continue;
      const w0 = nodeW(j, c), w1 = lp(0, c, j), e = eio(clamp((t - 21.45 - .7 * (n / 54)) / 1.5)), arc = Math.sin(Math.PI * e) * .35;
      const p = proj(cam, [lerp(w0[0], w1[0], e), lerp(w0[1], w1[1], e), lerp(w0[2], w1[2], e) + arc]); if (p[2] < .2) continue;
      const tIV = clamp((N.iv[j][c] - 23.7) / (65.3 - 23.7)), lc = LUT[(tIV * 255) | 0], isObs = N.status[j][c] === 3;
      const rgb = e < .98 ? "170,240,255" : `${lerp(lc[0], 190, .5) | 0},${lerp(lc[1], 245, .5) | 0},255`;
      glowDot(p[0], p[1], clamp(1883 * .0066 / p[2], 2.4, 6), rgb, 1, !isObs);
    }
    for (let li = 1; li < 4; li++) { const a = sstep(LAYER_T0[li], LAYER_T0[li] + .9, t); if (a <= 0) continue; const L = LAYERS[li]; for (let c = 0; c < L.cols; c++) for (let r = 0; r < L.rows; r++) { const p = proj(cam, lp(li, c, r)); if (p[2] > .2) { const pulse = .5 + .5 * Math.sin(t * 3 + c * 1.7 + r * 2.3 + li); glowDot(p[0], p[1], 3.6, li === 2 ? "190,160,255" : "160,140,255", a * (.65 + .35 * pulse)); } } }
    const la = sstep(23.0, 24.2, t);
    if (la > 0) { const lb = (txt, w, o2) => { const p = proj(cam, w); if (p[2] > .2) label(txt, p[0], p[1], { size: 17, weight: 600, spacing: "0.16em", alpha: la * o2 }); };
      lb("INPUT · 54 SURFACE CELLS", [-4.8, 0, -.16], 1); lb("HIDDEN LAYERS", [-1.2, 0, -.16], .9); lb("OUTPUT · SURFACE-SHAPED FORECAST", [5.4, 0, -.34], sstep(26.6, 27.6, t)); }
    return cam;
  }

  // ================= frame =================
  window.bbox = function (t, keys) { const cam = makeCam(camAt(keys === "B" ? CAM_B : CAM_A, t)); let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9; for (const x of [-E.XW, E.XW]) for (const y of [-E.YW, E.YW]) for (const z of [0, E.ZH]) { const p = proj(cam, [x, y, z]); x0 = Math.min(x0, p[0]); x1 = Math.max(x1, p[0]); y0 = Math.min(y0, p[1]); y1 = Math.max(y1, p[1]); } return [x0, x1, y0, y1].map(Math.round); };
  window.READY = Promise.all([document.fonts.ready, ...SHOTS.map(s => s.img.decode().catch(() => 0))]).then(() => true);

  window.renderFrame = function (t) {
    drawBackground(); ctx.globalAlpha = 1;
    let bloom = .55, bloom2 = .38, veil = 0;
    ALL.forEach(e => (e.style.opacity = 0));
    const e5 = (a, d) => clamp((t - a) / d);

    if (t < 20) {
      const pulse = t > 7 ? Math.exp(-(t - 7) * 2.6) : 0;
      const o = {
        time: t, nodeAppear: t < 6.2, nodesA: sstep(1, 1.8, t), latA: sstep(2.6, 4.6, t) * (1 - sstep(5.8, 7.2, t)),
        front: t < 4.4 ? -1 : lerp(-.1, 1.3, eio(clamp((t - 4.4) / 2.9))), alpha: 1, lineA: 1, contA: sstep(6.4, 8.6, t) * .75, floorA: sstep(4.8, 7.4, t) * .9,
        glow: pulse * .55 + sstep(14, 19, t) * .15, boxA: sstep(.2, 2.4, t), axisA: sstep(2.8, 4.6, t),
        focus: { x: trap(t, 9.4, 12.7, .6, .6), y: trap(t, 12.7, 15.8, .6, .6), z: trap(t, 15.8, 18.0, .6, .6) },
      };
      surfaceScene(t, CAM_A, o, cam => { slice(cam, "row", trap(t, 10.0, 12.9, .7, .6)); slice(cam, "col", trap(t, 13.2, 15.8, .7, .6)); });
      bloom += pulse * .5;
      put(lab, sstep(2.2, 3.4, t));
      put(l1, trap(t, .9, 4.6, 1.2, .9), (1 - clamp((t - .9) / 1.2)) * 14);
      put(l1b, trap(t, 4.9, 8.4, 1.0, .9), (1 - clamp((t - 4.9) / 1.0)) * 12);
      put(axT.x, trap(t, 9.4, 12.6, .6, .5)); put(axT.y, trap(t, 12.7, 15.7, .5, .5)); put(axT.z, trap(t, 15.8, 18.0, .5, .5));
      put(l2, trap(t, 18.2, 20.0, .8, .3), (1 - clamp((t - 18.2) / .8)) * 10);
      put(legend, trap(t, 9.2, 20, .8, .1) * .9);
    } else if (t < 30) {
      drawS3(t);
      put(lab, 1 - sstep(20.0, 21.4, t)); put(legend, (1 - sstep(20.0, 21.2, t)) * .9);
      put(n1, trap(t, 22.0, 29.2, 1.0, .6), (1 - e5(22.0, 1.0)) * 14); put(n1b, trap(t, 24.4, 29.2, 1.0, .6), (1 - e5(24.4, 1.0)) * 12);
      put(nlab, trap(t, 22.6, 29.4, 1.0, .6));
      veil = sstep(29.3, 29.95, t);
    } else {
      // backdrop for scenes 4-6 and the final reveal: the surface, faint, slowly orbiting
      const ramp = sstep(54.6, 56.2, t), faint = t < 54.6 ? (t < 48 ? .12 : .13) : lerp(.13, 1, ramp), pulse = t > 56.4 ? Math.exp(-(t - 56.4) * 2.4) : 0;
      const o = { time: t, nodesA: lerp(.2, 1, ramp), alpha: faint, lineA: 1, contA: lerp(.25, .85, ramp), floorA: lerp(.25, .9, ramp), glow: .18 + ramp * .25 + pulse * .6, boxA: lerp(.3, 1, ramp), axisA: t < 48 ? 0 : lerp(.25, 1, ramp), rimA: 1, zdx: 90 * ramp };
      surfaceScene(t, CAM_B, o);
      bloom += pulse * .55;
      veil = 1 - sstep(30.0, 30.8, t);

      if (t < 40.2) { // scene 4: engineering montage
        BEATS.forEach((b, i) => {
          const life = trap(t, b.a, b.a + 2.5, .5, .3), e = 1 - eout(clamp((t - b.a) / .7)), drift = -5 * clamp(t - b.a, 0, 2.5);
          b.L.style.opacity = life.toFixed(3); b.L.style.transform = `perspective(1800px) translate3d(${(-60 * e).toFixed(1)}px,${drift.toFixed(1)}px,0) rotateY(${(4 * e).toFixed(2)}deg)`;
          b.R.style.opacity = clamp(life * 1.3 - .1, 0, 1).toFixed(3); b.R.style.transform = `perspective(1800px) translate3d(${(60 * e).toFixed(1)}px,${(drift - 4).toFixed(1)}px,0) rotateY(${(-4 * e).toFixed(2)}deg)`;
          b.el.style.opacity = life.toFixed(3); b.el.style.transform = `translate3d(${(-24 * e).toFixed(1)}px,0,0)`;
        });
        put(prog, trap(t, 30.2, 40, .6, .4));
        BEATS.forEach((b, i) => { const on = t >= b.a && t < b.a + 2.5, s = document.getElementById("pg" + i); s.style.color = on ? "#bff3ff" : "#5d7a96"; s.style.borderBottom = on ? "2px solid #6fdcff" : "2px solid transparent"; s.style.paddingBottom = "6px"; });
      }
      if (t >= 39.8 && t < 48.3) { // scene 5: the real interface
        SHOTS.forEach(s => {
          const life = trap(t, s.a, s.b, .6, .6), u = eio(clamp((t - s.a) / (s.b - s.a))), z = lerp(s.from.z, s.to.z, u), px = lerp(s.from.px, s.to.px, u), py = lerp(s.from.py, s.to.py, u), ry = lerp(s.from.ry, s.to.ry, u);
          s.el.style.opacity = life.toFixed(3); s.el.style.transform = `perspective(2400px) rotateY(${ry.toFixed(2)}deg) rotateX(${(1.2 * (1 - u)).toFixed(2)}deg) translate3d(0,${((1 - clamp((t - s.a) / .8)) * 24).toFixed(1)}px,0)`;
          s.img.style.transform = `translate(${px.toFixed(1)}px,${py.toFixed(1)}px) scale(${z.toFixed(4)})`;
        });
        put(s5k, trap(t, 40.2, 47.8, .8, .6)); put(s5c, trap(t, 40.4, 47.8, .8, .6));
      }
      if (t >= 48 && t < 55.2) { // scene 6: evidence
        put(s6v, trap(t, 48.2, 55.0, 1.0, .8)); put(s6a, trap(t, 48.5, 51.9, 1.0, .7), (1 - e5(48.5, 1.0)) * 12); put(s6b, trap(t, 51.7, 55.0, 1.0, .8), (1 - e5(51.7, 1.0)) * 12);
        put(chain, trap(t, 49.0, 55.0, .8, .8) * .95, 0);
        CHAIN.forEach((c, i) => { document.getElementById("cn" + i).style.opacity = e5(49.3 + i * .22, .5).toFixed(3); });
        chips.forEach((c, i) => put(c, trap(t, 52.0 + i * .28, 55.0, .6, .7), (1 - e5(52.0 + i * .28, .6)) * 10));
        put(lab, .55 * trap(t, 48.2, 55, 1, .4));
      }
      if (t >= 54.6) { // scene 7: title
        put(lab, trap(t, 54.8, 60, 1, 1));
        put(tTitle, e5(56.3, 1.0) * (1 - sstep(59.2, 60, t)), (1 - e5(56.3, 1.0)) * 18);
        put(tSub, e5(57.1, .9) * (1 - sstep(59.2, 60, t)), (1 - e5(57.1, .9)) * 12);
        put(tFin, e5(58.0, .9) * (1 - sstep(59.2, 60, t)), (1 - e5(58.0, .9)) * 12);
      }
    }
    post(bloom, bloom2);
    fade.style.opacity = Math.max(veil, sstep(59.1, 59.95, t)).toFixed(3);
    return true;
  };
})();
