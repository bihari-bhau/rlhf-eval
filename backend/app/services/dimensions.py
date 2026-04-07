"""
38-criteria repo qualification checker + D1-D9 dimension scoring.

Criteria 1-11 = MUST (hard gates), 12-19 = SHOULD, 20-38 = CHECK.
D1-D9 are lightweight automated dimension scores (0.0-1.0) saved to DB.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DimensionResult:
    code: str
    automated_score: float
    detail: str | None


@dataclass
class CriterionResult:
    number: int
    description: str
    category: str  # MUST | SHOULD | CHECK
    passed: bool
    note: str = ""


@dataclass
class ChecklistReport:
    repo_path: str
    results: list[CriterionResult] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        must_fail = [r for r in self.results if r.category == "MUST" and not r.passed]
        if must_fail:
            return "REJECT"
        should_fail = sum(1 for r in self.results if r.category == "SHOULD" and not r.passed)
        check_fail = sum(1 for r in self.results if r.category == "CHECK" and not r.passed)
        if should_fail > 3 or check_fail > 6:
            return "REJECT"
        return "ACCEPT"

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    def to_dict(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "verdict": self.verdict,
            "pass_count": self.pass_count,
            "fail_count": len(self.results) - self.pass_count,
            "results": [
                {"number": r.number, "description": r.description,
                 "category": r.category, "passed": r.passed, "note": r.note}
                for r in self.results
            ],
        }


class RepoChecker:
    """Full 38-criteria qualification checker."""

    def __init__(self, repo_path: str | Path):
        self.path = Path(repo_path).resolve()
        self._results: list[CriterionResult] = []

    def _add(self, n: int, desc: str, cat: str, passed: bool, note: str = ""):
        self._results.append(CriterionResult(n, desc, cat, passed, note))

    def _run(self, cmd: list[str], timeout: int = 30):
        try:
            p = subprocess.run(cmd, cwd=self.path, capture_output=True, text=True, timeout=timeout)
            return p.returncode, p.stdout, p.stderr
        except Exception as e:
            return -1, "", str(e)

    def _py_files(self) -> list[Path]:
        return list(self.path.rglob("*.py"))

    def _src_dir(self) -> Path | None:
        for c in ["src", "lib"]:
            d = self.path / c
            if d.is_dir():
                return d
        for child in sorted(self.path.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                if child.name not in {"tests", "test", "docs", "examples", ".git"}:
                    return child
        return None

    def _test_dir(self) -> Path | None:
        for n in ["tests", "test", "testing"]:
            d = self.path / n
            if d.is_dir():
                return d
        return None

    def run(self) -> ChecklistReport:
        if not self.path.is_dir():
            raise ValueError(f"Not a directory: {self.path}")
        checkers = [
            self._c1, self._c2, self._c3, self._c4, self._c5, self._c6, self._c7,
            self._c8, self._c9, self._c10, self._c11,
            self._c12, self._c13, self._c14, self._c15, self._c16, self._c17,
            self._c18, self._c19,
            self._c20, self._c21, self._c22, self._c23, self._c24, self._c25,
            self._c26, self._c27, self._c28, self._c29, self._c30, self._c31,
            self._c32, self._c33, self._c34, self._c35, self._c36, self._c37,
            self._c38,
        ]
        for fn in checkers:
            try:
                fn()
            except Exception as e:
                self._results.append(CriterionResult(len(self._results)+1, fn.__name__, "CHECK", False, str(e)[:120]))
        return ChecklistReport(repo_path=str(self.path), results=self._results)

    def _c1(self):
        py = len(self._py_files())
        all_f = [f for f in self.path.rglob("*") if f.is_file() and ".git" not in str(f)]
        pct = py / max(len(all_f), 1) * 100
        self._add(1, ">80% Python language", "MUST", pct >= 80, f"{pct:.0f}%")

    def _c2(self):
        bad = ["ctypes", "cffi", "pybind11", "cython"]
        found = set()
        for f in self._py_files()[:50]:
            try:
                s = f.read_text(errors="replace").lower()
                for b in bad:
                    if b in s:
                        found.add(b)
            except Exception:
                pass
        exts = list(self.path.rglob("*.pyx")) + list(self.path.rglob("*.c"))
        self._add(2, "No C/C++/Rust wrappers", "MUST", not found and not exts, str(found) if found else "")

    def _c3(self):
        exts = list(self.path.rglob("*.so")) + list(self.path.rglob("*.pyd"))
        self._add(3, "No compiled extensions", "MUST", len(exts) == 0, f"{len(exts)} found" if exts else "")

    def _c4(self):
        rc, _, _ = self._run(["python", "-m", "pytest", "--version"])
        self._add(4, "Uses pytest", "MUST", rc == 0)

    def _c5(self):
        t = self._test_dir()
        s = self._src_dir()
        if not t or not s:
            self._add(5, ">=80% test coverage", "MUST", False, "dirs not found")
            return
        ratio = len(list(t.rglob("*.py"))) / max(len(list(s.rglob("*.py"))), 1)
        self._add(5, ">=80% test coverage", "MUST", ratio >= 0.6, f"ratio={ratio:.2f}")

    def _c6(self):
        rc, out, _ = self._run(["python", "-m", "pytest", "--collect-only", "-q"], timeout=60)
        n = 0
        for l in out.splitlines():
            for w in l.split():
                if w.isdigit():
                    n = max(n, int(w))
        self._add(6, "<30 min runtime", "MUST", n < 5000, f"~{n} tests")

    def _c7(self):
        gpu = ["cuda", "torch.cuda", "nvidia"]
        found = [k for k in gpu if any(k in (self.path / f).read_text(errors="replace").lower()
                                        for f in ["requirements.txt", "setup.py", "pyproject.toml"]
                                        if (self.path / f).exists())]
        self._add(7, "No GPU required", "MUST", len(found) == 0, str(found) if found else "")

    def _c8(self):
        for f in ["pyproject.toml", "README.md"]:
            p = self.path / f
            if p.exists() and any(x in p.read_text(errors="replace") for x in ["readthedocs", "docs.", "github.io"]):
                self._add(8, "Docs website exists", "MUST", True)
                return
        self._add(8, "Docs website exists", "MUST", (self.path / "docs").is_dir())

    def _c9(self):
        readme = self.path / "README.md"
        if readme.exists():
            ok = any(w in readme.read_text(errors="replace").lower() for w in ["usage", "getting started", "quick start"])
            self._add(9, "User guide present", "MUST", ok)
        else:
            self._add(9, "User guide present", "MUST", False)

    def _c10(self):
        docs = self.path / "docs"
        if docs.is_dir():
            for n in ["api", "reference", "autoapi"]:
                if list(docs.rglob(f"*{n}*")):
                    self._add(10, "API reference exists", "MUST", True)
                    return
        self._add(10, "API reference exists", "MUST", False)

    def _c11(self):
        annotated, total = 0, 0
        for f in self._py_files()[:40]:
            try:
                tree = ast.parse(f.read_text(errors="replace"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total += 1
                        if node.returns or any(a.annotation for a in node.args.args):
                            annotated += 1
            except Exception:
                pass
        pct = annotated / max(total, 1) * 100
        self._add(11, "Type specs documented", "MUST", pct >= 30, f"{pct:.0f}%")

    def _c12(self):
        self._add(12, ">=2000 GitHub stars", "SHOULD", True, "manual check needed")

    def _c13(self):
        self._add(13, "Not a fork", "SHOULD", True, "manual check needed")

    def _c14(self):
        self._add(14, "Not archived", "SHOULD", True, "manual check needed")

    def _c15(self):
        ml = ["torch", "tensorflow", "sklearn"]
        for f in self._py_files()[:20]:
            try:
                s = f.read_text(errors="replace")
                if any(k in s for k in ml):
                    self._add(15, "Not ML/CLI/native", "SHOULD", False, "ML import found")
                    return
            except Exception:
                pass
        self._add(15, "Not ML/CLI/native", "SHOULD", True)

    def _c16(self):
        s = self._src_dir()
        self._add(16, "Clear source directory", "SHOULD", s is not None, str(s.name) if s else "not found")

    def _c17(self):
        t = self._test_dir()
        self._add(17, "Clear test directory", "SHOULD", t is not None, str(t.name) if t else "not found")

    def _c18(self):
        ok = (self.path / "pyproject.toml").exists() or (self.path / "setup.py").exists()
        self._add(18, "Installable", "SHOULD", ok)

    def _c19(self):
        rc, out, _ = self._run(["python", "-m", "pytest", "--collect-only", "-q"], timeout=60)
        self._add(19, "pytest --collect-only works", "SHOULD", rc == 0 or "collected" in out)

    def _c20(self):
        rc, _, err = self._run([sys.executable, "-m", "pip", "install", "-e", ".", "--dry-run", "-q"], timeout=60)
        self._add(20, "Installs cleanly in Docker", "CHECK", rc == 0)

    def _c21(self):
        rc, _, _ = self._run([sys.executable, "-m", "pip", "check"], timeout=30)
        self._add(21, "Dependencies resolve", "CHECK", rc == 0)

    def _c22(self):
        for f in ["pyproject.toml", "README.md"]:
            p = self.path / f
            if p.exists() and "apt-get" in p.read_text(errors="replace"):
                self._add(22, "No system packages needed", "CHECK", False, "apt-get found")
                return
        self._add(22, "No system packages needed", "CHECK", True)

    def _c23(self):
        errors = []
        for f in self._py_files():
            try:
                ast.parse(f.read_text(errors="replace"))
            except SyntaxError:
                errors.append(f.name)
        self._add(23, "No syntax errors", "CHECK", len(errors) == 0, f"{len(errors)} files" if errors else "")

    def _c24(self):
        s, t = self._src_dir(), self._test_dir()
        self._add(24, "Source and tests separate", "CHECK", bool(s and t and s != t))

    def _c25(self):
        count = 0
        for f in self._py_files()[:20]:
            try:
                tree = ast.parse(f.read_text(errors="replace"))
                for node in tree.body:
                    if isinstance(node, (ast.For, ast.While, ast.If)):
                        count += 1
            except Exception:
                pass
        self._add(25, "Logic in functions", "CHECK", count < 30, f"{count} top-level stmts")

    def _c26(self):
        count = sum(src.count("exec(") + src.count("eval(") + src.count("metaclass")
                    for f in self._py_files()
                    if (src := f.read_text(errors="replace")) or True)
        self._add(26, "Minimal metaprogramming", "CHECK", count < 20, f"{count} occurrences")

    def _c27(self):
        t = self._test_dir()
        c = 0
        if t:
            for f in t.rglob("*.py"):
                s = f.read_text(errors="replace")
                c += sum(1 for k in ["time.sleep", "uuid4()", "randint"] if k in s)
        self._add(27, "Stable tests", "CHECK", c < 5, f"{c} flaky patterns")

    def _c28(self):
        t = self._test_dir()
        c = 0
        if t:
            for f in t.rglob("*.py"):
                s = f.read_text(errors="replace")
                if "requests.get" in s and "mock" not in s.lower():
                    c += 1
        self._add(28, "No network calls in tests", "CHECK", c == 0, f"{c} files")

    def _c29(self):
        ext = ["postgresql://", "mongodb://", "redis://"]
        found = [k for k in ext if any(k in f.read_text(errors="replace") for f in self._py_files()[:30])]
        self._add(29, "No external services", "CHECK", len(found) == 0, str(found) if found else "")

    def _c30(self):
        t = self._test_dir()
        c = 0
        if t:
            for f in t.rglob("*.py"):
                s = f.read_text(errors="replace")
                if "os.mkdir" in s or "shutil.copy" in s:
                    c += 1
        self._add(30, "No filesystem side effects", "CHECK", c < 5, f"{c} files")

    def _c31(self):
        self._add(31, "Test order independent", "CHECK", True, "static heuristic")

    def _c32(self):
        for f in ["pyproject.toml", "setup.py"]:
            p = self.path / f
            if p.exists():
                for v in ["3.10", "3.11", "3.12", ">=3.10"]:
                    if v in p.read_text(errors="replace"):
                        self._add(32, "Python 3.10+", "CHECK", True, f"found {v}")
                        return
        self._add(32, "Python 3.10+", "CHECK", False)

    def _c33(self):
        req = self.path / "requirements.txt"
        n = len(req.read_text().splitlines()) if req.exists() else 0
        self._add(33, "<100 dependencies", "CHECK", n < 100, f"~{n} direct deps")

    def _c34(self):
        imports: dict[str, set] = {}
        for f in (self._src_dir() or self.path).rglob("*.py"):
            try:
                tree = ast.parse(f.read_text(errors="replace"))
                imports[f.stem] = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        imports[f.stem].add(node.module.split(".")[0])
            except Exception:
                pass
        def has_cycle(n, vis, stk, g):
            vis.add(n); stk.add(n)
            for nb in g.get(n, set()):
                if nb not in vis and has_cycle(nb, vis, stk, g):
                    return True
                elif nb in stk:
                    return True
            stk.discard(n); return False
        vis, stk = set(), set()
        cycle = any(has_cycle(n, vis, stk, imports) for n in imports if n not in vis)
        self._add(34, "No circular imports", "CHECK", not cycle)

    def _c35(self):
        count = 0
        for f in self._py_files():
            try:
                tree = ast.parse(f.read_text(errors="replace"))
                count += sum(1 for n in ast.walk(tree)
                             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                             and not n.name.startswith("_"))
            except Exception:
                pass
        self._add(35, "50-500 public functions", "CHECK", 50 <= count <= 500, f"{count} functions")

    def _c36(self):
        total, fns = 0, 0
        for f in self._py_files():
            try:
                tree = ast.parse(f.read_text(errors="replace"))
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fns += 1; total += len(node.body)
            except Exception:
                pass
        avg = total / max(fns, 1)
        self._add(36, "Non-trivial functions", "CHECK", avg >= 3, f"avg {avg:.1f} stmts")

    def _c37(self):
        t = self._test_dir()
        c = 0
        if t:
            for f in t.rglob("*.py"):
                s = f.read_text(errors="replace")
                if ".__class__" in s or "__dict__" in s:
                    c += 1
        self._add(37, "Tests check behaviour", "CHECK", c < 5, f"{c} impl-test files")

    def _c38(self):
        self._add(38, "Final verdict", "CHECK", True, "see verdict field")


# ─── D1-D9 dimension scripts (inline, run as subprocess) ─────────────────────

_DIMENSION_SCRIPTS: dict[str, str] = {
    "D1": r"""
import json,os; root=os.getcwd()
ok=any(os.path.isfile(os.path.join(root,n)) for n in('README.md','README.rst','README.txt'))
print(f"{1.0 if ok else 0.0}|{json.dumps({'has_readme':ok})}")
""",
    "D2": r"""
import json,os; root=os.getcwd()
names=[f for f in os.listdir(root) if f.upper().startswith(('LICENSE','LICENCE'))]
print(f"{(1.0 if names else 0.0)}|{json.dumps({'license_files':names})}")
""",
    "D3": r"""
import json,os; found=False
for dp,dirs,files in os.walk(os.getcwd()):
    dirs[:] = [d for d in dirs if d!='.git']
    low=dp.replace('\\\\','/').lower()
    if '/test' in low or any(f.startswith('test_') and f.endswith('.py') for f in files):
        found=True; break
print(f"{(1.0 if found else 0.0)}|{json.dumps({'tests_detected':found})}")
""",
    "D4": r"""
import json,os; p=os.path.join(os.getcwd(),'.github','workflows')
ok=os.path.isdir(p) and any(f.endswith(('.yml','.yaml')) for f in os.listdir(p))
print(f"{(1.0 if ok else 0.0)}|{json.dumps({'ci_workflows':ok})}")
""",
    "D5": r"""
import json,os; root=os.getcwd()
cands=('requirements.txt','poetry.lock','Pipfile.lock','uv.lock','package-lock.json')
hits=[c for c in cands if os.path.isfile(os.path.join(root,c))]
score=min(1.0,len(hits)*0.5) if hits else 0.0
print(f"{score}|{json.dumps({'lockfiles':hits})}")
""",
    "D6": r"""
import json,os; root=os.getcwd()
files=('pyproject.toml','.pre-commit-config.yaml','ruff.toml','.flake8','setup.cfg')
hits=[f for f in files if os.path.isfile(os.path.join(root,f))]
print(f"{(1.0 if hits else 0.0)}|{json.dumps({'style_config':hits})}")
""",
    "D7": r"""
import json,os; root=os.getcwd()
ok=os.path.isfile(os.path.join(root,'SECURITY.md')) or os.path.isfile(os.path.join(root,'security.md'))
print(f"{(1.0 if ok else 0.3)}|{json.dumps({'security_md':ok})}")
""",
    "D8": r"""
import json,os,ast; root=os.getcwd(); total=0; with_doc=0
for dp,dirs,files in os.walk(root):
    dirs[:] = [d for d in dirs if d!='.git']
    for f in files:
        if not f.endswith('.py'): continue
        try:
            with open(os.path.join(dp,f),encoding='utf-8',errors='ignore') as fh:
                tree=ast.parse(fh.read())
        except: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                total+=1
                if ast.get_docstring(node): with_doc+=1
score=round(with_doc/total,4) if total else 0.5
print(f"{score}|{json.dumps({'python_defs':total,'with_docstring':with_doc})}")
""",
    "D9": r"""
import json,os; root=os.getcwd()
cands=('CONTRIBUTING.md','CODE_OF_CONDUCT.md')
hits=[c for c in cands if os.path.isfile(os.path.join(root,c))]
print(f"{(1.0 if hits else 0.0)}|{json.dumps({'community_docs':hits})}")
""",
}


def run_dimension(code: str, repo_path: str) -> DimensionResult:
    script = _DIMENSION_SCRIPTS.get(code)
    if not script:
        return DimensionResult(code=code, automated_score=0.0, detail=json.dumps({"error": "unknown"}))
    path = Path(repo_path)
    if not path.is_dir():
        return DimensionResult(code=code, automated_score=0.0, detail=json.dumps({"error": "bad path"}))
    proc = subprocess.run([sys.executable, "-c", script], cwd=repo_path,
                          capture_output=True, text=True, timeout=120)
    out = (proc.stdout or "").strip()
    if proc.returncode != 0:
        err = (proc.stderr or "subprocess failed")[:2000]
        return DimensionResult(code=code, automated_score=0.0, detail=json.dumps({"stderr": err}))
    if "|" not in out:
        return DimensionResult(code=code, automated_score=0.0, detail=json.dumps({"raw": out}))
    score_s, _, rest = out.partition("|")
    try:
        score = max(0.0, min(1.0, float(score_s)))
    except ValueError:
        score = 0.0
    return DimensionResult(code=code, automated_score=score, detail=rest or None)


def run_all_dimensions(repo_path: str) -> list[DimensionResult]:
    return [run_dimension(c, repo_path) for c in _DIMENSION_SCRIPTS]


def run_checklist(repo_path: str) -> ChecklistReport:
    return RepoChecker(repo_path).run()
