#!/usr/bin/env python3
"""Install this skill into the AI coding tools on this machine.

  python3 scripts/install.py                 every tool detected in your home directory
  python3 scripts/install.py claude cursor   specific tools
  python3 scripts/install.py --copy claude   copy instead of symlinking
  python3 scripts/install.py project [DIR]   wire it into one project instead of your home directory

Symlinking is the default so `git pull` in this repository updates every tool at once. Windows
usually forbids symlinks without Developer Mode, so there the installer falls back to copying and
says so.

Never deletes anything it did not create: an existing real directory at a target path is reported,
not removed.
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

NAME = "skill-pandaai-factor-online"
SRC = Path(__file__).resolve().parent.parent
IGNORE = shutil.ignore_patterns(".git", "__pycache__", "*.pyc")


def volatile(path: Path) -> bool:
    """Symlinks out of a temp directory break silently when the system clears it."""
    temp = Path(tempfile.gettempdir()).resolve()
    candidates = [temp, Path("/tmp"), Path("/private/tmp")]
    for base in candidates:
        try:
            path.relative_to(base)
            return True
        except ValueError:
            continue
    return False


def place(dest: Path, copy: bool, force: bool) -> bool:
    """Put the skill at dest. Returns True on success."""
    if dest.is_symlink():
        dest.unlink()
    elif dest.exists():
        if not force:
            sys.stdout.flush()
            print(f"  skipped {dest}\n"
                  f"          a real directory is already there; remove it or pass --force",
                  file=sys.stderr)
            return False
        shutil.rmtree(dest) if dest.is_dir() else dest.unlink()

    dest.parent.mkdir(parents=True, exist_ok=True)
    if not copy:
        try:
            dest.symlink_to(SRC, target_is_directory=True)
            print(f"  {dest}")
            return True
        except OSError:
            print("  note: symlinks are not permitted here, copying instead"
                  " (re-run after `git pull` to update)")
    shutil.copytree(SRC, dest, ignore=IGNORE)
    print(f"  {dest}")
    return True


def point(file: Path) -> bool:
    """Append a pointer to an instruction file, once."""
    file.parent.mkdir(parents=True, exist_ok=True)
    if file.exists() and NAME in file.read_text(encoding="utf-8"):
        print(f"  {file} (already referenced)")
        return True
    with file.open("a", encoding="utf-8") as fh:
        fh.write(f"\n## {NAME}\n\nFor PandaAI factor work, read {SRC}/SKILL.md first.\n"
                 f"做 PandaAI 因子时，先读 {SRC}/SKILL.md。\n")
    print(f"  {file}")
    return True


HOME_TARGETS = {
    "claude": ("Claude Code", lambda: Path.home() / ".claude"),
    "cursor": ("Cursor", lambda: Path.home() / ".cursor"),
    "codex": ("Codex", lambda: Path.home() / ".codex"),
    "gemini": ("Gemini CLI", lambda: Path.home() / ".gemini"),
}


def install(target: str, copy: bool, force: bool) -> bool:
    label, root = HOME_TARGETS[target]
    print(f"{label}:")
    base = root()
    if target == "codex":
        return point(base / "AGENTS.md")
    if target == "gemini":
        return point(base / "GEMINI.md")
    return place(base / "skills" / NAME, copy, force)


def install_project(directory: Path, copy: bool, force: bool) -> bool:
    print(f"Project {directory}:")
    ok = place(directory / ".cursor" / "skills" / NAME, copy, force)
    ok &= place(directory / ".claude" / "skills" / NAME, copy, force)
    # Codex, Kimi Code, opencode, Aider and others read AGENTS.md from the project root.
    ok &= point(directory / "AGENTS.md")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(__doc__.splitlines()[2:7]),
    )
    ap.add_argument("targets", nargs="*", metavar="TARGET",
                    help="claude, cursor, codex, gemini, all, or: project [DIR]")
    ap.add_argument("--copy", action="store_true", help="copy instead of symlinking")
    ap.add_argument("--force", action="store_true",
                    help="replace a real directory at a target path, or install from a temp one")
    args = ap.parse_args()

    # The warning against cloning into a temp directory lives inside the repository, which you have
    # to clone before you can read it. Refusing here is the only place it arrives in time.
    if volatile(SRC) and not args.force:
        print(f"This repository sits in {SRC}, which the system clears periodically.", file=sys.stderr)
        print("Installs are symlinks, so they would break there and take the skill out of every",
              file=sys.stderr)
        print("tool at once, silently. Move the repository somewhere permanent and run this again:",
              file=sys.stderr)
        print(f"\n  mv {SRC} ~/{SRC.name}\n  cd ~/{SRC.name} && {sys.executable} scripts/install.py\n",
              file=sys.stderr)
        print("Pass --force to install from here anyway.", file=sys.stderr)
        return 1

    if args.targets and args.targets[0] == "project":
        directory = Path(args.targets[1]).expanduser().resolve() if len(args.targets) > 1 else Path.cwd()
        ok = install_project(directory, args.copy, args.force)
    else:
        targets = [t for t in args.targets if t != "all"]
        if not targets:
            targets = [t for t in HOME_TARGETS if HOME_TARGETS[t][1]().is_dir()]
            missing = [HOME_TARGETS[t][0] for t in HOME_TARGETS if t not in targets]
            if missing:
                print(f"Not installed on this machine, so skipped: {', '.join(missing)}.")
                print("Install one later and re-run this to add it.\n")
            if not targets:
                print("No supported tool directories found in your home directory.", file=sys.stderr)
                print("Pass a target explicitly, or use: python3 scripts/install.py project [DIR]",
                      file=sys.stderr)
                return 1
        unknown = [t for t in targets if t not in HOME_TARGETS]
        if unknown:
            print(f"unknown target: {', '.join(unknown)}", file=sys.stderr)
            return 1
        ok = all([install(t, args.copy, args.force) for t in targets])

    print(f"\nNext: {sys.executable} {SRC / 'scripts' / 'bootstrap.py'}"
          "  (read-only, costs no compute credits)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
