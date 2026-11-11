#!/usr/bin/env python3
"""Render the landing page's frames from a strop binary.

    python3 tools/frames.py /path/to/strop --paths /path/to/linux-paths.txt.gz

Every frame is the released binary's own screen. For each scenario the
script below is run twice over the same fixture:

1. through `strop headless SCRIPT FILE`, the editor's scripted driver, which
   settles its own work and prints the cell grid as plain text;
2. through the interactive binary in a detached tmux pane, with the same
   keys, until the pane's text equals the headless frame cell for cell.

The headless frame has no colour, so the colours come from the pane
(`tmux capture-pane -e`) and `ansi2svg` turns that into an SVG. A scenario
whose two runs never agree fails; nothing is drawn or retouched.

Fixtures, both built fresh in a temporary directory:

- `tree/`  one stub file per line of `--paths` (the Linux kernel's file
  list, the fixture the editor's own ranking tests use:
  `crates/strop-picker/fixtures/linux-*-paths.txt.gz` in the strop repo);
- `tally/` `tools/fixture/project` committed to a git repository at a fixed
  date, then `tools/fixture/changes` copied over it: one file staged, two
  modified, one untracked.

A scenario lists candidates, newest surface first. The first whose frame
contains its `expect` strings is used, so the same command works on a
binary that predates a surface; `img/frames.json` records which candidate
each frame is, and `build.py` writes the captions from it.

Needs tmux and git. Python 3.8+, standard library only.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ansi2svg  # noqa: E402

SITE = Path(__file__).resolve().parent.parent
FIXTURE = SITE / "tools" / "fixture"
COLS, ROWS = 100, 30

# A candidate: `script` is a headless driver script (docs/terminal-and-scripting.md),
# `project`/`file` say where the editor starts, `expect` are strings the frame must
# contain, and `caption` is what the page says under it.
SCENARIOS = [
    {
        "name": "find",
        "tab": "Find",
        "candidates": [
            {
                "id": "files",
                "project": "tree",
                "file": None,
                "script": "keys <space>f\nsettle\nkeys sched.h\nsettle\n",
                "expect": ["files", "sched.h", "{paths:,}"],
                "caption": "<kbd>Space</kbd> <kbd>f</kbd>, then <code>sched.h</code>, in a tree with the "
                           "Linux kernel's {paths:,} file paths. The fixture has the kernel's paths, "
                           "not its sources: each file is a two-line stub, which is what the preview shows.",
                "alt": "The strop file finder over {paths:,} files with sched.h typed: a list of matching "
                       "file names with their directories on the left, a preview of the selected file on the right.",
            },
        ],
    },
    {
        "name": "replace",
        "tab": "Search and replace",
        "candidates": [
            {
                "id": "replace",
                "project": "tally",
                "file": "README.md",
                "script": "keys <space>R\nsettle\nkeys total_cents<tab>sum_cents\nsettle\n",
                "expect": ["Find total_cents", "With sum_cents", "sum_cents(&self)"],
                "caption": "<kbd>Space</kbd> <kbd>R</kbd> in a small Rust project: <code>total_cents</code> "
                           "to <code>sum_cents</code>. Every hit is listed under its file as a "
                           "<code>-</code> row and a <code>+</code> row while you type; nothing has "
                           "changed on disk yet.",
                "alt": "strop's search with a Find field reading total_cents and a With field reading "
                       "sum_cents; below, each hit grouped by file as a removed line and an added line, "
                       "and a preview of the first file on the right.",
            },
        ],
    },
    {
        "name": "git",
        "tab": "Git",
        "candidates": [
            {
                "id": "status-diff",
                "project": "tally",
                "file": "README.md",
                # ]c twice lands on the second unstaged file, whose diff fills the frame.
                "script": "settle\nkeys <space>gg\nsettle\nkeys ]c]c=\nsettle\n",
                "expect": ["git status", "Staged", "Unstaged", "Untracked", "@@", "is_empty"],
                "caption": "<kbd>Space</kbd> <kbd>g</kbd> <kbd>g</kbd>: the status buffer of the same "
                           "project, with one file's diff opened by <kbd>=</kbd>. <kbd>s</kbd> stages "
                           "and <kbd>u</kbd> unstages the file or hunk under the cursor.",
                "alt": "strop's git status buffer: sections for staged, unstaged and untracked files, "
                       "with the diff of one file shown under its row.",
            },
            {
                "id": "status",
                "project": "tally",
                "file": "README.md",
                "script": "settle\nkeys <space>gg\nsettle\n",
                "expect": ["git status", "Staged", "Unstaged", "Untracked"],
                "caption": "<kbd>Space</kbd> <kbd>g</kbd> <kbd>g</kbd>: the status buffer of the same "
                           "project. <kbd>s</kbd> stages and <kbd>u</kbd> unstages the file under the "
                           "cursor; <kbd>=</kbd> shows its diff.",
                "alt": "strop's git status buffer: sections for staged, unstaged and untracked files.",
            },
            {
                # Before 0.62 there is no status buffer; the hunk preview is the git surface to show.
                "id": "hunk",
                "project": "tally",
                "file": "README.md",
                "script": "settle\nkeys ]c<space>gp\nsettle\n",
                "expect": ["hunk", "@@"],
                "caption": "<kbd>]c</kbd> to the next changed hunk, then <kbd>Space</kbd> <kbd>g</kbd> "
                           "<kbd>p</kbd>: the hunk under the cursor as a diff, in an ordinary read-only buffer.",
                "alt": "strop showing one git hunk as a diff: old and new line numbers in two columns, "
                       "the removed and added lines marked in the gutter.",
            },
        ],
    },
]

STUB_C = ("/* SPDX-License-Identifier: GPL-2.0 */\n"
          "/* A stub. This fixture has the kernel's file paths, not its sources. */\n")
STUB_OTHER = ("# SPDX-License-Identifier: GPL-2.0\n"
              "# A stub. This fixture has the kernel's file paths, not its sources.\n")
C_LIKE = (".c", ".h", ".S", ".dts", ".dtsi", ".rs", ".cc", ".cpp", ".lds")

KEY_NAMES = {"space": " ", "cr": "Enter", "esc": "Escape", "tab": "Tab", "bs": "BSpace", "lt": "<"}


def run(cmd: List[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


# --------------------------------------------------------------------------- fixtures

def build_tree(root: Path, paths_file: Path) -> int:
    opener = gzip.open if paths_file.suffix == ".gz" else open
    made = set()
    count = 0
    with opener(paths_file, "rt", encoding="utf-8") as lines:
        for line in lines:
            rel = line.rstrip("\n")
            if not rel or rel.startswith("/") or ".." in rel.split("/"):
                continue
            path = root / rel
            if path.parent not in made:
                path.parent.mkdir(parents=True, exist_ok=True)
                made.add(path.parent)
            path.write_text(STUB_C if rel.endswith(C_LIKE) else STUB_OTHER, encoding="utf-8")
            count += 1
    if count == 0:
        raise SystemExit(f"{paths_file}: no paths")
    return count


def build_tally(root: Path) -> None:
    shutil.copytree(FIXTURE / "project", root)
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_AUTHOR_DATE="2026-03-02T09:00:00Z", GIT_COMMITTER_DATE="2026-03-02T09:00:00Z")
    git = ["git", "-C", str(root), "-c", "user.name=Dana Reyes", "-c", "user.email=dana@example.com"]
    run(git + ["init", "-q", "-b", "main"], env=env)
    run(git + ["add", "-A"], env=env)
    run(git + ["commit", "-q", "-m", "Sum a ledger and print a report"], env=env)
    shutil.copytree(FIXTURE / "changes", root, dirs_exist_ok=True)
    run(git + ["add", "src/report.rs"], env=env)


def editor_env(home: Path) -> Dict[str, str]:
    """A hermetic environment: an empty home, no language servers on PATH, truecolor."""
    home.mkdir(parents=True)
    return {
        "HOME": str(home), "XDG_CONFIG_HOME": str(home / "config"), "XDG_STATE_HOME": str(home / "state"),
        "XDG_CACHE_HOME": str(home / "cache"), "XDG_DATA_HOME": str(home / "data"),
        "PATH": "/usr/bin:/bin", "TERM": "xterm-256color", "COLORTERM": "truecolor", "LANG": "C.UTF-8",
        "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
    }


# --------------------------------------------------------------------------- the two runs

def grid_text(text: str) -> List[str]:
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return lines


def headless_frame(binary: Path, script: str, cwd: Path, file: Optional[str], work: Path, tag: str) -> List[str]:
    path = work / f"{tag}.keys"
    path.write_text(f"resize {COLS} {ROWS}\n{script}frame\n", encoding="utf-8")
    cmd = [str(binary), "headless", str(path)] + ([file] if file else [])
    done = subprocess.run(cmd, cwd=cwd, env=editor_env(work / f"home-headless-{tag}"),
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise SystemExit(f"{tag}: strop headless failed ({done.returncode}):\n{done.stderr.strip()}")
    lines = done.stdout.split("\n")
    if not lines or not lines[0].startswith("─── frame"):
        raise SystemExit(f"{tag}: unexpected headless output: {lines[:1]}")
    return grid_text("\n".join(lines[1:]))


class Pane:
    """The interactive binary in a detached tmux pane of exactly COLS×ROWS cells."""

    def __init__(self, binary: Path, cwd: Path, file: Optional[str], env: Dict[str, str], socket: str):
        self.tmux = ["tmux", "-L", socket, "-f", os.devnull]
        command = ["env", "-i"] + [f"{k}={v}" for k, v in env.items()]
        command += [str(binary), "--theme", "hone"] + ([file] if file else [])
        run(self.tmux + ["new-session", "-d", "-s", "frame", "-x", str(COLS), "-y", str(ROWS),
                         "-c", str(cwd)] + command)

    def text(self) -> List[str]:
        return grid_text(run(self.tmux + ["capture-pane", "-p", "-t", "frame"]).stdout)

    def ansi(self) -> str:
        return run(self.tmux + ["capture-pane", "-e", "-p", "-t", "frame"]).stdout

    def stable(self, quiet: float = 0.4, timeout: float = 30.0) -> List[str]:
        """Wait until the screen has text and has not changed for `quiet` seconds."""
        deadline = time.monotonic() + timeout
        last, since = None, time.monotonic()
        while time.monotonic() < deadline:
            now = self.text()
            if now != last:
                last, since = now, time.monotonic()
            elif now and time.monotonic() - since >= quiet:
                return now
            time.sleep(0.05)
        raise SystemExit("the pane never settled")

    def keys(self, text: str) -> None:
        for token in re.findall(r"<[^<>\s]+>|[^<]+|<", text):
            m = re.fullmatch(r"<([^<>]+)>", token)
            if not m:
                run(self.tmux + ["send-keys", "-t", "frame", "-l", token])
                continue
            name = m.group(1).lower()
            if name in KEY_NAMES:
                key = KEY_NAMES[name]
                literal = len(key) == 1
                run(self.tmux + ["send-keys", "-t", "frame"] + (["-l", key] if literal else [key]))
            elif re.fullmatch(r"c-.", name):
                run(self.tmux + ["send-keys", "-t", "frame", "C-" + name[2]])
            else:
                raise SystemExit(f"key {token} has no tmux spelling here")

    def drive(self, script: str) -> None:
        self.stable()
        for line in script.splitlines():
            verb, _, rest = line.partition(" ")
            if verb == "keys":
                self.keys(rest)
            elif verb == "settle":
                self.stable()
            elif verb == "wait":
                time.sleep(int(rest) / 1000)
            elif verb:
                raise SystemExit(f"script verb {verb!r} is not driven in the pane")

    def until(self, want: List[str], timeout: float = 30.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.text() == want:
                return
            time.sleep(0.1)
        got = self.text()
        rows = [f"  row {i + 1}:\n    headless {a!r}\n    pane     {b!r}"
                for i, (a, b) in enumerate(zip(want + [""] * ROWS, got + [""] * ROWS)) if a != b]
        raise SystemExit("the pane does not show the headless frame:\n" + "\n".join(rows[:8]))

    def close(self) -> None:
        subprocess.run(self.tmux + ["kill-server"], capture_output=True)


def hone_defaults() -> Dict[str, str]:
    css = (SITE / "assets" / "site.css").read_text(encoding="utf-8")
    block = css[css.index(':root, :root[data-palette="hone"] {'):]
    block = block[:block.index("}")]
    return {"bg": re.search(r"--bg-base: (#[0-9a-f]{6})", block).group(1),
            "fg": re.search(r"--fg-text: (#[0-9a-f]{6})", block).group(1)}


# --------------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("binary", type=Path, help="the strop binary to capture")
    ap.add_argument("--paths", type=Path, required=True,
                    help="file list for the large tree, one path per line (.gz or plain)")
    ap.add_argument("--out", type=Path, default=SITE / "img", help="where the SVGs and frames.json go")
    ap.add_argument("--only", action="append", help="render only this scenario (repeatable)")
    ap.add_argument("--keep", action="store_true", help="keep the temporary fixtures and print their path")
    args = ap.parse_args(argv)
    binary = args.binary.resolve()
    for tool in ("tmux", "git"):
        if not shutil.which(tool):
            raise SystemExit(f"{tool} is required")
    version = run([str(binary), "--version"]).stdout.split()[-1]
    colours = hone_defaults()

    work = Path(tempfile.mkdtemp(prefix="strop-frames-"))
    manifest_path = args.out / "frames.json"
    frames = json.loads(manifest_path.read_text())["frames"] if args.only and manifest_path.exists() else {}
    try:
        facts = {"paths": build_tree(work / "tree", args.paths)}
        build_tally(work / "tally")
        for scenario in SCENARIOS:
            name = scenario["name"]
            if args.only and name not in args.only:
                continue
            for cand in scenario["candidates"]:
                tag = f"{name}-{cand['id']}"
                cwd = work / cand["project"]
                want = headless_frame(binary, cand["script"], cwd, cand["file"], work, tag)
                screen = "\n".join(want)
                if all(e.format(**facts) in screen for e in cand["expect"]):
                    break
                print(f"{tag}: not on this binary", file=sys.stderr)
            else:
                raise SystemExit(f"{name}: no candidate frame matched strop {version}")
            pane = Pane(binary, cwd, cand["file"], editor_env(work / f"home-pane-{tag}"), f"strop-frames-{os.getpid()}")
            try:
                pane.drive(cand["script"])
                pane.until(want)
                ansi = pane.ansi()
            finally:
                pane.close()
            alt = cand["alt"].format(**facts)
            svg = ansi2svg.render(ansi2svg.parse(ansi, COLS, ROWS), cols=COLS, font_size=14.0,
                                  default_fg=colours["fg"], default_bg=colours["bg"],
                                  title=f"strop {version}: {scenario['tab'].lower()}", desc=alt, pad=12.0)
            out = args.out / f"frame-{name}.svg"
            out.write_text(svg, encoding="utf-8")
            width, height = re.search(r'width="([\d.]+)" height="([\d.]+)"', svg).groups()
            frames[name] = {"file": f"img/{out.name}", "tab": scenario["tab"], "surface": cand["id"],
                            "width": round(float(width)), "height": round(float(height)),
                            "caption": cand["caption"].format(**facts), "alt": alt}
            print(f"wrote {out} ({tag}, {len(svg)} bytes)", file=sys.stderr)
        order = [s["name"] for s in SCENARIOS if s["name"] in frames]
        manifest = {"version": version, "cols": COLS, "rows": ROWS, "palette": "hone",
                    "frames": {n: frames[n] for n in order}}
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"wrote {manifest_path} (strop {version})", file=sys.stderr)
    finally:
        if args.keep:
            print(f"fixtures kept in {work}", file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
