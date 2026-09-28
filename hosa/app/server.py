"""App de pilotage Hosa — serveur HTTP local (stdlib) au-dessus de la KB OKF."""
import json
import mimetypes
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import graph
import kb

PUBLIC = Path(__file__).parent / "public"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


def make_handler(root):
    checkout = graph.checkout_root(root)  # le graphe vit à la racine git du projet dont on sert la KB

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, payload=None, ctype="application/json; charset=utf-8", raw=None):
            data = raw if raw is not None else json.dumps(payload, ensure_ascii=False, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _error(self, status, message):
            self._send(status, {"error": message})

        def _guard(self):
            # DNS rebinding : n'accepte que les requêtes adressées à localhost.
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
            if host not in LOCAL_HOSTS:
                self._error(403, "hôte non autorisé")
                return False
            return True

        def _json_body(self):
            # Exiger application/json force un preflight CORS (jamais accordé) : bloque le CSRF depuis un autre site.
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                raise kb.KbError("Content-Type application/json requis")
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as e:
                raise kb.KbError(f"JSON invalide : {e}") from e
            if not isinstance(body, dict):
                raise kb.KbError("le corps doit être un objet JSON")
            return body

        def _dispatch(self, method):
            if not self._guard():
                return
            url = urlsplit(self.path)
            path = unquote(url.path)
            try:
                if path.startswith("/api/"):
                    return self._api(method, path[5:], parse_qs(url.query))
                if method != "GET":
                    return self._error(405, "méthode non autorisée")
                return self._static(path)
            except FileExistsError as e:
                self._error(409, f"existe déjà : {e}")
            except graph.GraphError as e:
                self._error(404, str(e))
            except kb.KbError as e:
                self._error(400, str(e))

        def _api(self, method, route, query):
            if method == "GET" and route == "overview":
                return self._send(200, kb.overview(root))
            if method == "GET" and route == "activity":
                return self._send(200, kb.activity(root, 300))
            if method == "GET" and route == "concepts":
                concepts = kb.walk(root)
                if "type" in query:
                    concepts = [c for c in concepts if c["frontmatter"].get("type") == query["type"][0]]
                return self._send(200, concepts)
            if method == "POST" and route == "concepts":
                b = self._json_body()
                return self._send(201, kb.create(root, str(b.get("bundle", "")), str(b.get("slug", "")),
                                                 str(b.get("type", "")), str(b.get("title", ""))))
            if method == "POST" and route == "render":
                return self._send(200, {"html": kb.render(str(self._json_body().get("body", "")))})
            if method == "GET" and route in ("graph/find", "graph/node", "graph/trace"):
                return self._send(200, self._graph(route[len("graph/"):], query))
            if route.startswith("concepts/"):
                rel = route[len("concepts/"):]
                if method == "GET":
                    concept = kb.get(root, rel)
                elif method == "PATCH":
                    fm = self._json_body().get("frontmatter")
                    if not isinstance(fm, dict):
                        raise kb.KbError("le corps doit être { frontmatter: {...} }")
                    concept = kb.update(root, rel, fm, merge=True)
                elif method == "PUT":
                    b = self._json_body()
                    fm = b.get("frontmatter")
                    if isinstance(fm, str):
                        fm, _ = kb.parse(f"---\n{fm}\n---\n")
                    if not isinstance(fm, dict) or not isinstance(b.get("body"), str):
                        raise kb.KbError("le corps doit être { frontmatter, body }")
                    concept = kb.update(root, rel, fm, b["body"], merge=False)
                else:
                    return self._error(405, "méthode non autorisée")
                return self._send(200, concept) if concept else self._error(404, "introuvable")
            return self._error(404, "route inconnue")

        def _graph(self, what, query):
            if not (graph.graph_dir(checkout) / "graph.json").exists():
                raise graph.GraphError(f"graphe absent : lancer `graph.py index` dans {checkout}")
            g = graph.Index(graph.refresh(checkout))  # fraîcheur : comme pour la CLI
            if what == "trace":
                return g.trace()
            if what == "find":
                return [g.nodes[i] for i in g.find((query.get("q") or [""])[0])]
            nid = (query.get("id") or [""])[0]
            if nid not in g.nodes:
                raise graph.GraphError(f"élément introuvable : {nid}")
            return {**g.detail(nid), "affected": g.affected(nid)}

        def _static(self, path):
            target = (PUBLIC / path.lstrip("/")).resolve()
            if path == "/" or not target.is_file() or PUBLIC.resolve() not in target.parents:
                target = PUBLIC / "index.html"  # SPA : le routage est côté client (hash)
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype.endswith("javascript"):
                ctype += "; charset=utf-8"
            self._send(200, ctype=ctype, raw=target.read_bytes())

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            self._dispatch("POST")

        def do_PATCH(self):
            self._dispatch("PATCH")

        def do_PUT(self):
            self._dispatch("PUT")

    return Handler


def serve(root, port=0):
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(Path(root).resolve()))


if __name__ == "__main__":
    root = os.environ.get("HOSA_KB_ROOT") or kb.resolve_kb_root()
    server = serve(root, int(os.environ.get("PORT", 3000)))
    print(f"Hosa — http://localhost:{server.server_port}  (KB : {root})", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
