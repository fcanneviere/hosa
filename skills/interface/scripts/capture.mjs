#!/usr/bin/env node
// Captures d'écran et contrôles machine des écrans d'un projet Hosa. Node 22+ et un Chrome, Chromium ou Edge local.
// Lancé par `<hosa> capture` (capture.py), qui lit les routes du plan de navigation. `--help` : le mode d'emploi.
// Le navigateur est piloté par le protocole DevTools sur un tube (--remote-debugging-pipe) : aucun port n'est ouvert,
// chaque commande a un délai, et une page qui ne répond plus devient un problème de sa capture, pas un blocage.
import { spawn, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const AIDE = `Usage : capture <adresse ou fichier> [options]

  --out <dossier>         dossier des captures, par défaut ./captures
  --size <LxH,...>        tailles de fenêtre, par défaut 390x844,1280x900
  --routes </a,/b,...>    une capture par route de l'adresse de base ; compte les routes rendues
  --connexion "<actions>" actions jouées une fois avant les routes, pour se connecter :
                          "goto /connexion; type #email a@b.fr; type #mdp secret; click button[type=submit]"
  --states <a,b,...>      ouvre ?state=<nom> pour chaque état et le capture
  --param <nom>           nom du paramètre d'état, par défaut state
  --steps "<actions>"     actions avant chaque capture, séparées par des points-virgules :
                          click <sél> | hover <sél> | type <sél> <texte> | key <touche> | scroll <dy>
                          | wait <ms> | wait <sél> | goto <route ou adresse>
                          un sélecteur avec des espaces va entre guillemets : click ".nav .item"
                          un click qui change de page attend la nouvelle page
  --sheet                 planche des états, quatre par ligne
  --mark "1=<sél>;..."    capture annotée : un cadre numéroté par groupe d'éléments
  --mask                  capture où chaque ligne de texte devient une barre (lire la composition)
  --full                  page entière ; par défaut, la fenêtre seule
  --zoom <facteur>        densité de pixels, par défaut 1
  --wait <ms>             attente après le chargement, par défaut 400
  --sans-a11y             sans les contrôles d'accessibilité

Chaque capture est contrôlée : erreurs de script, de console et de chargement, statut HTTP, redirection,
chargement inachevé, débordement horizontal, images cassées, et accessibilité (contraste WCAG AA du texte,
images sans alt, champs sans libellé, boutons et liens sans nom, langue de la page, cibles tactiles de moins
de 24 px en mobile). La dernière ligne est le verdict ; le détail est dans report.json.
Code : 0 sans problème, 1 sinon, 2 mauvais appel, 3 pas de navigateur.`;

// ---------- Arguments ----------
const AVEC_VALEUR = { "--out": "captures", "--size": "390x844,1280x900", "--routes": "", "--connexion": "",
  "--states": "", "--param": "state", "--steps": "", "--mark": "", "--zoom": "1", "--wait": "400" };
const DRAPEAUX = ["--sheet", "--mask", "--full", "--sans-a11y"];

function arret(message, code = 1) {
  console.error(`capture : ${message}`);
  process.exit(code);
}

const argv = process.argv.slice(2);
if (argv.length === 0 || argv.includes("--help") || argv.includes("-h")) {
  console.log(AIDE);
  process.exit(argv.length ? 0 : 2);
}
if (Number(process.versions.node.split(".")[0]) < 22) arret("Node 22 ou plus récent requis.", 2);

const opt = { ...AVEC_VALEUR };
const drapeaux = new Set();
let cible = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--force") continue;  // accepté pour l'uniformité des outils : une capture est toujours refaite
  if (DRAPEAUX.includes(a)) drapeaux.add(a);
  else if (Object.hasOwn(AVEC_VALEUR, a)) {
    const v = argv[i + 1];
    if (v === undefined || v.startsWith("--")) arret(`${a} attend une valeur`, 2);
    opt[a] = v;
    i++;
  } else if (a.startsWith("--")) arret(`option inconnue ${a}\noptions : ${[...Object.keys(AVEC_VALEUR), ...DRAPEAUX].join(" ")}`, 2);
  else if (cible) arret(`une seule adresse ou un seul fichier : ${cible}, ${a}`, 2);
  else cible = a;
}
if (!cible) arret("adresse ou fichier manquant.", 2);

const liste = (s) => s.split(",").map((x) => x.trim()).filter(Boolean);
const tailles = liste(opt["--size"]).map((s) => {
  const m = /^(\d{2,5})x(\d{2,5})$/.exec(s);
  if (!m) arret(`taille au format LxH, par exemple 390x844 : ${s}`, 2);
  return { l: Number(m[1]), h: Number(m[2]) };
});
if (!tailles.length) arret("--size : au moins une taille", 2);
const routes = opt["--routes"] ? liste(opt["--routes"]) : null;
const etats = opt["--states"] ? liste(opt["--states"]) : [null];
const zoom = Number(opt["--zoom"]);
if (!(zoom > 0 && zoom <= 4)) arret("--zoom : un nombre de 0 à 4", 2);
const attente = Number(opt["--wait"]);
if (!(attente >= 0)) arret("--wait : un nombre de millisecondes", 2);
const reperes = opt["--mark"] ? opt["--mark"].split(";").map((s) => s.trim()).filter(Boolean).map((s, i) => {
  const m = /^([\w-]{1,4})\s*=\s*(.+)$/.exec(s);
  return m ? { etiquette: m[1], selecteur: m[2].trim() } : { etiquette: String(i + 1), selecteur: s };
}) : [];
const dossier = path.resolve(opt["--out"]);
fs.mkdirSync(dossier, { recursive: true });

// Un nom de fichier lisible quand c'est possible, sinon un nom court et stable tiré du texte.
const empreinte = (s) => createHash("sha256").update(s).digest("hex").slice(0, 10);
const nomSur = (s, prefixe, i) => (/^[A-Za-z0-9_-]{1,80}$/.test(s) ? s : `${prefixe}-${i + 1}-${empreinte(s)}`);
const nomRoute = (r, i) => {
  const s = r.replace(/^\/+|\/+$/g, "").replace(/[^A-Za-z0-9_-]+/g, "-").slice(0, 80);
  return s ? nomSur(s, "route", i) : "accueil";
};
const pause = (ms) => new Promise((ok) => setTimeout(ok, ms));

// ---------- Fichier local : servi par un serveur local, rien hors de son dossier ----------
const TYPES = {
  ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8", ".json": "application/json",
  ".map": "application/json", ".txt": "text/plain; charset=utf-8", ".csv": "text/csv; charset=utf-8",
  ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
  ".webp": "image/webp", ".avif": "image/avif", ".ico": "image/x-icon", ".woff2": "font/woff2", ".woff": "font/woff",
  ".ttf": "font/ttf", ".otf": "font/otf", ".mp4": "video/mp4", ".webm": "video/webm", ".vtt": "text/vtt",
  ".wasm": "application/wasm", ".pdf": "application/pdf",
};
// Fichiers cachés, clés et secrets : jamais servis, même dans le dossier de la page.
const prive = (segment) => segment.startsWith(".") || /^(?:secrets?|credentials?)(?:[._-]|$)/i.test(segment)
  || /^id_[a-z0-9]+(?:\.pub)?$/i.test(segment) || /\.(?:pem|key|p12|pfx|kdbx)$/i.test(segment);
let serveur = null;

async function adresseDeBase(t) {
  if (/^https?:\/\//i.test(t)) return t;
  const chemin = path.resolve(t);
  if (!fs.existsSync(chemin)) arret(`fichier introuvable : ${t}`, 2);
  const estDossier = fs.statSync(chemin).isDirectory();
  const racine = fs.realpathSync(estDossier ? chemin : path.dirname(chemin));
  let hote = "";
  serveur = createServer((req, res) => {
    const absent = () => res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("404 introuvable");
    try {
      if ((req.method !== "GET" && req.method !== "HEAD") || req.headers.host !== hote) return absent();
      const segments = decodeURIComponent(new URL(req.url, "http://local").pathname).split(/[\\/]+/).filter(Boolean);
      if (segments.some((s) => s === ".." || prive(s))) return absent();
      let fichier = path.join(racine, ...segments);
      if (fs.statSync(fichier).isDirectory()) fichier = path.join(fichier, "index.html");
      const reel = fs.realpathSync(fichier);
      const relatif = path.relative(racine, reel);
      if (relatif.startsWith("..") || path.isAbsolute(relatif) || relatif.split(path.sep).some(prive)) return absent();
      const type = TYPES[path.extname(reel).toLowerCase()];
      if (!type || !fs.statSync(reel).isFile()) return absent();
      res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" });
      res.end(req.method === "HEAD" ? undefined : fs.readFileSync(reel));
    } catch {
      absent();
    }
  });
  await new Promise((ok) => serveur.listen(0, "127.0.0.1", ok));
  hote = `127.0.0.1:${serveur.address().port}`;
  return `http://${hote}/${estDossier ? "" : encodeURIComponent(path.basename(chemin))}`;
}

// ---------- Navigateur : invisible, profil jetable, piloté sur un tube ----------
function trouveNavigateur() {
  if (process.env.CHROME_PATH) {
    if (fs.existsSync(process.env.CHROME_PATH)) return process.env.CHROME_PATH;
    arret(`CHROME_PATH ne mène à aucun fichier : ${process.env.CHROME_PATH}`, 3);
  }
  const env = process.env;
  const parSysteme = {
    win32: [env.PROGRAMFILES, env["PROGRAMFILES(X86)"], env.LOCALAPPDATA].filter(Boolean).flatMap((d) => [
      path.join(d, "Google", "Chrome", "Application", "chrome.exe"),
      path.join(d, "Chromium", "Application", "chrome.exe"),
      path.join(d, "Microsoft", "Edge", "Application", "msedge.exe")]),
    darwin: ["Google Chrome.app/Contents/MacOS/Google Chrome", "Chromium.app/Contents/MacOS/Chromium",
      "Microsoft Edge.app/Contents/MacOS/Microsoft Edge"].map((p) => `/Applications/${p}`),
  }[process.platform] || [];
  const trouve = parSysteme.find((p) => fs.existsSync(p));
  if (trouve) return trouve;
  if (process.platform !== "win32") {
    for (const nom of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]) {
      const r = spawnSync("which", [nom], { encoding: "utf8" });
      if (r.status === 0 && r.stdout.trim()) return r.stdout.trim();
    }
  }
  arret("Chrome, Chromium ou Edge introuvable : indique son chemin dans CHROME_PATH, ou demande-le en `## Installation nécessaire`.", 3);
}

class Tube {
  // Messages JSON terminés par un octet nul : fd 3 vers le navigateur, fd 4 depuis le navigateur.
  constructor(processus) {
    this.versNav = processus.stdio[3];
    this.enAttente = new Map();
    this.ecouteurs = new Set();
    this.numero = 0;
    let reste = "";
    processus.stdio[4].setEncoding("utf8");
    processus.stdio[4].on("data", (morceau) => {
      const messages = (reste + morceau).split("\0");
      reste = messages.pop();
      for (const m of messages) if (m) this.recu(JSON.parse(m));
    });
    processus.stdio[4].on("close", () => {
      for (const a of this.enAttente.values()) { clearTimeout(a.minuteur); a.non(new Error("le navigateur s'est fermé")); }
      this.enAttente.clear();
    });
  }

  recu(msg) {
    if (msg.id === undefined) {
      for (const f of [...this.ecouteurs]) f(msg);
      return;
    }
    const a = this.enAttente.get(msg.id);
    if (!a) return;
    this.enAttente.delete(msg.id);
    clearTimeout(a.minuteur);
    if (msg.error) a.non(new Error(`${a.methode} : ${msg.error.message}`));
    else a.oui(msg.result);
  }

  appel(methode, params = {}, sessionId = undefined, delai = 30000) {
    const id = ++this.numero;
    return new Promise((oui, non) => {
      const minuteur = setTimeout(() => {
        this.enAttente.delete(id);
        non(new Error(`le navigateur ne répond pas à ${methode} en ${delai / 1000} s`));
      }, delai);
      this.enAttente.set(id, { oui, non, minuteur, methode });
      this.versNav.write(JSON.stringify(sessionId ? { id, method: methode, params, sessionId } : { id, method: methode, params }) + "\0");
    });
  }

  ecoute(f) {
    this.ecouteurs.add(f);
    return () => this.ecouteurs.delete(f);
  }

  // Le premier message qui passe le test, ou null après le délai.
  attend(test, delai) {
    return new Promise((oui) => {
      const fin = (v) => { arreter(); clearTimeout(minuteur); oui(v); };
      const arreter = this.ecoute((m) => { if (test(m)) fin(m); });
      const minuteur = setTimeout(() => fin(null), delai);
    });
  }
}

const profil = fs.mkdtempSync(path.join(os.tmpdir(), "hosa-capture-"));
const navigateur = spawn(trouveNavigateur(), [
  "--headless=new", "--remote-debugging-pipe", `--user-data-dir=${profil}`, "--no-first-run", "--no-default-browser-check",
  "--disable-extensions", "--disable-background-networking", "--disable-sync", "--disable-component-update",
  "--hide-scrollbars", "--mute-audio", "--force-color-profile=srgb", "--enable-unsafe-swiftshader", "about:blank",
], { stdio: ["ignore", "ignore", "pipe", "pipe", "pipe"], windowsHide: true });
let journalNav = "";
navigateur.stderr.setEncoding("utf8");
navigateur.stderr.on("data", (d) => { journalNav = (journalNav + d).slice(-2000); });
navigateur.on("error", (e) => arret(`le navigateur ne démarre pas : ${e.message}`, 3));
const tube = new Tube(navigateur);

let nettoyage = null;
function nettoie() {
  return nettoyage ||= (async () => {
    if (navigateur.exitCode === null && navigateur.signalCode === null) {
      const ferme = new Promise((ok) => navigateur.once("close", ok));
      tube.appel("Browser.close", {}, undefined, 3000).catch(() => {});
      if (!(await Promise.race([ferme.then(() => true), pause(3000).then(() => false)]))) navigateur.kill("SIGKILL");
    }
    serveur?.close();
    try { fs.rmSync(profil, { recursive: true, force: true }); } catch {}
  })();
}
process.on("exit", () => {
  try { navigateur.kill(); } catch {}
  try { fs.rmSync(profil, { recursive: true, force: true }); } catch {}
});
for (const [signal, code] of [["SIGINT", 130], ["SIGTERM", 143]]) process.on(signal, async () => { await nettoie(); process.exit(code); });

try {
  await tube.appel("Browser.getVersion", {}, undefined, 15000);
} catch {
  arret(`le navigateur n'a pas démarré en 15 secondes.${journalNav ? "\n" + journalNav.trim().split("\n").slice(-3).join("\n") : ""}`, 3);
}
const { targetId } = await tube.appel("Target.createTarget", { url: "about:blank" });
const { sessionId } = await tube.appel("Target.attachToTarget", { targetId, flatten: true });
const page = (methode, params, delai) => tube.appel(methode, params, sessionId, delai);
const dePage = (m) => m.sessionId === sessionId;
for (const domaine of ["Page", "Runtime", "Log", "Network"]) await page(`${domaine}.enable`);

// Ce que la page signale d'elle-même pendant une capture.
let releve = [];
let statut = null;
tube.ecoute((m) => {
  if (!dePage(m)) return;
  const p = m.params;
  if (m.method === "Runtime.exceptionThrown") {
    const d = p.exceptionDetails;
    releve.push(`erreur de script : ${(d.exception?.description || d.text || "").split("\n")[0]}`);
  } else if (m.method === "Runtime.consoleAPICalled" && p.type === "error") {
    releve.push(`erreur de console : ${p.args.map((a) => a.value ?? a.description ?? "").join(" ").slice(0, 200)}`);
  } else if (m.method === "Log.entryAdded" && p.entry.level === "error" && !/favicon\.ico/.test(p.entry.url || "")) {
    releve.push(`erreur de chargement : ${p.entry.text.slice(0, 200)}${p.entry.url ? " " + p.entry.url : ""}`);
  } else if (m.method === "Network.responseReceived" && p.type === "Document" && p.frameId === targetId) {
    statut = p.response.status;
  }
});

class ErreurDePage extends Error {}
// Une fonction de ce fichier, exécutée dans la page avec ses arguments. Une page qui change de processus
// (page d'erreur du navigateur) perd son contexte un instant : on réessaie.
async function dansLaPage(fonction, ...args) {
  const expression = `(${fonction})(${args.map((a) => JSON.stringify(a)).join(",")})`;
  for (let essai = 1; ; essai++) {
    try {
      const r = await page("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
      if (r.exceptionDetails) {
        const d = r.exceptionDetails;
        throw new ErreurDePage((d.exception?.description || d.text || "erreur").split("\n")[0].replace(/^Error: /, ""));
      }
      return r.result.value;
    } catch (e) {
      if (e instanceof ErreurDePage || essai >= 4 || !/context|target|attached|destroyed/i.test(e.message)) throw e;
      await pause(300);
    }
  }
}

const chargee = (delai) => tube.attend((m) => dePage(m) && m.method === "Page.loadEventFired", delai);

async function ouvre(adresse) {
  statut = null;
  const fin = chargee(15000);
  const r = await page("Page.navigate", { url: adresse });
  if (r.errorText) throw new Error(`impossible d'ouvrir ${adresse} : ${r.errorText}`);
  if (!(await fin)) releve.push("chargement inachevé après 15 s");
  await dansLaPage(() => (document.fonts ? document.fonts.ready.then(() => true) : true));
  await pause(attente);
}

async function fenetre(l, h, densite) {
  const mobile = l < 600;
  await page("Emulation.setDeviceMetricsOverride", { width: l, height: h, deviceScaleFactor: densite, mobile });
  await page("Emulation.setTouchEmulationEnabled", { enabled: mobile });
}

async function photo(fichier, entiere) {
  const params = { format: "png", captureBeyondViewport: entiere };
  if (entiere) {
    const m = await page("Page.getLayoutMetrics");
    const t = m.cssContentSize || m.contentSize;
    params.clip = { x: 0, y: 0, width: Math.ceil(t.width), height: Math.ceil(t.height), scale: 1 };
  }
  const { data } = await page("Page.captureScreenshot", params, 60000);
  fs.writeFileSync(fichier, Buffer.from(data, "base64"));
  return fichier;
}

// ---------- Contrôles dans la page : rendu, mise en page, accessibilité ----------
// Chaque problème nomme l'élément par un sélecteur court, et son texte quand il en a un.
function controlesDeLaPage(accessibilite, mobile) {
  const trouves = [];
  const racine = document.documentElement;
  const nom = (el) => {
    const classes = typeof el.className === "string" ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 2) : [];
    return el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (classes.length ? "." + classes.join(".") : "");
  };
  const cite = (el) => {
    const t = (el.innerText || el.value || "").replace(/\s+/g, " ").trim();
    return t ? ` « ${t.slice(0, 40)} »` : "";
  };
  const visible = (el) => {
    const b = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return b.width > 0 && b.height > 0 && b.right > 0 && b.bottom > 0 && s.display !== "none"
      && s.visibility !== "hidden" && Number(s.opacity) > 0.05;
  };
  if (racine.scrollWidth > innerWidth + 1) trouves.push(`débordement horizontal : page de ${racine.scrollWidth} px pour une fenêtre de ${innerWidth} px`);
  for (const img of document.images) if (img.complete && img.naturalWidth === 0) trouves.push(`image cassée : ${(img.getAttribute("src") || "").slice(0, 120)}`);
  if (!document.body || !document.body.innerText.trim()) trouves.push("page vide : aucun texte rendu");
  if (!accessibilite) return trouves;

  if (!racine.lang) trouves.push("langue de la page absente (<html lang>)");
  // Le navigateur ramène toute couleur CSS à des octets RGBA sur une toile d'un pixel.
  const toile = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
  const couleur = (css) => {
    toile.clearRect(0, 0, 1, 1);
    toile.fillStyle = "#000";
    toile.fillStyle = css;
    toile.fillRect(0, 0, 1, 1);
    const d = toile.getImageData(0, 0, 1, 1).data;
    return { r: d[0], g: d[1], b: d[2], a: d[3] / 255 };
  };
  const sur = (haut, bas) => ({ r: haut.r * haut.a + bas.r * (1 - haut.a), g: haut.g * haut.a + bas.g * (1 - haut.a),
    b: haut.b * haut.a + bas.b * (1 - haut.a), a: 1 });
  const fondDe = (el) => {
    const couches = [];
    for (let n = el; n; n = n.parentElement) {
      const s = getComputedStyle(n);
      if (s.backgroundImage !== "none") return null;  // image ou dégradé : contraste non calculable ici
      const c = couleur(s.backgroundColor);
      if (c.a > 0) couches.push(c);
      if (c.a >= 1) break;
    }
    return couches.reverse().reduce((bas, haut) => sur(haut, bas), { r: 255, g: 255, b: 255, a: 1 });
  };
  const lum = (c) => {
    const [r, g, b] = [c.r, c.g, c.b].map((v) => (v / 255 <= 0.04045 ? v / 255 / 12.92 : ((v / 255 + 0.055) / 1.055) ** 2.4));
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const rapport = (a, b) => (Math.max(lum(a), lum(b)) + 0.05) / (Math.min(lum(a), lum(b)) + 0.05);
  const hexa = (c) => "#" + [c.r, c.g, c.b].map((v) => Math.round(v).toString(16).padStart(2, "0")).join("");
  const vus = new Set();
  let echecs = 0;
  const textes = document.createTreeWalker(document.body || racine, NodeFilter.SHOW_TEXT);
  while (textes.nextNode() && echecs < 12) {
    const el = textes.currentNode.parentElement;
    if (!el || vus.has(el) || !textes.currentNode.textContent.trim()) continue;
    vus.add(el);
    if (!visible(el) || el.closest("[disabled],[aria-disabled=true],[aria-hidden=true]")) continue;
    const fond = fondDe(el);
    if (!fond) continue;
    const s = getComputedStyle(el);
    const texte = sur(couleur(s.color), fond);
    const taille = parseFloat(s.fontSize);
    const grand = taille >= 24 || (taille >= 18.66 && Number(s.fontWeight) >= 700);
    const minimum = grand ? 3 : 4.5;
    const r = rapport(texte, fond);
    if (r < minimum) {
      echecs++;
      trouves.push(`contraste ${r.toFixed(2)}:1 < ${minimum}:1 : ${nom(el)}${cite(el)} (${hexa(texte)} sur ${hexa(fond)})`);
    }
  }
  for (const img of document.images) if (visible(img) && !img.hasAttribute("alt")) trouves.push(`image sans alt : ${nom(img)} ${(img.getAttribute("src") || "").slice(0, 60)}`);
  const nomme = (el) => el.getAttribute("aria-label") || el.getAttribute("aria-labelledby") || el.getAttribute("title");
  for (const el of document.querySelectorAll("input:not([type=hidden]):not([type=submit]):not([type=button]):not([type=reset]),select,textarea")) {
    if (visible(el) && !nomme(el) && !(el.labels && el.labels.length)) trouves.push(`champ sans libellé : ${nom(el)}${el.name ? ` [name=${el.name}]` : ""}`);
  }
  for (const el of document.querySelectorAll("button,a[href],[role=button]")) {
    if (!visible(el)) continue;
    if (!(el.innerText || "").trim() && !nomme(el) && !el.querySelector("img[alt]:not([alt=''])")) {
      trouves.push(`${el.tagName === "A" ? "lien" : "bouton"} sans nom accessible : ${nom(el)}`);
    }
    if (mobile && !el.closest("p,li,td")) {
      const b = el.getBoundingClientRect();
      if (b.width < 24 || b.height < 24) trouves.push(`cible tactile ${Math.round(b.width)}×${Math.round(b.height)} px < 24 px : ${nom(el)}${cite(el)}`);
    }
  }
  return trouves;
}

// ---------- Repères, masque : un calque SVG posé sur la page, retiré après la capture ----------
function poseReperes(groupes) {
  const ns = "http://www.w3.org/2000/svg";
  const doc = document.documentElement;
  const calque = document.createElementNS(ns, "svg");
  calque.id = "hosa-reperes";
  calque.setAttribute("width", Math.max(doc.scrollWidth, innerWidth));
  calque.setAttribute("height", Math.max(doc.scrollHeight, innerHeight));
  calque.style.cssText = "position:absolute;left:0;top:0;z-index:2147483647;pointer-events:none;overflow:visible";
  const forme = (balise, attributs) => {
    const n = document.createElementNS(ns, balise);
    for (const [k, v] of Object.entries(attributs)) n.setAttribute(k, v);
    calque.append(n);
    return n;
  };
  const absents = [];
  for (const { etiquette, selecteur } of groupes) {
    let elements;
    try { elements = [...document.querySelectorAll(selecteur)]; } catch { absents.push(`${selecteur} (sélecteur invalide)`); continue; }
    const boites = elements.map((e) => e.getBoundingClientRect()).filter((b) => b.width > 0 && b.height > 0);
    if (!boites.length) { absents.push(selecteur + (elements.length ? " (invisible)" : "")); continue; }
    boites.forEach((b, i) => {
      const x = b.left + scrollX - 3, y = b.top + scrollY - 3;
      forme("rect", { x, y, width: b.width + 6, height: b.height + 6, rx: 4, fill: "none", stroke: "#d81b60", "stroke-width": 2.5 });
      if (i > 0) return;
      const cx = x >= 14 ? x : x + 14, cy = y >= 14 ? y : y + 14;  // contre le bord : dans le coin du cadre
      forme("circle", { cx, cy, r: 12, fill: "#d81b60", stroke: "#fff", "stroke-width": 2 });
      forme("text", { x: cx, y: cy + 4.5, "text-anchor": "middle", fill: "#fff", "font-size": 13, "font-weight": 700,
        "font-family": "system-ui,sans-serif" }).textContent = etiquette;
    });
  }
  (document.body || doc).append(calque);
  return absents;
}

function poseMasque() {
  // Chaque ligne de texte devient une barre de sa couleur : on lit la composition, pas les mots.
  const ns = "http://www.w3.org/2000/svg";
  const doc = document.documentElement;
  const calque = document.createElementNS(ns, "svg");
  calque.id = "hosa-masque";
  calque.setAttribute("width", Math.max(doc.scrollWidth, innerWidth));
  calque.setAttribute("height", Math.max(doc.scrollHeight, innerHeight));
  calque.style.cssText = "position:absolute;left:0;top:0;z-index:2147483646;pointer-events:none";
  const textes = document.createTreeWalker(document.body || doc, NodeFilter.SHOW_TEXT);
  const plage = document.createRange();
  let barres = 0;
  while (textes.nextNode() && barres < 5000) {
    const n = textes.currentNode;
    if (!n.textContent.trim() || !n.parentElement || n.parentElement.closest("script,style,noscript")) continue;
    const s = getComputedStyle(n.parentElement);
    if (s.visibility === "hidden" || Number(s.opacity) < 0.05) continue;
    plage.selectNodeContents(n);
    for (const b of plage.getClientRects()) {
      if (b.width < 1 || b.height < 1) continue;
      const r = document.createElementNS(ns, "rect");
      const h = Math.max(2, b.height * 0.55);
      for (const [k, v] of Object.entries({ x: b.left + scrollX, y: b.top + scrollY + (b.height - h) / 2, width: b.width,
        height: h, rx: Math.min(3, h / 2), fill: s.color, "fill-opacity": 0.4 })) r.setAttribute(k, v);
      calque.append(r);
      barres++;
    }
  }
  const style = document.createElement("style");
  style.id = "hosa-masque-css";
  style.textContent = "*,*::before,*::after{color:transparent!important;-webkit-text-fill-color:transparent!important;"
    + "text-shadow:none!important;caret-color:transparent!important}::placeholder{color:transparent!important}"
    + "svg:not(#hosa-masque) text{fill:transparent!important;stroke:transparent!important}";
  document.head.append(style);
  (document.body || doc).append(calque);
  return barres;
}

function retireCalques() {
  for (const id of ["hosa-reperes", "hosa-masque", "hosa-masque-css"]) document.getElementById(id)?.remove();
  return true;
}

// ---------- Planche : les captures d'une taille, quatre par ligne ----------
async function planche(images, fichier, l, h) {
  const colonne = Math.min(l, 400), parLigne = Math.min(images.length, 4), lignes = Math.ceil(images.length / parLigne);
  const hauteur = Math.round((colonne * h) / l);
  const echappe = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const figures = images.map(({ fichier: f, legende }) =>
    `<figure><img alt="" src="data:image/png;base64,${fs.readFileSync(f).toString("base64")}"><figcaption>${echappe(legende)}</figcaption></figure>`).join("");
  const html = `<!doctype html><html lang="fr"><meta charset="utf-8"><style>body{margin:0;padding:28px;background:#e8e8e4;`
    + `font:600 13px/1.3 system-ui,sans-serif;color:#2b2b28}.g{display:grid;grid-template-columns:repeat(${parLigne},${colonne}px);`
    + `gap:28px 20px}figure{margin:0}img{display:block;width:100%;border-radius:8px;box-shadow:0 0 0 1px #0002,0 2px 8px #0001}`
    + `figcaption{margin-top:6px}</style><div class="g">${figures}</div>`;
  await fenetre(parLigne * colonne + (parLigne - 1) * 20 + 56, lignes * (hauteur + 26) + (lignes - 1) * 28 + 56, 1);
  await ouvre("about:blank");
  const { frameTree } = await page("Page.getFrameTree");
  await page("Page.setDocumentContent", { frameId: frameTree.frame.id, html });
  await dansLaPage(() => Promise.all([...document.images].map((i) => i.decode().catch(() => null))).then(() => true));
  return photo(fichier, true);
}

// ---------- Actions : se connecter, ouvrir un menu, remplir un champ… ----------
function mots(texte) {
  return [...texte.matchAll(/"([^"]*)"|'([^']*)'|(\S+)/g)].map((m) => m[1] ?? m[2] ?? m[3]);
}
// nom de touche → [code DevTools, code Windows, texte produit]
const TOUCHES = { Enter: ["Enter", 13, "\r"], Escape: ["Escape", 27], Tab: ["Tab", 9], Space: ["Space", 32, " "],
  Backspace: ["Backspace", 8], Delete: ["Delete", 46], Home: ["Home", 36], End: ["End", 35], PageUp: ["PageUp", 33],
  PageDown: ["PageDown", 34], ArrowUp: ["ArrowUp", 38], ArrowDown: ["ArrowDown", 40], ArrowLeft: ["ArrowLeft", 37],
  ArrowRight: ["ArrowRight", 39] };

async function centre(selecteur) {
  const p = await dansLaPage((s) => {
    const el = document.querySelector(s);
    if (!el) return null;
    el.scrollIntoView({ block: "center", inline: "center" });
    const b = el.getBoundingClientRect();
    return { x: b.left + b.width / 2, y: b.top + b.height / 2 };
  }, selecteur);
  if (!p) throw new Error(`élément introuvable : ${selecteur}`);
  return p;
}
const souris = (type, p) => page("Input.dispatchMouseEvent", { type, x: p.x, y: p.y, button: "left", clickCount: 1, pointerType: "mouse" });

async function clique(selecteur) {
  const p = await centre(selecteur);
  const depart = tube.attend((m) => dePage(m) && m.method === "Page.frameStartedLoading" && m.params.frameId === targetId, 300);
  await souris("mouseMoved", p);
  await souris("mousePressed", p);
  await souris("mouseReleased", p);
  if (await depart) {
    await chargee(15000);
    await pause(attente);
  } else await pause(120);
}

async function touche(nomTouche) {
  const [code, windows, texte] = TOUCHES[nomTouche] || [nomTouche.length === 1 ? `Key${nomTouche.toUpperCase()}` : nomTouche,
    nomTouche.length === 1 ? nomTouche.toUpperCase().charCodeAt(0) : 0, nomTouche.length === 1 ? nomTouche : undefined];
  const cle = nomTouche === "Space" ? " " : nomTouche;
  await page("Input.dispatchKeyEvent", { type: texte ? "keyDown" : "rawKeyDown", key: cle, code, windowsVirtualKeyCode: windows, ...(texte && { text: texte }) });
  await page("Input.dispatchKeyEvent", { type: "keyUp", key: cle, code, windowsVirtualKeyCode: windows });
  await pause(80);
}

async function joue(actions, base) {
  for (const brut of actions.split(";").map((s) => s.trim()).filter(Boolean)) {
    const [verbe, ...args] = mots(brut);
    const unSeul = () => { if (args.length !== 1) throw new Error(`action mal formée : ${brut} ; un sélecteur avec des espaces va entre guillemets : ${verbe} ".nav .item"`); };
    if (verbe === "wait") {
      unSeul();
      if (/^\d+$/.test(args[0])) await pause(Number(args[0]));
      else {
        const vu = await dansLaPage((s, ms) => new Promise((ok) => {
          const t0 = Date.now();
          const tour = () => (document.querySelector(s) ? ok(true) : Date.now() - t0 > ms ? ok(false) : setTimeout(tour, 50));
          tour();
        }), args[0], 10000);
        if (!vu) throw new Error(`élément absent après 10 s : ${args[0]}`);
      }
    } else if (verbe === "goto") await ouvre(new URL(args[0] || "/", base).href);
    else if (verbe === "click") { unSeul(); await clique(args[0]); }
    else if (verbe === "hover") { unSeul(); await souris("mouseMoved", await centre(args[0])); await pause(200); }
    else if (verbe === "type") {
      if (args.length < 2) throw new Error(`action mal formée : ${brut} ; type <sélecteur> <texte>`);
      const ok = await dansLaPage((s) => { const el = document.querySelector(s); if (!el) return false; el.focus(); return true; }, args[0]);
      if (!ok) throw new Error(`élément introuvable : ${args[0]}`);
      await page("Input.insertText", { text: args.slice(1).join(" ") });
      await pause(100);
    } else if (verbe === "key") { unSeul(); await touche(args[0]); }
    else if (verbe === "scroll") { await dansLaPage((dy) => { scrollBy(0, dy); return true; }, Number(args[0]) || 0); await pause(200); }
    else throw new Error(`action inconnue : ${brut}`);
  }
}

// ---------- Programme ----------
const base = await adresseDeBase(cible);
const adresse = (route, etat) => {
  const u = route === null ? new URL(base) : new URL(route, base);
  if (etat) u.searchParams.set(opt["--param"], etat);
  return u.href;
};
const BLOQUANT = /^(HTTP |redirigé|page vide|erreur de script|impossible d'ouvrir|capture impossible)/;
const rapport = [];
const lignes = [];
const rendues = new Map();  // route → première raison de non-rendu, "" si rendue
const entiere = drapeaux.has("--full");
try {
  if (opt["--connexion"]) {
    const t = tailles.at(-1);
    await fenetre(t.l, t.h, 1);
    await ouvre(base);
    await joue(opt["--connexion"], base);
  }
  for (const [ri, route] of (routes || [null]).entries()) {
    for (const { l, h } of tailles) {
      const vues = [], masquees = [];
      for (const [ei, etat] of etats.entries()) {
        releve = [];
        await fenetre(l, h, zoom);
        const voulue = adresse(route, etat);
        const problemes = [];
        try {
          await ouvre(voulue);
          if (opt["--steps"]) await joue(opt["--steps"], base);
        } catch (e) { problemes.push(e.message); }
        const nom = [route === null ? "" : nomRoute(route, ri), etat ? nomSur(etat, "etat", ei) : "", `${l}x${h}`,
          zoom === 1 ? "" : `@${zoom}x`].filter(Boolean).join("-");
        let fichier = null;
        try {  // une capture qui échoue est un problème de cette capture, jamais l'arrêt des suivantes
          if (statut >= 400) problemes.push(`HTTP ${statut}`);
          fichier = await photo(path.join(dossier, `${nom}.png`), entiere);
          const ici = await dansLaPage(() => location.pathname).catch(() => null);
          const sansBarre = (p) => p.replace(/\/+$/, "");
          if (route !== null && ici !== null && sansBarre(ici) !== sansBarre(new URL(voulue).pathname)) problemes.push(`redirigé vers ${ici}`);
          problemes.push(...await dansLaPage(controlesDeLaPage, !drapeaux.has("--sans-a11y"), l < 600));
          if (reperes.length) {
            const absents = await dansLaPage(poseReperes, reperes);
            if (absents.length) problemes.push(`--mark : introuvable : ${absents.join(" ; ")}`);
            else lignes.push(path.basename(await photo(path.join(dossier, `${nom}-marque.png`), entiere)));
            await dansLaPage(retireCalques);
          }
          if (drapeaux.has("--mask")) {
            await dansLaPage(poseMasque);
            masquees.push({ fichier: await photo(path.join(dossier, `${nom}-masque.png`), entiere), legende: etat || route || "page" });
            await dansLaPage(retireCalques);
          }
        } catch (e) { problemes.push(`capture impossible : ${e.message}`); }
        const tous = [...new Set([...releve, ...problemes])];
        if (route !== null) {
          const raison = tous.find((x) => BLOQUANT.test(x)) || "";
          if (!rendues.has(route) || (raison && !rendues.get(route))) rendues.set(route, raison);
        }
        rapport.push({ file: fichier && path.basename(fichier), route, state: etat, size: `${l}x${h}`, zoom, status: statut, issues: tous });
        if (fichier) vues.push({ fichier, legende: etat || route || "page" });
        lignes.push(`${fichier ? path.basename(fichier) : nom}${tous.length ? "  ⚠ " + tous.join(" ; ") : ""}`);
      }
      if (drapeaux.has("--sheet") && vues.length > 1) {
        const prefixe = route === null ? "" : nomRoute(route, ri) + "-";
        lignes.push(path.basename(await planche(vues, path.join(dossier, `${prefixe}planche-${l}x${h}.png`), l, h)));
        if (masquees.length > 1) lignes.push(path.basename(await planche(masquees, path.join(dossier, `${prefixe}planche-${l}x${h}-masque.png`), l, h)));
      }
    }
  }
} catch (e) {
  console.error(`capture : ${e.message}`);
  process.exitCode = 1;
}

const echecs = [...rendues].filter(([, raison]) => raison);
const nbRendues = rendues.size - echecs.length;
fs.writeFileSync(path.join(dossier, "report.json"), JSON.stringify({
  routes: routes ? { rendues: nbRendues, total: routes.length, echecs: Object.fromEntries(echecs) } : null,
  captures: rapport,
}, null, 2));
console.log(`Dossier : ${dossier}`);
for (const ligne of lignes) if (lignes.length <= 12 || ligne.includes("⚠")) console.log(`- ${ligne}`);
const total = rapport.reduce((n, r) => n + r.issues.length, 0);
const routesManquees = routes ? routes.length - nbRendues : 0;
if (routes) console.log(`Routes rendues : ${nbRendues} / ${routes.length}${echecs.length ? " — " + echecs.map(([r, v]) => `${r} (${v})`).join(" ; ") : ""}`);
if (total || routesManquees) {
  console.log(`Verdict : ${total} problème(s) sur ${rapport.length} capture(s), détail dans report.json`);
  process.exitCode ||= 1;
} else console.log(`Verdict : OK — ${rapport.length} capture(s), aucun problème`);
await nettoie();
process.exit(process.exitCode || 0);
