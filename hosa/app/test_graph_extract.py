import unittest

import graph_extract as gx

PY = b'"""Module A."""\nfrom .b import helper\nimport pkg.util\n\nclass Base:\n    pass\n\nclass Foo(Base):\n    """A foo."""\n' \
     b'    def run(self):\n        helper()\n        self.stop()\n    def stop(self):\n        pass\n\n# top fn\ndef main():\n    Foo().run()\n'


def defs(facts):
    return {d["qual"]: (d["kind"], d["line"], d["parent"], d["bases"]) for d in facts["defs"]}


def calls(facts):
    return {(c["name"], c["scope"]) for c in facts["calls"]}


class ExtractTest(unittest.TestCase):
    def test_python_defs_nesting_docs_bases_calls_imports(self):
        f = gx.extract("a.py", PY)
        self.assertEqual(f["lang"], "python")
        self.assertEqual(f["doc"], "Module A.")
        self.assertEqual(defs(f), {"Base": ("class", 5, None, []), "Foo": ("class", 8, None, ["Base"]),
                                   "Foo.run": ("method", 10, "Foo", []), "Foo.stop": ("method", 13, "Foo", []),
                                   "main": ("function", 17, None, [])})
        docs = {d["qual"]: d["doc"] for d in f["defs"]}
        self.assertEqual((docs["Foo"], docs["main"]), ("A foo.", "top fn"))
        self.assertEqual(calls(f), {("helper", "Foo.run"), ("stop", "Foo.run"), ("Foo", "main"), ("run", "main")})
        self.assertEqual(f["imports"], [".b", "pkg.util"])

    def test_javascript_esm_and_commonjs(self):
        f = gx.extract("u.js", b"// util module\nimport { a } from './lib/x.js';\nconst y = require('../y');\n/** Does f. */\n"
                                b"export function f() { a(); }\nclass K extends Base { m() { this.n(); } }\n")
        self.assertEqual(f["doc"], "util module")
        self.assertEqual(defs(f), {"f": ("function", 5, None, []), "K": ("class", 6, None, ["Base"]), "K.m": ("method", 6, "K", [])})
        self.assertEqual(f["defs"][0]["doc"], "Does f.")
        self.assertEqual(calls(f), {("a", "f"), ("n", "K.m")})
        self.assertEqual(f["imports"], ["../y", "./lib/x.js"])

    def test_typescript_reuses_the_javascript_query(self):
        f = gx.extract("t.ts", b"import { X } from './x';\nexport class C implements I { go(): void { X.run(); } }\nfunction g() { new C().go(); }\n")
        self.assertEqual(defs(f), {"C": ("class", 2, None, ["I"]), "C.go": ("method", 2, "C", []), "g": ("function", 3, None, [])})
        self.assertIn(("C", "g"), calls(f))
        self.assertEqual(f["imports"], ["./x"])

    def test_other_languages(self):
        cases = {
            "p.php": (b"<?php\nnamespace App;\nuse App\\Models\\User;\nclass Ctl extends Base { public function show() { return User::find(1); } }\n",
                      {"Ctl": ("class", 4, None, ["Base"]), "Ctl.show": ("method", 4, "Ctl", [])}, ["App.Models.User"]),
            "J.java": (b"package a;\nimport com.x.Util;\npublic class J extends B implements I { void m() { Util.go(); n(); } void n() {} }\n",
                       {"J": ("class", 3, None, ["B", "I"]), "J.m": ("method", 3, "J", []), "J.n": ("method", 3, "J", [])}, ["com.x.Util"]),
            "c.cs": (b"using App.Services;\nnamespace App { public class Ctl : Base { public void Run() { Svc.Go(); } } }\n",
                     {"Ctl": ("class", 2, None, ["Base"]), "Ctl.Run": ("method", 2, "Ctl", [])}, ["App.Services"]),
            "r.rb": (b"require 'json'\nrequire_relative 'lib/x'\nclass Foo < Bar\n  def run\n    JSON.parse('')\n  end\nend\n",
                     {"Foo": ("class", 3, None, ["Bar"]), "Foo.run": ("method", 4, "Foo", [])}, ["./lib/x", "json"]),
        }
        for path, (src, want, imports) in cases.items():
            with self.subTest(path):
                f = gx.extract(path, src)
                self.assertEqual(defs(f), want)
                self.assertEqual(f["imports"], imports)

    def test_go(self):
        f = gx.extract("m.go", b'package main\nimport (\n  "fmt"\n  "example.com/app/util"\n)\n// Main entry\n'
                               b'func main() { fmt.Println(util.Do()) }\n')
        self.assertEqual(defs(f), {"main": ("function", 7, None, [])})
        self.assertEqual(f["defs"][0]["doc"], "Main entry")
        self.assertEqual(f["imports"], ["example.com/app/util", "fmt"])

    def test_unknown_extension_has_no_language(self):
        self.assertIsNone(gx.lang_of("README.md"))
        self.assertEqual(gx.lang_of("src/App.TSX"), "tsx")


if __name__ == "__main__":
    unittest.main()
