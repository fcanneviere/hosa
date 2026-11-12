#!/usr/bin/env node
// Captures et contrôles machine des écrans d'un projet Hosa. Node 22+ et un Chrome, Chromium ou Edge local.
// Lancé par `<hosa> capture` (capture.py), qui lit les routes du plan de navigation. `--help` : le mode d'emploi.
// Le pilotage du navigateur est adapté de shoot.mjs d'oil-ui (https://github.com/oil-oil/oil-ui,
// licence MIT, © 2026 oil-oil, voir ../NOTICE-oil-ui.md) ; les contrôles d'accessibilité, les routes et le verdict sont de Hosa.
import { spawn, spawnSync } from "node:child_process";
import { createServer } from "node:http";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, realpathSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { basename, dirname, extname, isAbsolute, join, relative, resolve, sep } from "node:path";

const HELP = `Usage : capture <adresse ou fichier> [options]

  --out <dossier>        dossier de sortie, par défaut ./captures
  --size <LxH,...>       fenêtres, par défaut 390x844,1280x900
  --routes </a,/b,...>   capture chaque route de l'adresse de base ; compte les routes rendues
  --connexion "<actions>" actions jouées une fois avant les routes, pour se connecter :
                         "goto /connexion; type #email a@b.fr; type #mdp secret; click button[type=submit]; wait 800"
  --states <a,b,...>     ouvre ?state=<nom> pour chaque état et le capture
  --param <nom>          nom du paramètre d'état, par défaut state
  --steps "<actions>"    actions avant chaque capture, séparées par des points-virgules :
                         click <sél> | hover <sél> | type <sél> <texte> | key <touche> | scroll <dy> | wait <ms>
                         | goto <route ou adresse>
                         un sélecteur avec des espaces se met entre guillemets : click ".nav .item"
  --sheet                planche des états côte à côte
  --mark "1=<sél>;..."   capture annotée : un cadre numéroté par groupe d'éléments
  --mask                 capture où tout le texte est masqué (lire la composition)
  --full                 page entière ; par défaut, la fenêtre seule
  --zoom <facteur>       densité de pixels, par défaut 1
  --wait <ms>            attente après le chargement, par défaut 400
  --sans-a11y            sans les contrôles d'accessibilité

Chaque capture est contrôlée : erreurs de script, de console et de chargement, statut HTTP, redirection,
débordement horizontal, images cassées, et accessibilité (contraste WCAG AA du texte, images sans alt,
champs sans libellé, boutons et liens sans nom, langue de la page, cibles tactiles de moins de 24 px en mobile).
La dernière ligne est le verdict ; le détail est dans report.json. Code : 0 sans problème, 1 sinon.`;

const args = process.argv.slice(2);
if (!args.length || args.includes("--help") || args.includes("-h")) {
  console.log(HELP);
  process.exit(args.length ? 0 : 2);
}
if (typeof WebSocket !== "function") fail("Node 22 ou plus récent requis.", 2);

const opt = { out: "captures", size: "390x844,1280x900", param: "state", zoom: "1", wait: "400" };
const options = [...HELP.matchAll(/^  (--[\w-]+)/gm)].map((m) => m[1]);
const BOOL = ["--full", "--mask", "--sheet", "--sans-a11y"];
const flags = new Set();
let target = null;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === "--force") continue;
  if (BOOL.includes(a)) flags.add(a.slice(2));
  else if (a.startsWith("--")) {
    if (!options.includes(a)) fail(`option inconnue ${a}\noptions : ${options.join(" ")}`, 2);
    if (i + 1 >= args.length || args[i + 1].startsWith("--")) fail(`${a} attend une valeur`, 2);
    opt[a.slice(2)] = args[++i];
  } else if (target) fail(`une seule adresse ou un seul fichier : ${target}, ${a}`, 2);
  else target = a;
}
if (!target) fail("adresse ou fichier manquant.", 2);

const sizes = opt.size.split(",").map((s) => {
  const m = s.trim().match(/^(\d+)x(\d+)$/);
  if (!m) fail(`taille au format LxH, par exemple 390x844 : ${s}`, 2);
  return { w: +m[1], h: +m[2] };
});
const routes = opt.routes ? opt.routes.split(",").map((s) => s.trim()).filter(Boolean) : null;
const states = opt.states ? opt.states.split(",").map((s) => s.trim()).filter(Boolean) : [null];
const safe = (s, i, prefix) => /^[A-Za-z0-9_-]{1,80}$/.test(s) ? s : `${prefix}-${i + 1}-${createHash("sha256").update(s).digest("hex").slice(0, 10)}`;
const stateIds = states.map((s, i) => !s ? "" : safe(s, i, "etat"));
const routeId = (r, i) => { const s = r.replace(/^\/+|\/+$/g, "").replace(/[^A-Za-z0-9_-]+/g, "-"); return s ? safe(s.slice(0, 80), i, "route") : "accueil"; };
const zoom = Number(opt.zoom) || 1;
const out = resolve(opt.out);
mkdirSync(out, { recursive: true });

function fail(message, code = 1) {
  console.error(`capture : ${message}`);
  process.exit(code);
}

// ---------- Fichier local : servi en local pour que modules et fetch marchent ; rien hors du dossier ----------
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
  ".webp": "image/webp", ".gif": "image/gif", ".avif": "image/avif", ".woff2": "font/woff2", ".woff": "font/woff",
  ".ttf": "font/ttf", ".otf": "font/otf", ".mp4": "video/mp4", ".webm": "video/webm", ".txt": "text/plain; charset=utf-8",
  ".wasm": "application/wasm", ".ico": "image/x-icon", ".csv": "text/csv; charset=utf-8", ".pdf": "application/pdf",
};
const privatePath = (p) => p.split(/[\\/]/).some((part) => part.startsWith(".")
  || /^(?:credentials?|secrets?|id_(?:rsa|dsa|ecdsa|ed25519))(?:[._-]|$)/i.test(part));
let server = null;
const notFound = (res) => res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("404 introuvable");
async function resolveTarget(t) {
  if (/^https?:\/\//.test(t)) return t;
  const file = resolve(t);
  if (!existsSync(file)) fail(`fichier introuvable : ${t}`, 2);
  const root = realpathSync(statSync(file).isDirectory() ? file : dirname(file));
  const page = statSync(file).isDirectory() ? "index.html" : basename(file);
  server = createServer((req, res) => {
    try {
      const origin = `http://127.0.0.1:${server.address().port}`;
      const url = new URL(req.url, origin);
      if (req.headers.host !== new URL(origin).host || !["GET", "HEAD"].includes(req.method)) { res.writeHead(404).end(); return; }
      const path = decodeURIComponent(url.pathname);
      if (privatePath(path)) { res.writeHead(404).end(); return; }
      const local = realpathSync(resolve(join(root, path)));
      const rel = relative(root, local);
      const type = MIME[extname(local).toLowerCase()];
      if (rel === ".." || rel.startsWith(`..${sep}`) || isAbsolute(rel) || privatePath(rel) || !type || !statSync(local).isFile()) {
        notFound(res); return;
      }
      res.writeHead(200, { "Content-Type": type, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store" });
      res.end(req.method === "HEAD" ? undefined : readFileSync(local));
    } catch { notFound(res); }
  });
  await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
  return `http://127.0.0.1:${server.address().port}/${encodeURIComponent(page)}`;
}

// ---------- Navigateur isolé et invisible, profil jetable ----------
function findChrome() {
  const env = process.env.CHROME_PATH;
  if (env && existsSync(env)) return env;
  const candidates = {
    darwin: ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
    win32: [`${process.env.PROGRAMFILES}\\Google\\Chrome\\Application\\chrome.exe`,
      `${process.env["PROGRAMFILES(X86)"]}\\Google\\Chrome\\Application\\chrome.exe`,
      `${process.env.LOCALAPPDATA}\\Google\\Chrome\\Application\\chrome.exe`,
      `${process.env["PROGRAMFILES(X86)"]}\\Microsoft\\Edge\\Application\\msedge.exe`],
  }[process.platform] || [];
  for (const c of candidates) if (c && existsSync(c)) return c;
  if (process.platform !== "win32") for (const name of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]) {
    const r = spawnSync("which", [name], { encoding: "utf8" });
    if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
  }
  fail("Chrome, Chromium ou Edge introuvable : indique son chemin dans CHROME_PATH, ou demande-le en `## Installation nécessaire`.", 3);
}

const profile = mkdtempSync(join(tmpdir(), "hosa-capture-"));
const chrome = spawn(findChrome(), [
  "--headless=new", "--enable-unsafe-swiftshader", "--remote-debugging-port=0", `--user-data-dir=${profile}`, "--no-first-run",
  "--no-default-browser-check", "--hide-scrollbars", "--mute-audio", "--disable-extensions", "about:blank",
], { stdio: ["ignore", "ignore", "pipe"], windowsHide: true });

let cleaning;
function cleanup() {
  return cleaning ||= (async () => {
    if (chrome.exitCode === null && chrome.signalCode === null) {
      await new Promise((ok) => {
        const timer = setTimeout(() => { chrome.kill("SIGKILL"); ok(); }, 3000);
        chrome.once("close", () => { clearTimeout(timer); ok(); });
        chrome.kill();
      });
    }
    server?.close();
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
  })();
}
process.on("exit", () => { try { chrome.kill(); } catch {} try { server?.close(); } catch {} try { rmSync(profile, { recursive: true, force: true }); } catch {} });
process.on("SIGINT", async () => { await cleanup(); process.exit(130); });
process.on("SIGTERM", async () => { await cleanup(); process.exit(143); });
chrome.on("error", (e) => fail(`le navigateur ne démarre pas : ${e.message}`, 3));

const wsUrl = await new Promise((ok) => {
  let buf = "";
  const timer = setTimeout(() => fail("le navigateur n'a pas démarré en 15 secondes.", 3), 15000);
  chrome.stderr.on("data", (d) => {
    buf += d;
    const m = buf.match(/DevTools listening on (ws:\/\/\S+)/);
    if (m) { clearTimeout(timer); ok(m[1]); }
  });
});

// ---------- Protocole Chrome DevTools ----------
const ws = new WebSocket(wsUrl);
await new Promise((ok, no) => { ws.onopen = ok; ws.onerror = () => no(new Error("connexion au navigateur impossible")); });
let seq = 0;
const pending = new Map();
const listeners = [];
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.id && pending.has(msg.id)) {
    const { ok, no } = pending.get(msg.id);
    pending.delete(msg.id);
    msg.error ? no(new Error(msg.error.message)) : ok(msg.result);
  } else if (msg.method) listeners.forEach((fn) => fn(msg));
};
const send = (method, params = {}, sessionId) => new Promise((ok, no) => {
  const id = ++seq;
  pending.set(id, { ok, no });
  ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
});
const { targetId } = await send("Target.createTarget", { url: "about:blank" });
const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
const cdp = (method, params) => send(method, params, sessionId);
await cdp("Page.enable");
await cdp("Runtime.enable");
await cdp("Log.enable");
await cdp("Network.enable");

let problems = [];
let docStatus = null;
listeners.push((m) => {
  if (m.sessionId !== sessionId) return;
  if (m.method === "Runtime.exceptionThrown") problems.push(`erreur de script : ${m.params.exceptionDetails?.exception?.description?.split("\n")[0] || m.params.exceptionDetails?.text}`);
  if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") problems.push(`erreur de console : ${m.params.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 200)}`);
  if (m.method === "Log.entryAdded" && m.params.entry.level === "error" && !/favicon\.ico/.test(m.params.entry.url || "")) problems.push(`erreur de chargement : ${m.params.entry.text.slice(0, 200)} ${m.params.entry.url || ""}`.trim());
  if (m.method === "Network.responseReceived" && m.params.type === "Document" && m.params.frameId === targetId) docStatus = m.params.response.status;
});

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
// Une page d'erreur du navigateur change de processus : le premier appel peut tomber entre deux, on réessaie.
const evaluate = async (expression, tries = 4) => {
  let r;
  try { r = await cdp("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }); } catch (e) {
    if (tries > 1 && /attached|context|target/i.test(e.message)) { await sleep(300); return evaluate(expression, tries - 1); }
    throw e;
  }
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};

async function setViewport(w, h, scale) {
  await cdp("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: scale, mobile: w < 600 });
  await cdp("Emulation.setTouchEmulationEnabled", { enabled: w < 600 });
}

async function open(url) {
  docStatus = null;
  const loaded = new Promise((ok) => {
    const fn = (m) => { if (m.sessionId === sessionId && m.method === "Page.loadEventFired") { listeners.splice(listeners.indexOf(fn), 1); ok(); } };
    listeners.push(fn);
  });
  const nav = await cdp("Page.navigate", { url });
  if (nav.errorText) throw new Error(`impossible d'ouvrir ${url} : ${nav.errorText}`);
  await Promise.race([loaded, sleep(15000)]);
  await evaluate(`document.fonts ? document.fonts.ready.then(() => true) : true`);
  await sleep(Number(opt.wait));
}

// Contrôles dans la page : rendu, mise en page, accessibilité. Chaque problème nomme l'élément (sélecteur court).
const CHECK = (a11y, mobile) => `(() => {
  const out = [];
  const doc = document.documentElement;
  const name = (el) => el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") +
    (typeof el.className === "string" && el.className.trim() ? "." + el.className.trim().split(/\\s+/).slice(0, 2).join(".") : "");
  const say = (el) => { const t = (el.innerText || el.value || "").trim().replace(/\\s+/g, " "); return t ? " « " + t.slice(0, 40) + " »" : ""; };
  const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && r.right > 0 && r.bottom > 0 && s.visibility !== "hidden" && s.display !== "none" && +s.opacity > 0.05; };
  if (doc.scrollWidth > innerWidth + 1) out.push("débordement horizontal : page de " + doc.scrollWidth + " px pour une fenêtre de " + innerWidth + " px");
  for (const img of document.images) if (img.complete && img.naturalWidth === 0) out.push("image cassée : " + (img.getAttribute("src") || "").slice(0, 120));
  if (!(document.body && document.body.innerText.trim())) out.push("page vide : aucun texte rendu");
  if (!${a11y}) return out;
  if (!doc.lang) out.push("langue de la page absente (<html lang>)");
  const canvas = document.createElement("canvas"); canvas.width = canvas.height = 1;
  const ctx = canvas.getContext("2d", { willReadFrequently: true });
  const rgba = (c) => { ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = "#000"; ctx.fillStyle = c; ctx.fillRect(0, 0, 1, 1); const d = ctx.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
  const over = (top, under) => top.slice(0, 3).map((v, i) => v * top[3] + under[i] * (1 - top[3])).concat(1);
  const bgOf = (el) => { const layers = []; for (let n = el; n; n = n.parentElement) { const s = getComputedStyle(n);
      if (s.backgroundImage !== "none") return null; const c = rgba(s.backgroundColor); if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let base = [255, 255, 255, 1]; for (const c of layers.reverse()) base = over(c, base); return base; };
  const lum = (c) => { const [r, g, b] = c.slice(0, 3).map((v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; }); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
  const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
  const hex = (c) => "#" + c.slice(0, 3).map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const seen = new Set(); let n = 0;
  const walker = document.createTreeWalker(document.body || doc, NodeFilter.SHOW_TEXT);
  while (walker.nextNode() && n < 12) {
    const el = walker.currentNode.parentElement;
    if (!el || seen.has(el) || !walker.currentNode.textContent.trim() || !visible(el) || el.closest("[disabled],[aria-disabled=true],[aria-hidden=true]")) continue;
    seen.add(el);
    const s = getComputedStyle(el); const bg = bgOf(el); if (!bg) continue;
    const fg = over(rgba(s.color), bg); const size = parseFloat(s.fontSize); const bold = +s.fontWeight >= 700;
    const need = size >= 24 || (size >= 18.66 && bold) ? 3 : 4.5; const r = ratio(fg, bg);
    if (r < need) { n++; out.push("contraste " + r.toFixed(2) + ":1 < " + need + ":1 : " + name(el) + say(el) + " (" + hex(fg) + " sur " + hex(bg) + ")"); }
  }
  for (const img of document.images) if (visible(img) && !img.hasAttribute("alt")) out.push("image sans alt : " + name(img) + " " + (img.getAttribute("src") || "").slice(0, 60));
  const labelled = (el) => el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title") || (el.labels && el.labels.length);
  for (const el of document.querySelectorAll("input:not([type=hidden]):not([type=submit]):not([type=button]),select,textarea"))
    if (visible(el) && !labelled(el)) out.push("champ sans libellé : " + name(el) + (el.name ? " [name=" + el.name + "]" : ""));
  for (const el of document.querySelectorAll("button,a[href],[role=button]")) {
    if (!visible(el)) continue;
    const accessible = (el.innerText || "").trim() || el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title") || el.querySelector("img[alt]:not([alt=''])");
    if (!accessible) out.push((el.tagName === "A" ? "lien" : "bouton") + " sans nom accessible : " + name(el));
    if (${mobile}) { const r = el.getBoundingClientRect(); if ((r.width < 24 || r.height < 24) && !el.closest("p,li,td")) out.push("cible tactile " + Math.round(r.width) + "×" + Math.round(r.height) + " px < 24 px : " + name(el) + say(el)); }
  }
  return out;
})()`;

async function check(w) {
  const found = await evaluate(CHECK(!flags.has("sans-a11y"), w < 600));
  return [...new Set([...problems, ...found])];
}

async function screenshot(file, full) {
  let clip;
  if (full) {
    const { contentSize } = await cdp("Page.getLayoutMetrics");
    clip = { x: 0, y: 0, width: Math.ceil(contentSize.width), height: Math.ceil(contentSize.height), scale: 1 };
  }
  const { data } = await cdp("Page.captureScreenshot", { format: "png", captureBeyondViewport: !!full, ...(clip ? { clip } : {}) });
  writeFileSync(file, Buffer.from(data, "base64"));
  return file;
}

const MASK_CSS = `*,*::before,*::after{text-shadow:none!important;-webkit-text-fill-color:transparent!important;caret-color:transparent!important}
::placeholder{color:transparent!important}svg text,svg tspan{fill:transparent!important;stroke:transparent!important}`;
const mask = () => evaluate(`(() => { const s = document.createElement("style"); s.id = "hosa-mask"; s.textContent = ${JSON.stringify(MASK_CSS)}; document.head.append(s); return true; })()`);
const unmask = () => evaluate(`(document.getElementById("hosa-mask")?.remove(), true)`);

const marks = (opt.mark ? opt.mark.split(";").map((s) => s.trim()).filter(Boolean) : []).map((s, i) => {
  const m = s.match(/^(\d+)\s*=\s*(.+)$/);
  return m ? { label: m[1], selector: m[2].trim() } : { label: String(i + 1), selector: s };
});
async function mark() {
  const missing = await evaluate(`((selectors) => {
    const layer = document.createElement("div");
    layer.id = "hosa-mark";
    layer.style.cssText = "position:absolute;left:0;top:0;width:0;height:0;z-index:2147483647;pointer-events:none";
    const missing = [];
    selectors.forEach(({ label, selector }) => {
      let found;
      try { found = [...document.querySelectorAll(selector)]; } catch { missing.push(selector + " (sélecteur invalide)"); return; }
      const boxes = found.map((el) => el.getBoundingClientRect()).filter((r) => r.width > 0 && r.height > 0);
      if (!boxes.length) { missing.push(selector + (found.length ? " (invisible)" : "")); return; }
      boxes.forEach((r, j) => {
        const box = document.createElement("div");
        box.style.cssText = "position:absolute;box-sizing:border-box;border:2px solid #e8175d;border-radius:3px;left:" + (r.left + scrollX - 4) + "px;top:" + (r.top + scrollY - 4) + "px;width:" + (r.width + 8) + "px;height:" + (r.height + 8) + "px";
        if (j === 0) {
          const small = r.width < 48 || r.height < 28;
          const pos = !small ? "left:-12px;top:-12px" : r.left + scrollX - 34 >= 0 ? "left:-30px;top:" + (r.height / 2 - 7) + "px" : "right:-30px;top:" + (r.height / 2 - 7) + "px";
          const tag = document.createElement("span");
          tag.textContent = label;
          tag.style.cssText = "position:absolute;" + pos + ";min-width:22px;height:22px;padding:0 6px;box-sizing:border-box;border-radius:11px;background:#e8175d;color:#fff;font:600 13px/22px system-ui,sans-serif;text-align:center;box-shadow:0 0 0 2px #fff";
          box.append(tag);
        }
        layer.append(box);
      });
    });
    document.body.append(layer);
    return missing;
  })(${JSON.stringify(marks)})`);
  if (missing.length) throw new Error(`--mark : introuvable : ${missing.join(" ; ")}`);
}
const unmark = () => evaluate(`(document.getElementById("hosa-mark")?.remove(), true)`);

function tokenize(text) { return [...text.matchAll(/"([^"]*)"|'([^']*)'|(\S+)/g)].map((m) => m[1] ?? m[2] ?? m[3]); }
const KEYS = { ArrowUp: 38, ArrowDown: 40, ArrowLeft: 37, ArrowRight: 39, Enter: 13, Escape: 27, Tab: 9, " ": 32, Space: 32, Home: 36, End: 35, PageUp: 33, PageDown: 34, Backspace: 8 };
async function center(selector) {
  const box = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); if (!el) return null; el.scrollIntoView({ block: "center", inline: "center" }); const r = el.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
  if (!box) throw new Error(`élément introuvable : ${selector}`);
  return box;
}
const mouse = (type, x, y, extra = {}) => cdp("Input.dispatchMouseEvent", { type, x, y, button: "left", pointerType: "mouse", ...extra });
async function runSteps(text) {
  for (const raw of (text || "").split(";").map((s) => s.trim()).filter(Boolean)) {
    const [verb, ...rest] = tokenize(raw);
    const arity = { click: 1, hover: 1 }[verb];
    if (arity && rest.length !== arity) throw new Error(`action mal formée : ${raw}. Sélecteur avec des espaces : entre guillemets, ${verb} ".nav .item"`);
    if (verb === "wait") await sleep(Number(rest[0]) || 0);
    else if (verb === "goto") await open(new URL(rest[0] || "/", base).toString());
    else if (verb === "click") { const p = await center(rest[0]); await mouse("mouseMoved", p.x, p.y); await mouse("mousePressed", p.x, p.y, { clickCount: 1 }); await mouse("mouseReleased", p.x, p.y, { clickCount: 1 }); await sleep(150); }
    else if (verb === "hover") { const p = await center(rest[0]); await mouse("mouseMoved", p.x, p.y); await sleep(200); }
    else if (verb === "type") {
      await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(rest[0])}); if (!el) throw new Error(${JSON.stringify("élément introuvable : " + rest[0])}); el.focus(); return true; })()`);
      await cdp("Input.insertText", { text: rest.slice(1).join(" ") }); await sleep(120);
    } else if (verb === "key") {
      const key = rest[0] === "Space" ? " " : rest[0]; const code = KEYS[rest[0]] ?? key.toUpperCase().charCodeAt(0);
      await cdp("Input.dispatchKeyEvent", { type: "keyDown", key, code: rest[0], windowsVirtualKeyCode: code });
      await cdp("Input.dispatchKeyEvent", { type: "keyUp", key, code: rest[0], windowsVirtualKeyCode: code }); await sleep(80);
    } else if (verb === "scroll") { await evaluate(`scrollBy(0, ${Number(rest[0]) || 0}), true`); await sleep(200); }
    else throw new Error(`action inconnue : ${raw}`);
  }
}

async function sheet(items, file, w, h) {
  const cell = Math.min(w, 420);
  const esc = (t) => String(t).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const figures = items.map(({ path, label }) => `<figure><img src="data:image/png;base64,${readFileSync(path).toString("base64")}"><figcaption>${esc(label)}</figcaption></figure>`).join("");
  const page = `<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'"><style>body{margin:0;padding:32px;background:#ececea;font:13px system-ui,sans-serif;color:#444}main{display:flex;gap:24px;align-items:flex-start}figure{margin:0;width:${cell}px}img{width:100%;display:block;border-radius:10px;box-shadow:0 1px 3px #0002}figcaption{margin-top:8px}</style><main>${figures}</main>`;
  const tmp = join(profile, "planche.html");
  writeFileSync(tmp, page);
  await setViewport(items.length * cell + (items.length - 1) * 24 + 64, Math.round((cell * h) / w) + 110, 1);
  await open(`file://${tmp}`);
  return screenshot(file, true);
}

// ---------- Programme principal ----------
const base = await resolveTarget(target);
const pageUrl = (route, state) => {
  const u = route ? new URL(route, base) : new URL(base);
  if (state) u.searchParams.set(opt.param, state);
  return u.toString();
};
const report = [];
const lines = [];
const rendered = new Map(); // route → raison du non-rendu, ou "" si rendue
try {
  if (opt.connexion) {
    await setViewport(sizes.at(-1).w, sizes.at(-1).h, 1);
    await open(base);
    await runSteps(opt.connexion);
    await sleep(500);
  }
  for (const [ri, route] of (routes || [null]).entries()) {
    for (const { w, h } of sizes) {
      const shots = [], masked = [];
      for (const [si, s] of states.entries()) {
        problems = [];
        await setViewport(w, h, zoom);
        const url = pageUrl(route, s);
        let issues = [];
        try {
          await open(url);
          if (opt.steps) await runSteps(opt.steps);
        } catch (e) { issues.push(e.message); }
        const name = [route !== null ? routeId(route, ri) : "", stateIds[si], `${w}x${h}`, zoom !== 1 ? `@${zoom}x` : ""].filter(Boolean).join("-") || "page";
        let file = null;
        try {  // une capture qui échoue est un problème de cette capture, jamais l'arrêt des suivantes
          if (docStatus && docStatus >= 400) issues.push(`HTTP ${docStatus}`);
          file = await screenshot(join(out, `${name}.png`), flags.has("full"));
          const landed = await evaluate("location.pathname").catch(() => null);
          const wanted = new URL(url).pathname;
          if (route !== null && landed && landed.replace(/\/$/, "") !== wanted.replace(/\/$/, "")) issues.push(`redirigé vers ${landed}`);
          issues = [...issues, ...(await check(w))];
          if (marks.length) { await mark(); lines.push(basename(await screenshot(join(out, `${name}-marque.png`), flags.has("full")))); await unmark(); }
          if (flags.has("mask")) { await mask(); await sleep(60); masked.push({ path: await screenshot(join(out, `${name}-masque.png`), flags.has("full")), label: s || "page" }); await unmask(); }
        } catch (e) { issues.push(`capture impossible : ${e.message}`); }
        if (route !== null) {
          const blocking = issues.find((x) => /^(HTTP |redirigé|page vide|erreur de script|impossible d'ouvrir|capture impossible)/.test(x));
          if (!rendered.has(route) || blocking) rendered.set(route, blocking || rendered.get(route) || "");
        }
        report.push({ file: file && basename(file), route, state: s, size: `${w}x${h}`, zoom, status: docStatus, issues });
        if (file) shots.push({ path: file, label: s || route || "page" });
        lines.push(`${file ? basename(file) : name}${issues.length ? "  ⚠ " + issues.join(" ; ") : ""}`);
      }
      if (flags.has("sheet") && shots.length > 1) {
        const prefix = route !== null ? routeId(route, ri) + "-" : "";
        lines.push(basename(await sheet(shots, join(out, `${prefix}planche-${w}x${h}.png`), w, h)));
        if (masked.length) lines.push(basename(await sheet(masked, join(out, `${prefix}planche-${w}x${h}-masque.png`), w, h)));
      }
    }
  }
} catch (error) {
  console.error(`capture : ${error.message}`);
  process.exitCode = 1;
}
const routesOk = [...rendered.values()].filter((v) => !v).length;
writeFileSync(join(out, "report.json"), JSON.stringify({ routes: routes ? { rendues: routesOk, total: routes.length,
  echecs: Object.fromEntries([...rendered].filter(([, v]) => v)) } : null, captures: report }, null, 2));
console.log(`Dossier : ${out}`);
for (const l of lines) if (/⚠/.test(l) || lines.length <= 12) console.log(`- ${l}`);
const total = report.reduce((n, r) => n + r.issues.length, 0);
if (routes) console.log(`Routes rendues : ${routesOk} / ${routes.length}${routesOk < routes.length ? " — " + [...rendered].filter(([, v]) => v).map(([r, v]) => `${r} (${v})`).join(" ; ") : ""}`);
console.log(total || (routes && routesOk < routes.length)
  ? `Verdict : ${total} problème(s) sur ${report.length} capture(s), détail dans report.json`
  : `Verdict : OK — ${report.length} capture(s), aucun problème`);
if (total || (routes && routesOk < routes.length)) process.exitCode ||= 1;
ws.close();
await cleanup();
process.exit(process.exitCode || 0);
