// Zero-dependency frame capture: drives the local Chrome over the DevTools protocol (Node >= 22 global WebSocket).
//   node render.mjs stills <outDir> <t1,t2,...>            PNG of index.html at the given seconds
//   node render.mjs frames <outDir> <from> <to> [port]     frames from..to-1 at 30 fps (index.html, 1920x1080)
//   node render.mjs events <out.json>                      dump window.EVENTS (audio cue times)
//   node render.mjs shot <url> <out.png> <w> <h> <dsf> <waitMs> [js]   screenshot of any page (application capture)
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const TMP = process.env.NVS_TMP || path.join(HERE, "out", "tmp");
const FPS = 30;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function launch(port, w, h, dsf) {
  const dir = path.join(TMP, "profile_" + port);
  fs.mkdirSync(dir, { recursive: true });
  const proc = spawn(CHROME, ["--headless=new", `--remote-debugging-port=${port}`, `--user-data-dir=${dir}`, `--window-size=${w},${h}`,
    "--hide-scrollbars", `--force-device-scale-factor=${dsf}`, "--allow-file-access-from-files", "--no-first-run",
    "--no-default-browser-check", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "about:blank"], { stdio: "ignore" });
  for (let i = 0; i < 100; i++) {
    try { const r = await fetch(`http://127.0.0.1:${port}/json/list`); const l = await r.json(); const pg = l.find(x => x.type === "page"); if (pg) return { proc, ws: pg.webSocketDebuggerUrl }; } catch {}
    await sleep(150);
  }
  throw new Error("chrome did not start");
}

function client(wsUrl) {
  const ws = new WebSocket(wsUrl); let id = 0; const pend = new Map(); const waiters = [];
  ws.onmessage = ev => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { const { res, rej } = pend.get(m.id); pend.delete(m.id); m.error ? rej(new Error(JSON.stringify(m.error))) : res(m.result); } else if (m.method) waiters.slice().forEach(w => w(m)); };
  const ready = new Promise(r => (ws.onopen = r));
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  const once = name => new Promise(r => { const f = m => { if (m.method === name) { waiters.splice(waiters.indexOf(f), 1); r(m); } }; waiters.push(f); });
  return { ready, send, once, close: () => ws.close() };
}

async function open(url, w, h, dsf, port) {
  const { proc, ws } = await launch(port, w, h, dsf);
  const c = client(ws); await c.ready;
  await c.send("Page.enable"); await c.send("Runtime.enable");
  await c.send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: dsf, mobile: false });
  const loaded = c.once("Page.loadEventFired");
  await c.send("Page.navigate", { url }); await loaded;
  const ev = async (expression) => { const r = await c.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }); if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 600)); return r.result.value; };
  const snap = async file => { const r = await c.send("Page.captureScreenshot", { format: "png", fromSurface: true }); fs.writeFileSync(file, Buffer.from(r.data, "base64")); };
  const close = () => { c.close(); proc.kill(); };
  return { ev, snap, close };
}

const [, , mode, ...a] = process.argv;
const page = pathToFileURL(path.join(HERE, "index.html")).href;

if (mode === "stills") {
  const [dir, ts] = a; fs.mkdirSync(dir, { recursive: true });
  const p = await open(page, 1920, 1080, 1, 9401); await p.ev("window.READY");
  for (const t of ts.split(",")) { await p.ev(`renderFrame(${t})`); await p.snap(path.join(dir, `t_${Number(t).toFixed(2).padStart(6, "0")}.png`)); }
  p.close();
} else if (mode === "frames") {
  const [dir, from, to, port = "9402"] = a; fs.mkdirSync(dir, { recursive: true });
  const p = await open(page, 1920, 1080, 1, Number(port)); await p.ev("window.READY");
  const t0 = Date.now();
  for (let n = Number(from); n < Number(to); n++) {
    await p.ev(`renderFrame(${(n / FPS).toFixed(5)})`); await p.snap(path.join(dir, `f_${String(n).padStart(5, "0")}.png`));
    if (n % 30 === 0) console.log(`frame ${n} (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
  }
  p.close();
} else if (mode === "events") {
  const p = await open(page, 1920, 1080, 1, 9403); await p.ev("window.READY");
  fs.writeFileSync(a[0], JSON.stringify(await p.ev("window.EVENTS")));
  p.close();
} else if (mode === "eval") {
  const p = await open(page, 1920, 1080, 1, 9405); await p.ev("window.READY");
  console.log(JSON.stringify(await p.ev(a[0]))); p.close();
} else if (mode === "shot") {
  const [url, out, w, h, dsf, wait, js] = a;
  const p = await open(url, Number(w), Number(h), Number(dsf), 9404);
  await sleep(Number(wait)); if (js) { await p.ev(js); await sleep(1500); }
  await p.snap(out); p.close();
} else { console.error("modes: stills | frames | events | shot"); process.exit(2); }
process.exit(0);
