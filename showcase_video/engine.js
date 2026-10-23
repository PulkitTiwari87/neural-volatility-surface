"use strict";
// Dependency-free 3D surface renderer on a 2D canvas (painter's algorithm). Everything is a pure function of time.
(function () {
  const W = 1920, H = 1080, N = window.NVS, M = N.mesh, NJ = M.nj, NI = M.ni, NV = NJ * NI, NQ = (NJ - 1) * (NI - 1);
  const cv = document.getElementById("c"), ctx = cv.getContext("2d");
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
  const eio = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const eout = t => 1 - Math.pow(1 - t, 3);
  const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

  // ---------- world mapping: x = log-moneyness k, y = tenor node index (7d at the back), z = IV in vol points ----------
  const KMIN = N.kNodes[0], KMAX = N.kNodes[N.kNodes.length - 1];
  const XW = 1.2, YW = 1.0, ZH = 1.0, ZLO = 20, ZHI = 70;
  const kx = k => (k - KMIN) / (KMAX - KMIN) * 2 * XW - XW;
  const ty = j => YW - (j / 5) * 2 * YW;
  const vz = v => (v - ZLO) / (ZHI - ZLO) * ZH;
  const nodeW = (j, c) => [kx(N.kNodes[c]), ty(j), vz(N.iv[j][c])];

  const VX = new Float32Array(NV), VY = new Float32Array(NV), VZ = new Float32Array(NV), VH = new Float32Array(NV), VI = new Float32Array(NV);
  let IVMIN = 1e9, IVMAX = -1e9;
  for (let j = 0; j < NJ; j++) for (let i = 0; i < NI; i++) { const v = M.z[j][i]; IVMIN = Math.min(IVMIN, v); IVMAX = Math.max(IVMAX, v); }
  for (let j = 0; j < NJ; j++) for (let i = 0; i < NI; i++) {
    const n = j * NI + i, v = M.z[j][i];
    VX[n] = kx(M.kGrid[i]); VY[n] = ty(j * 5 / (NJ - 1)); VZ[n] = vz(v); VI[n] = v; VH[n] = clamp((v - IVMIN) / (IVMAX - IVMIN));
  }
  // vertex normals (central differences), oriented upward
  const VNX = new Float32Array(NV), VNY = new Float32Array(NV), VNZ = new Float32Array(NV);
  for (let j = 0; j < NJ; j++) for (let i = 0; i < NI; i++) {
    const a = j * NI + Math.max(0, i - 1), b = j * NI + Math.min(NI - 1, i + 1), c = Math.max(0, j - 1) * NI + i, d = Math.min(NJ - 1, j + 1) * NI + i;
    const ux = VX[b] - VX[a], uy = VY[b] - VY[a], uz = VZ[b] - VZ[a], wx = VX[d] - VX[c], wy = VY[d] - VY[c], wz = VZ[d] - VZ[c];
    let nx = wy * uz - wz * uy, ny = wz * ux - wx * uz, nz = wx * uy - wy * ux; if (nz < 0) { nx = -nx; ny = -ny; nz = -nz; }
    const l = Math.hypot(nx, ny, nz) || 1; const n = j * NI + i; VNX[n] = nx / l; VNY[n] = ny / l; VNZ[n] = nz / l;
  }
  // quad statics
  const QH = new Float32Array(NQ), QNX = new Float32Array(NQ), QNY = new Float32Array(NQ), QNZ = new Float32Array(NQ);
  const QX = new Float32Array(NQ), QY = new Float32Array(NQ), QZ = new Float32Array(NQ), QR = new Float32Array(NQ), QMIN = new Float32Array(NQ), QMAX = new Float32Array(NQ);
  const RMAX = Math.hypot(XW, YW);
  for (let j = 0; j < NJ - 1; j++) for (let i = 0; i < NI - 1; i++) {
    const q = j * (NI - 1) + i, a = j * NI + i, b = a + 1, c = a + NI + 1, d = a + NI;
    QH[q] = (VH[a] + VH[b] + VH[c] + VH[d]) / 4; QNX[q] = (VNX[a] + VNX[b] + VNX[c] + VNX[d]) / 4; QNY[q] = (VNY[a] + VNY[b] + VNY[c] + VNY[d]) / 4; QNZ[q] = (VNZ[a] + VNZ[b] + VNZ[c] + VNZ[d]) / 4;
    const l = Math.hypot(QNX[q], QNY[q], QNZ[q]); QNX[q] /= l; QNY[q] /= l; QNZ[q] /= l;
    QX[q] = (VX[a] + VX[c]) / 2; QY[q] = (VY[a] + VY[c]) / 2; QZ[q] = (VZ[a] + VZ[b] + VZ[c] + VZ[d]) / 4;
    QR[q] = clamp(Math.hypot(QX[q] - 0.1, QY[q]) / RMAX);
    QMIN[q] = Math.min(VI[a], VI[b], VI[c], VI[d]); QMAX[q] = Math.max(VI[a], VI[b], VI[c], VI[d]);
  }

  // ---------- palette (deep indigo -> electric blue -> azure -> ice) ----------
  const STOPS = [[0, [14, 14, 70]], [.22, [26, 30, 126]], [.48, [26, 84, 206]], [.74, [36, 168, 244]], [1, [180, 248, 255]]];
  const LUT = [];
  for (let n = 0; n < 256; n++) { const t = n / 255; let k = 0; while (k < STOPS.length - 2 && t > STOPS[k + 1][0]) k++; const [t0, c0] = STOPS[k], [t1, c1] = STOPS[k + 1]; const u = clamp((t - t0) / (t1 - t0)); LUT.push([lerp(c0[0], c1[0], u), lerp(c0[1], c1[1], u), lerp(c0[2], c1[2], u)]); }
  const SHADOW = [30, 12, 82]; // violet-blue shadow tone

  // ---------- camera ----------
  const CK = ["az", "el", "d", "tx", "ty", "tz", "fov", "sx", "sy"];
  const K = (t, az, el, d, tx = 0, tyy = 0, tz = .4, fov = 32, sx = 0, sy = 0) => ({ t, az, el, d, tx, ty: tyy, tz, fov, sx, sy });
  function camAt(keys, t) {
    const n = keys.length; if (t <= keys[0].t) return Object.assign({}, keys[0]); if (t >= keys[n - 1].t) return Object.assign({}, keys[n - 1]);
    let i = 0; while (keys[i + 1].t < t) i++;
    const k0 = keys[Math.max(0, i - 1)], k1 = keys[i], k2 = keys[i + 1], k3 = keys[Math.min(n - 1, i + 2)];
    const dt = k2.t - k1.t, u = (t - k1.t) / dt, u2 = u * u, u3 = u2 * u, o = {};
    for (const p of CK) {
      const m1 = k0 === k1 ? 0 : (k2[p] - k0[p]) / (k2.t - k0.t) * dt, m2 = k3 === k2 ? 0 : (k3[p] - k1[p]) / (k3.t - k1.t) * dt;
      o[p] = (2 * u3 - 3 * u2 + 1) * k1[p] + (u3 - 2 * u2 + u) * m1 + (-2 * u3 + 3 * u2) * k2[p] + (u3 - u2) * m2;
    } return o;
  }
  function makeCam(c) {
    const az = c.az * Math.PI / 180, el = c.el * Math.PI / 180, ce = Math.cos(el);
    const pos = [c.tx + c.d * Math.sin(az) * ce, c.ty - c.d * Math.cos(az) * ce, c.tz + c.d * Math.sin(el)];
    let f = [c.tx - pos[0], c.ty - pos[1], c.tz - pos[2]]; let l = Math.hypot(...f); f = f.map(v => v / l);
    let r = [f[1], -f[0], 0]; l = Math.hypot(...r); r = r.map(v => v / l);
    const u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
    return { pos, f, r, u, foc: (H / 2) / Math.tan(c.fov * Math.PI / 360), sx0: c.sx, sy0: c.sy, d: c.d };
  }
  function proj(cam, p) { const dx = p[0] - cam.pos[0], dy = p[1] - cam.pos[1], dz = p[2] - cam.pos[2]; const a = dx * cam.r[0] + dy * cam.r[1] + dz * cam.r[2], b = dx * cam.u[0] + dy * cam.u[1] + dz * cam.u[2], c = dx * cam.f[0] + dy * cam.f[1] + dz * cam.f[2]; return [W / 2 + cam.sx0 + cam.foc * a / c, H / 2 + cam.sy0 - cam.foc * b / c, c]; }
  function toCam(cam, p) { const dx = p[0] - cam.pos[0], dy = p[1] - cam.pos[1], dz = p[2] - cam.pos[2]; return [dx * cam.r[0] + dy * cam.r[1] + dz * cam.r[2], dx * cam.u[0] + dy * cam.u[1] + dz * cam.u[2], dx * cam.f[0] + dy * cam.f[1] + dz * cam.f[2]]; }
  function scr(cam, pc) { return [W / 2 + cam.sx0 + cam.foc * pc[0] / pc[2], H / 2 + cam.sy0 - cam.foc * pc[1] / pc[2]]; }
  function seg3(cam, a, b) {
    let pa = toCam(cam, a), pb = toCam(cam, b); const n = .12;
    if (pa[2] < n && pb[2] < n) return null;
    if (pa[2] < n) { const t = (n - pa[2]) / (pb[2] - pa[2]); pa = [pa[0] + (pb[0] - pa[0]) * t, pa[1] + (pb[1] - pa[1]) * t, n]; }
    else if (pb[2] < n) { const t = (n - pb[2]) / (pa[2] - pb[2]); pb = [pb[0] + (pa[0] - pb[0]) * t, pb[1] + (pa[1] - pb[1]) * t, n]; }
    const A = scr(cam, pa), B = scr(cam, pb); return [A[0], A[1], B[0], B[1]];
  }
  function line3(cam, a, b) { const s = seg3(cam, a, b); if (!s) return; ctx.beginPath(); ctx.moveTo(s[0], s[1]); ctx.lineTo(s[2], s[3]); ctx.stroke(); }

  // ---------- background, vignette, bloom ----------
  function mkCanvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
  const bg = mkCanvas(W, H), vg = mkCanvas(W, H), bl1 = mkCanvas(W / 2, H / 2), bl2 = mkCanvas(W / 4, H / 4);
  (function () {
    const g = bg.getContext("2d"); let gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, "#04060d"); gr.addColorStop(.55, "#070b17"); gr.addColorStop(1, "#05070f"); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    gr = g.createRadialGradient(W * .52, H * .55, 40, W * .52, H * .55, W * .6); gr.addColorStop(0, "rgba(34,60,130,.30)"); gr.addColorStop(.5, "rgba(18,30,76,.12)"); gr.addColorStop(1, "rgba(0,0,0,0)"); g.fillStyle = gr; g.fillRect(0, 0, W, H);
    const im = g.getImageData(0, 0, W, H), d = im.data; let s = 12345; // static dither against banding in dark gradients
    for (let p = 0; p < d.length; p += 4) { s = (s * 1664525 + 1013904223) >>> 0; const nz = ((s >>> 24) / 255 - .5) * 2.4; d[p] = clamp(d[p] + nz, 0, 255); d[p + 1] = clamp(d[p + 1] + nz, 0, 255); d[p + 2] = clamp(d[p + 2] + nz, 0, 255); }
    g.putImageData(im, 0, 0);
    const v = vg.getContext("2d"); gr = v.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, W * .72); gr.addColorStop(0, "rgba(0,0,0,0)"); gr.addColorStop(1, "rgba(0,0,0,.62)"); v.fillStyle = gr; v.fillRect(0, 0, W, H);
  })();
  function post(bloom, bloom2) {
    const a = bl1.getContext("2d"); a.clearRect(0, 0, W / 2, H / 2); a.filter = "blur(6px)"; a.drawImage(cv, 0, 0, W / 2, H / 2); a.filter = "none";
    const b = bl2.getContext("2d"); b.clearRect(0, 0, W / 4, H / 4); b.filter = "blur(7px)"; b.drawImage(cv, 0, 0, W / 4, H / 4); b.filter = "none";
    ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.globalAlpha = bloom; ctx.drawImage(bl1, 0, 0, W, H); ctx.globalAlpha = bloom2; ctx.drawImage(bl2, 0, 0, W, H); ctx.restore();
    ctx.drawImage(vg, 0, 0);
  }
  function drawBackground(shade = 1) { ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.drawImage(bg, 0, 0); if (shade < 1) { ctx.fillStyle = `rgba(3,5,10,${1 - shade})`; ctx.fillRect(0, 0, W, H); } }

  // ---------- text on canvas ----------
  const FONT = '"Bahnschrift","Segoe UI Variable Text","Segoe UI",system-ui,sans-serif';
  function label(txt, x, y, o = {}) {
    ctx.save(); ctx.font = `${o.weight || 500} ${o.size || 17}px ${FONT}`; ctx.textAlign = o.align || "center"; ctx.textBaseline = "middle";
    if (o.spacing) ctx.letterSpacing = o.spacing; ctx.globalAlpha = o.alpha == null ? 1 : o.alpha;
    ctx.lineWidth = 5; ctx.strokeStyle = "rgba(4,6,12,.85)"; ctx.lineJoin = "round"; ctx.strokeText(txt, x, y);
    ctx.fillStyle = o.color || "rgba(175,214,236,.86)"; ctx.fillText(txt, x, y); ctx.restore();
  }

  // ---------- axes box ----------
  const KT = [-.2, -.15, -.1, -.05, 0, .05], ZT = [20, 30, 40, 50, 60, 70];
  const TLAB = N.tenorDays.map(d => d + "d");
  const fmtK = k => (k > 0 ? "+" : k < 0 ? "−" : "") + Math.abs(k).toFixed(2);
  const fsx = new Float32Array(NV), fsy = new Float32Array(NV), fok = new Uint8Array(NV);
  function contourTri(a, b, c, lv, X, Y) {
    const va = VI[a] - lv, vb = VI[b] - lv, vc = VI[c] - lv; const p = []; const ed = (m, n, vm, vn) => { if ((vm < 0) !== (vn < 0)) { const t = vm / (vm - vn); p.push(X[m] + (X[n] - X[m]) * t, Y[m] + (Y[n] - Y[m]) * t); } };
    ed(a, b, va, vb); ed(b, c, vb, vc); ed(c, a, vc, va); if (p.length === 4) { ctx.moveTo(p[0], p[1]); ctx.lineTo(p[2], p[3]); }
  }
  function drawBox(cam, o) {
    const A = o.boxA == null ? 1 : o.boxA; if (A <= 0) return;
    ctx.save(); ctx.lineCap = "round";
    const cp = [cam.pos[0], cam.pos[1], cam.pos[2] - ZH / 2];
    const gridRgb = "130,190,230";
    ctx.strokeStyle = `rgba(${gridRgb},${.16 * A})`; ctx.lineWidth = 1;
    for (const k of KT) line3(cam, [kx(k), -YW, 0], [kx(k), YW, 0]);
    for (let j = 0; j < 6; j++) line3(cam, [-XW, ty(j), 0], [XW, ty(j), 0]);
    ctx.strokeStyle = `rgba(${gridRgb},${.5 * A})`; ctx.lineWidth = 1.3;
    const C = [[-XW, -YW], [XW, -YW], [XW, YW], [-XW, YW]];
    for (let e = 0; e < 4; e++) line3(cam, [C[e][0], C[e][1], 0], [C[(e + 1) % 4][0], C[(e + 1) % 4][1], 0]);
    const walls = [{ n: [-1, 0], p: [-XW, 0] }, { n: [1, 0], p: [XW, 0] }, { n: [0, -1], p: [0, -YW] }, { n: [0, 1], p: [0, YW] }];
    for (const w of walls) {
      if (w.n[0] * cp[0] + w.n[1] * cp[1] - (w.n[0] * w.p[0] + w.n[1] * w.p[1]) > 0) continue; // camera outside this wall => front wall
      ctx.strokeStyle = `rgba(${gridRgb},${.12 * A})`; ctx.lineWidth = 1;
      for (const z of ZT) { const h = vz(z); if (w.n[0] !== 0) line3(cam, [w.p[0], -YW, h], [w.p[0], YW, h]); else line3(cam, [-XW, w.p[1], h], [XW, w.p[1], h]); }
      if (w.n[0] !== 0) for (let j = 0; j < 6; j++) line3(cam, [w.p[0], ty(j), 0], [w.p[0], ty(j), ZH]); else for (const k of KT) line3(cam, [kx(k), w.p[1], 0], [kx(k), w.p[1], ZH]);
    }
    if ((o.floorA || 0) > 0) { // floor iso-IV contours (projected, not occluded)
      for (let n = 0; n < NV; n++) { const p = proj(cam, [VX[n], VY[n], 0]); fsx[n] = p[0]; fsy[n] = p[1]; fok[n] = p[2] > .15 ? 1 : 0; }
      ctx.lineWidth = 1.1;
      for (let lv = 25; lv <= 65; lv += 5) {
        ctx.strokeStyle = `rgba(120,200,255,${(lv % 10 === 0 ? .34 : .17) * o.floorA * A})`; ctx.beginPath();
        for (let j = 0; j < NJ - 1; j++) for (let i = 0; i < NI - 1; i++) {
          const a = j * NI + i, b = a + 1, c = a + NI + 1, d = a + NI; if (!(fok[a] & fok[b] & fok[c] & fok[d])) continue;
          const q = j * (NI - 1) + i; if (lv < QMIN[q] || lv > QMAX[q]) continue;
          contourTri(a, b, c, lv, fsx, fsy); contourTri(a, c, d, lv, fsx, fsy);
        }
        ctx.stroke();
      }
    }
    ctx.restore();
  }
  function drawAxisLabels(cam, o) { // tick labels and axis titles, drawn after the surface
    const A = o.axisA == null ? 1 : o.axisA; if (A <= 0) return; const F = o.focus || {};
    const yE = cam.pos[1] < 0 ? -YW : YW, ySg = yE < 0 ? -1 : 1, xE = cam.pos[0] > 0 ? XW : -XW, xSg = xE < 0 ? -1 : 1;
    const base = { size: 17, alpha: A };
    for (const k of KT) { const p = proj(cam, [kx(k), yE + ySg * .13, 0]); if (p[2] > .2) label(fmtK(k), p[0], p[1], base); }
    for (let j = 0; j < 6; j++) { const p = proj(cam, [xE + xSg * .14, ty(j), 0]); if (p[2] > .2) label(TLAB[j], p[0], p[1], base); }
    const cs = [[-XW, -YW], [XW, -YW], [XW, YW], [-XW, YW]].map(c => ({ c, p: proj(cam, [c[0], c[1], 0]) }));
    const nearest = cs.reduce((m, e) => (e.p[2] < m.p[2] ? e : m)); const cand = cs.filter(e => e !== nearest); const zc = cand.reduce((m, e) => (e.p[0] < m.p[0] ? e : m));
    const ox = zc.c[0] < 0 ? -1 : 1, oy = zc.c[1] < 0 ? -1 : 1;
    for (const z of ZT) { const p = proj(cam, [zc.c[0] + ox * .13, zc.c[1] + oy * .13, vz(z)]); if (p[2] > .2) label(String(z), p[0], p[1], base); }
    const tit = (txt, sub, p, f, al) => { if (p[2] < .2) return; const e = clamp(f || 0), x = al ? Math.max(p[0] - 60 + (o.zdx || 0), 72) : p[0]; label(txt, x, p[1], { size: 20 + 3 * e, weight: 600, spacing: "0.22em", align: al, color: `rgba(${lerp(160, 140, e) | 0},${lerp(205, 240, e) | 0},${lerp(228, 255, e) | 0},${A * lerp(.62, 1, e)})` }); if (sub) label(sub, x, p[1] + 26, { size: 15, align: al, color: "rgba(150,190,215,.7)", alpha: A * lerp(.55, 1, e) }); };
    tit("STRIKE", "log-moneyness  k = ln(K/F)", proj(cam, [0.1, yE + ySg * .42, 0]), F.x);
    tit("MATURITY", "tenor, days  (T = days / 365)", proj(cam, [xE + xSg * .5, 0, 0]), F.y);
    tit("IMPLIED VOLATILITY", "vol points", proj(cam, [zc.c[0] + ox * .3, zc.c[1] + oy * .3, ZH * 1.12]), F.z, "left");
  }

  // ---------- the surface ----------
  const keyQ = new Float32Array(NQ + 54 + 93), idxAll = new Int32Array(NQ + 54 + 93), czA = new Float32Array(NV), sxA = new Float32Array(NV), syA = new Float32Array(NV);
  const LX = -.42, LY = -.52, LZ = .74, LL = Math.hypot(LX, LY, LZ);
  const SEGS = []; for (let j = 0; j < 6; j++) for (let c = 0; c < 8; c++) SEGS.push([j, c, j, c + 1]); for (let c = 0; c < 9; c++) for (let j = 0; j < 5; j++) SEGS.push([j, c, j + 1, c]);
  // node appearance times (seconds) for the emergence shot; a diagonal sweep with jitter, shared with the audio cues
  const NODE_T = []; for (let j = 0; j < 6; j++) for (let c = 0; c < 9; c++) NODE_T.push(1.15 + 3.4 * (0.5 * (c / 8) + 0.5 * (j / 5)) * .85 + .55 * hash(j * 9 + c + 3));
  function drawSurface(cam, o) {
    const alpha = o.alpha == null ? 1 : o.alpha; if (alpha <= 0 && !(o.nodesA > 0) && !(o.latA > 0)) return;
    const { pos, r, u, f, foc } = cam; const xf = o.xf || { s: 1, ox: 0, oy: 0, oz: 0 }, xs = xf.s;
    const xw = w => [w[0] * xs + xf.ox, w[1] * xs + xf.oy, w[2] * xs + xf.oz];
    for (let n = 0; n < NV; n++) {
      const dx = VX[n] * xs + xf.ox - pos[0], dy = VY[n] * xs + xf.oy - pos[1], dz = VZ[n] * xs + xf.oz - pos[2];
      const a = dx * r[0] + dy * r[1] + dz * r[2], b = dx * u[0] + dy * u[1] + dz * u[2], c = dx * f[0] + dy * f[1] + dz * f[2];
      czA[n] = c; if (c > .05) { sxA[n] = W / 2 + cam.sx0 + foc * a / c; syA[n] = H / 2 + cam.sy0 - foc * b / c; }
    }
    const front = o.front == null ? 2 : o.front; let cnt = 0;
    const fogN = cam.d * .55, fogS = cam.d * 1.25;
    if (alpha > 0) for (let q = 0; q < NQ; q++) {
      const vis = clamp((front - QR[q] * .85) / .16); if (vis <= 0) continue;
      const j = (q / (NI - 1)) | 0, i = q - j * (NI - 1), a = j * NI + i, b = a + 1, c = a + NI + 1, d = a + NI;
      const z4 = Math.min(czA[a], czA[b], czA[c], czA[d]); if (z4 < .2) continue;
      keyQ[cnt] = (czA[a] + czA[b] + czA[c] + czA[d]) * .25; idxAll[cnt++] = q;
    }
    const showN = (o.nodesA || 0) > 0, showL = (o.latA || 0) > 0; const nodeP = [];
    if (showN || showL) for (let j = 0; j < 6; j++) for (let c = 0; c < 9; c++) { const w = xw(nodeW(j, c)); w[2] += .012; nodeP.push(proj(cam, w)); }
    if (showN) for (let n = 0; n < 54; n++) if (nodeP[n][2] > .2) { keyQ[cnt] = nodeP[n][2] - .035; idxAll[cnt++] = NQ + n; }
    if (showL) for (let s = 0; s < SEGS.length; s++) { const sg = SEGS[s], pa = nodeP[sg[0] * 9 + sg[1]], pb = nodeP[sg[2] * 9 + sg[3]]; if (pa[2] > .2 && pb[2] > .2) { keyQ[cnt] = (pa[2] + pb[2]) / 2 - .03; idxAll[cnt++] = NQ + 54 + s; } }
    const ord = new Array(cnt); for (let n = 0; n < cnt; n++) ord[n] = n; ord.sort((x, y) => keyQ[y] - keyQ[x]);
    ctx.save(); ctx.lineJoin = "round"; ctx.lineCap = "round";
    const lineA = (o.lineA == null ? 1 : o.lineA) * alpha, contA = (o.contA || 0) * alpha, rimA = o.rimA == null ? 1 : o.rimA, glow = o.glow || 0;
    const t = o.time || 0;
    for (let n = 0; n < ord.length; n++) {
      const id = idxAll[ord[n]];
      if (id < NQ) {
        const q = id, j = (q / (NI - 1)) | 0, i = q - j * (NI - 1), a = j * NI + i, b = a + 1, c = a + NI + 1, d = a + NI;
        const vis = clamp((front - QR[q] * .85) / .16) * alpha;
        const cxw = QX[q] * xs + xf.ox - pos[0], cyw = QY[q] * xs + xf.oy - pos[1], czw = QZ[q] * xs + xf.oz - pos[2], dl = Math.hypot(cxw, cyw, czw);
        const vn = -(QNX[q] * cxw + QNY[q] * cyw + QNZ[q] * czw) / dl; // N . V
        const diff = Math.max(0, (QNX[q] * LX + QNY[q] * LY + QNZ[q] * LZ) / LL), fog = clamp((dl - fogN) / fogS);
        const rim = Math.pow(1 - clamp(Math.abs(vn)), 3) * rimA;
        const br = clamp(.08 + .52 * diff + .20 * clamp(vn)) * (1 - .42 * fog) * (1 + .35 * glow);
        const base = LUT[(Math.pow(QH[q], .82) * 255) | 0], k = clamp(br * .74);
        const R = lerp(SHADOW[0], base[0], k) + rim * 40, G = lerp(SHADOW[1], base[1], k) + rim * 120, B = lerp(SHADOW[2], base[2], k) + rim * 150;
        const col = `rgb(${R | 0},${G | 0},${B | 0})`;
        ctx.globalAlpha = vis * .96; ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = .9;
        ctx.beginPath(); ctx.moveTo(sxA[a], syA[a]); ctx.lineTo(sxA[b], syA[b]); ctx.lineTo(sxA[c], syA[c]); ctx.lineTo(sxA[d], syA[d]); ctx.closePath(); ctx.fill(); ctx.stroke();
        const la = lineA * clamp((front - QR[q] * .85) / .16) * (.5 + .5 * QH[q] + .25 * glow) * (1 - .45 * fog); // mesh lines on every second fine edge
        if (la > .01) {
          ctx.globalAlpha = Math.min(1, la); const hh = QH[q]; ctx.strokeStyle = `rgb(${lerp(70, 215, hh) | 0},${lerp(190, 252, hh) | 0},${lerp(255, 255, hh) | 0})`; ctx.lineWidth = 1.2; ctx.beginPath();
          if (j % 2 === 0) { ctx.moveTo(sxA[a], syA[a]); ctx.lineTo(sxA[b], syA[b]); }
          if (i % 2 === 0) { ctx.moveTo(sxA[a], syA[a]); ctx.lineTo(sxA[d], syA[d]); }
          if (j === NJ - 2) { ctx.moveTo(sxA[d], syA[d]); ctx.lineTo(sxA[c], syA[c]); }
          if (i === NI - 2) { ctx.moveTo(sxA[b], syA[b]); ctx.lineTo(sxA[c], syA[c]); }
          ctx.stroke();
        }
        if (j === 0 || i === 0 || j === NJ - 2 || i === NI - 2) { // border edges of the surface: brighter, a little thicker
          ctx.globalAlpha = Math.min(1, .95 * lineA * clamp((front - QR[q] * .85) / .16)); ctx.strokeStyle = "rgb(190,245,255)"; ctx.lineWidth = 2; ctx.beginPath();
          if (j === 0) { ctx.moveTo(sxA[a], syA[a]); ctx.lineTo(sxA[b], syA[b]); } if (i === 0) { ctx.moveTo(sxA[a], syA[a]); ctx.lineTo(sxA[d], syA[d]); }
          if (j === NJ - 2) { ctx.moveTo(sxA[d], syA[d]); ctx.lineTo(sxA[c], syA[c]); } if (i === NI - 2) { ctx.moveTo(sxA[b], syA[b]); ctx.lineTo(sxA[c], syA[c]); } ctx.stroke();
        }
        if (contA > .01) { // iso-IV contours
          for (let lv = 25; lv <= 65; lv += 5) {
            if (lv < QMIN[q] || lv > QMAX[q]) continue; const major = lv % 10 === 0;
            ctx.globalAlpha = Math.min(1, contA * clamp((front - QR[q] * .85) / .16) * (major ? .95 : .5) * (1 - .45 * fog)); ctx.strokeStyle = major ? "rgb(225,252,255)" : "rgb(150,225,255)"; ctx.lineWidth = major ? 1.7 : 1.1; ctx.beginPath();
            contourTri(a, b, c, lv, sxA, syA); contourTri(a, c, d, lv, sxA, syA); ctx.stroke();
          }
        }
      } else if (id < NQ + 54) {
        const nn = id - NQ, j = (nn / 9) | 0, c = nn % 9, p = nodeP[nn]; const st = N.status[j][c];
        const s = o.nodeAppear ? eout(clamp((t - NODE_T[nn]) / .7)) : 1; if (s <= 0) continue;
        const rad = clamp(foc * .0066 / p[2] * (.7 + .3 * s), 2, 6) * (o.nodeScale || 1);
        const lift = o.nodeAppear ? (1 - s) * .22 : 0; const pp = lift ? proj(cam, (() => { const w = xw(nodeW(j, c)); w[2] += .012 + lift; return w; })()) : p;
        const al = s * (o.nodesA || 0);
        const halo = ctx.createRadialGradient(pp[0], pp[1], 0, pp[0], pp[1], rad * 3.4); halo.addColorStop(0, `rgba(150,240,255,${.5 * al})`); halo.addColorStop(1, "rgba(150,240,255,0)");
        ctx.globalAlpha = 1; ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(pp[0], pp[1], rad * 3.4, 0, 7); ctx.fill();
        if (st === 3) { ctx.globalAlpha = al; ctx.fillStyle = "#e9fdff"; ctx.beginPath(); ctx.arc(pp[0], pp[1], rad, 0, 7); ctx.fill(); }
        else { ctx.globalAlpha = al; ctx.strokeStyle = "#a8ecff"; ctx.lineWidth = 1.8; ctx.beginPath(); ctx.arc(pp[0], pp[1], rad * 1.05, 0, 7); ctx.stroke(); ctx.fillStyle = "rgba(5,10,24,.9)"; ctx.beginPath(); ctx.arc(pp[0], pp[1], rad * .6, 0, 7); ctx.fill(); }
      } else {
        const sg = SEGS[id - NQ - 54], pa = nodeP[sg[0] * 9 + sg[1]], pb = nodeP[sg[2] * 9 + sg[3]];
        const k0 = sg[0] * 9 + sg[1], k1 = sg[2] * 9 + sg[3]; const s = o.nodeAppear ? Math.min(clamp((t - NODE_T[k0] - .5) / .8), clamp((t - NODE_T[k1] - .5) / .8)) : 1; if (s <= 0) continue;
        ctx.globalAlpha = (o.latA || 0) * s * .75; ctx.strokeStyle = "rgb(140,225,255)"; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(pa[0], pa[1]); ctx.lineTo(pb[0] * s + pa[0] * (1 - s), pb[1] * s + pa[1] * (1 - s)); ctx.stroke();
      }
    }
    ctx.restore();
  }

  window.E = { W, H, ctx, cv, N, clamp, lerp, sstep, eio, eout, hash, K, camAt, makeCam, proj, toCam, scr, line3, seg3, drawBackground, post, label, drawBox, drawAxisLabels, drawSurface, nodeW, kx, ty, vz, XW, YW, ZH, NODE_T, FONT, LUT };
})();
