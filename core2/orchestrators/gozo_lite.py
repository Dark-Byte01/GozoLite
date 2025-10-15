from __future__ import annotations
import os, shlex, shutil, subprocess, tempfile, time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Tuple, Callable, Optional

@dataclass
class LangSpec:
    suffix: str
    tools: Tuple[str, ...]
    cmd_builder: Callable[[Path, str, Path], str]

class GozoLite:
    MODE = "gozo-lite"

    def __init__(self, memory=None):
        self.memory = memory
        self.registry = self._build_registry()
        # Ajustes mínimos por compiladores/lanzadores más pesados
        self.min_timeout = {"kotlin": 60, "zig": 60, "scala": 20, "haskell": 20, "typescript": 10}

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        language = (payload.get("language") or "").strip().lower()
        code = payload.get("code") or ""
        stdin = payload.get("stdin")  # NUEVO: soporta entrada estándar
        req_to = int(payload.get("timeout") or 10)
        timeout = max(req_to, self.min_timeout.get(language, 10))

        if not language or language not in self.registry:
            return self._fail(2, f"Lenguaje no soportado: {language or '(vacío)'}")

        spec = self.registry[language]
        missing = [t for t in spec.tools if not self._which(t)]
        if missing:
            return self._fail(127, f"{'/'.join(missing)} no instalado", language=language)

        workdir = Path(tempfile.mkdtemp(prefix="ce-", dir="/tmp"))
        try:
            src = self._write_source(language, spec.suffix, code, workdir)
            cmd = spec.cmd_builder(src, code, workdir)
            started = time.monotonic()
            proc = subprocess.run(
                ["bash", "-lc", cmd],
                cwd=str(workdir),
                text=True,
                input=stdin if isinstance(stdin, str) else None,  # NUEVO
                capture_output=True,
                timeout=timeout
            )
            elapsed = int((time.monotonic() - started) * 1000)
            return {
                "ok": proc.returncode == 0,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "time_ms": elapsed,
                "mode": self.MODE,
                "language": language
            }
        except subprocess.TimeoutExpired:
            elapsed = int((time.monotonic() - started) * 1000)
            return self._fail(124, "Timeout", time_ms=elapsed, language=language)
        except Exception as e:
            return self._fail(1, f"Excepción: {e}", language=language)
        finally:
            try:
                for p in workdir.iterdir():
                    try:
                        if p.is_dir():
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            p.unlink(missing_ok=True)
                    except Exception:
                        pass
                workdir.rmdir()
            except Exception:
                pass

    def status(self, job_id: str) -> Dict[str, Any]:
        return {"job_id": job_id, "state": "unsupported", "detail": "GozoLite es síncrono"}

    @staticmethod
    def _which(bin_name: str) -> Optional[str]:
        return shutil.which(bin_name)

    def _fail(self, code: int, msg: str, time_ms: int = 0, language: Optional[str] = None) -> Dict[str, Any]:
        return {
            "ok": False,
            "exit_code": code,
            "stdout": "",
            "stderr": msg,
            "time_ms": time_ms,
            "mode": self.MODE,
            "language": language or "-"
        }

    def _write_source(self, language: str, suffix: str, code: str, workdir: Path) -> Path:
        if language == "java":
            path = workdir / "Main.java"
            path.write_text(code, encoding="utf-8")
            return path
        if language == "scala":
            if "object Main" not in code and "class Main" not in code:
                code = f"object Main extends App {{\n{code}\n}}\n"
            path = workdir / "Main.scala"
            path.write_text(code, encoding="utf-8")
            return path
        if language == "make":
            path = workdir / "Makefile"
            path.write_text(code, encoding="utf-8")
            return path
        fd, tmp = tempfile.mkstemp(prefix="code_", suffix=suffix, dir=str(workdir))
        os.close(fd)
        path = Path(tmp)
        path.write_text(code, encoding="utf-8")
        if language == "bash":
            path.chmod(0o755)
        return path

    def _build_registry(self) -> Dict[str, LangSpec]:
        R: Dict[str, LangSpec] = {}

        def _cmd(fmt: str, **kw) -> str:
            return fmt.format(**{k: shlex.quote(str(v)) for k, v in kw.items()})

        # Core
        R["python"] = LangSpec(".py", ("python3",), lambda s, _c, _w: _cmd("python3 {src}", src=s))
        R["node"]   = LangSpec(".js", ("node",),    lambda s, _c, _w: _cmd("node {src}", src=s))
        R["bash"]   = LangSpec(".sh", ("bash",),    lambda s, _c, _w: _cmd("bash {src}", src=s))
        R["c"]      = LangSpec(".c",  ("gcc",),     lambda s, _c, w: _cmd("gcc -O2 -s -o {out} {src} && {out}", src=s, out=w/"c.out"))
        R["cpp"]    = LangSpec(".cpp",("g++",),     lambda s, _c, w: _cmd("g++ -O2 -s -o {out} {src} && {out}", src=s, out=w/"cpp.out"))
        R["java"]   = LangSpec(".java",("javac","java"),
                               lambda _s, _c, w: _cmd("mkdir -p {out} && javac {main} -d {out} && java -cp {out} Main",
                                                      out=w/"out", main=w/"Main.java"))
        R["go"]     = LangSpec(".go", ("go",),      lambda s, _c, w: _cmd("go build -ldflags='-s -w' -o {out} {src} && {out}", src=s, out=w/"go.out"))
        R["rust"]   = LangSpec(".rs", ("rustc",),   lambda s, _c, w: _cmd("rustc -C opt-level=2 -o {out} {src} && {out}", src=s, out=w/"rust.out"))
        R["sql"]    = LangSpec(".sql",("sqlite3",), lambda s, _c, _w: _cmd("sqlite3 :memory: '.read {src}'", src=s))

        # Scripting
        R["ruby"] = LangSpec(".rb", ("ruby",),  lambda s, _c, _w: _cmd("ruby {src}", src=s))
        R["php"]  = LangSpec(".php",("php",),   lambda s, _c, _w: _cmd("php {src}", src=s))
        R["r"]    = LangSpec(".R",  ("Rscript",),lambda s, _c, _w: _cmd("Rscript {src}", src=s))
        R["lua"]  = LangSpec(".lua",("lua",),   lambda s, _c, _w: _cmd("lua {src}", src=s))
        R["perl"] = LangSpec(".pl", ("perl",),  lambda s, _c, _w: _cmd("perl {src}", src=s))
        R["tcl"]  = LangSpec(".tcl",("tclsh",), lambda s, _c, _w: _cmd("tclsh {src}", src=s))

        # CLI extras
        R["awk"]  = LangSpec(".awk",("awk",),   lambda s, _c, _w: _cmd("awk -f {src} /dev/null", src=s))
        R["sed"]  = LangSpec(".sed",("sed",),   lambda s, _c, _w: _cmd("echo x | sed -f {src}", src=s))
        R["make"] = LangSpec(".mk", ("make",),  lambda _s, _c, w: _cmd("make -C {w} -f {mk}", w=w, mk=w/"Makefile"))
        R["bc"]   = LangSpec(".bc", ("bc",),    lambda s, _c, _w: _cmd("cat {src} | bc -l", src=s))

        # JVM/funcionales
        R["kotlin"]  = LangSpec(".kt", ("kotlinc","java"),
                                lambda s, _c, w: _cmd("kotlinc {src} -include-runtime -d {jar} && java -jar {jar}",
                                                      src=s, jar=w/"kotlin.jar"))
        R["scala"]   = LangSpec(".scala", ("scalac","scala"),
                                lambda s, _c, w: _cmd("mkdir -p {out} && scalac -d {out} {src} && scala -nc -cp {out} Main",
                                                      src=s, out=w/"scala_out"))
        R["haskell"] = LangSpec(".hs", ("runghc",), lambda s, _c, _w: _cmd("runghc {src}", src=s))
        R["ocaml"]   = LangSpec(".ml", ("ocaml",),  lambda s, _c, _w: _cmd("ocaml {src}", src=s))
        R["dart"]    = LangSpec(".dart",("dart",),  lambda s, _c, _w: _cmd("dart {src}", src=s))

        # Legacy/modern
        R["fortran"] = LangSpec(".f90",("gfortran",), lambda s, _c, w: _cmd("gfortran -O2 -o {out} {src} && {out}", src=s, out=w/"fortran.out"))
        R["pascal"]  = LangSpec(".pas",("fpc",),      lambda s, _c, w: _cmd("fpc -O2 -o{out} {src} && {out}", src=s, out=w/"pascal.out"))
        R["ada"]     = LangSpec(".adb",("gnatmake",), lambda s, _c, w: _cmd("gnatmake -q -o {out} {src} && {out}", src=s, out=w/"ada.out"))
        R["cobol"]   = LangSpec(".cob",("cobc",),     lambda s, _c, w: _cmd("cobc -x -O2 -o {out} {src} && {out}", src=s, out=w/"cobol.out"))
        R["zig"]     = LangSpec(".zig",("zig",),      lambda s, _c, w: _cmd("ZIG_GLOBAL_CACHE_DIR={cache} ZIG_LOCAL_CACHE_DIR={cache} zig run {src}",
                                                                            src=s, cache=w/"zig-cache"))

        # TypeScript (reemplazo de Nim) — requiere `npm i -g typescript ts-node`
        R["typescript"] = LangSpec(".ts", ("ts-node",),
                                   # --transpile-only acelera (no type-check estricto)
                                   lambda s, _c, _w: _cmd("ts-node --transpile-only {src}", src=s))

        return R