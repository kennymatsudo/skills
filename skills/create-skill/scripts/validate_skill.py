#!/usr/bin/env python3
"""Check skill directories for the defects that silently break or rot a skill.

Usage: validate_skill.py [--codex-policy-generated] <skill-dir> [<skill-dir> ...]
       validate_skill.py [--codex-policy-generated] --all <skills-root>

Errors (exit 1): frontmatter that won't parse, a missing or malformed name or
description, a name that differs from its directory, a relative file reference
that doesn't exist, a "**name** skill" reference no installed skill answers to,
a bare <placeholder> outside code that rendered markdown would hide, and a skill that is user-invoked in some harnesses but not others. Claude Code
and Pi read `disable-model-invocation: true` from the frontmatter; Codex ignores
it and reads `policy.allow_implicit_invocation: false` from `agents/openai.yaml`.
Pass --codex-policy-generated when an installer writes that file from the
frontmatter, which skips the check.
Warnings (exit 0): a body over 500 lines.
"""

import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("validate_skill.py needs PyYAML: pip install pyyaml")

NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024
MAX_BODY_LINES = 500

# Subdirectories a skill conventionally bundles. A backticked path starting
# with one of these is a claim that the file ships with the skill.
BUNDLED_DIRS = ("references/", "scripts/", "assets/", "playbooks/", "examples/")

MARKDOWN_LINK = re.compile(r"\]\(([^)\s]+)\)")
BACKTICKED_PATH = re.compile(r"`([^`\s<>*]+)`")
SKILL_MENTION = re.compile(r"\*\*([a-z0-9][a-z0-9-]*)\*\*( principle)? skill\b")
FENCED_BLOCK = re.compile(r"^[ \t]*```.*?^[ \t]*```", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
BARE_PLACEHOLDER = re.compile(r"</?([a-z][a-z0-9-]*)[^>\n]*>")
HTML_TAGS = {"br", "details", "summary", "kbd", "sub", "sup", "img", "a", "p", "b", "i", "em", "strong", "code", "pre"}


def installed_skill_names(extra_roots):
    roots = list(extra_roots)
    for env, default in (
        ("CLAUDE_CONFIG_DIR", "~/.claude"),
        ("CODEX_HOME", "~/.codex"),
        ("PI_CODING_AGENT_DIR", "~/.pi/agent"),
    ):
        roots.append(Path(os.environ.get(env, default)).expanduser() / "skills")
    roots.append(Path("~/.agents/skills").expanduser())
    names = set()
    for root in roots:
        if root.is_dir():
            names.update(p.name for p in root.iterdir() if (p / "SKILL.md").exists())
    return names


def split_frontmatter(text):
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    return text[4:end], text[end + 5 :]


def check_frontmatter(skill_dir, raw, errors):
    """Return the parsed frontmatter, or None when it can't be read."""
    if raw is None:
        errors.append("no frontmatter: SKILL.md must open with a --- block")
        return None
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        first_line = str(exc).splitlines()[0]
        errors.append(f"frontmatter is not valid YAML ({first_line}); quote a description containing ': '")
        return None
    if not isinstance(meta, dict):
        errors.append("frontmatter must be a mapping of keys to values")
        return None

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("missing name")
    else:
        if not NAME_PATTERN.match(name) or len(name) > MAX_NAME:
            errors.append(f"name {name!r} must be kebab-case and at most {MAX_NAME} characters")
        if name != skill_dir.name:
            errors.append(f"name {name!r} differs from its directory {skill_dir.name!r}")

    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("missing description")
    elif len(description) > MAX_DESCRIPTION:
        errors.append(f"description is {len(description)} characters, over the {MAX_DESCRIPTION} limit")
    return meta


def check_invocation(skill_dir, meta, errors):
    """Codex keeps its own invocation switch, so a user-invoked skill needs both."""
    user_invoked = meta.get("disable-model-invocation") is True
    codex_file = skill_dir / "agents" / "openai.yaml"
    codex_blocks = False
    if codex_file.exists():
        try:
            codex = yaml.safe_load(codex_file.read_text()) or {}
        except yaml.YAMLError:
            errors.append("agents/openai.yaml is not valid YAML")
            return
        if not isinstance(codex, dict) or set(codex) - {"interface", "policy", "dependencies"}:
            errors.append("agents/openai.yaml may only hold interface, policy, and dependencies")
            return
        codex_blocks = (codex.get("policy") or {}).get("allow_implicit_invocation") is False
    if user_invoked and not codex_blocks:
        errors.append(
            "disable-model-invocation is true but Codex will still auto-invoke it; "
            "add agents/openai.yaml with policy.allow_implicit_invocation: false"
        )
    elif codex_blocks and not user_invoked:
        errors.append(
            "agents/openai.yaml blocks implicit invocation but the frontmatter doesn't; "
            "set disable-model-invocation: true so Claude Code and Pi match"
        )


def check_references(skill_dir, file_dir, body, known_skills, errors):
    """Markdown links resolve from the file that holds them; bundled paths from the skill root."""
    prose = FENCED_BLOCK.sub("", body)
    for target in MARKDOWN_LINK.findall(prose):
        if re.match(r"^[a-z]+:|^#|^/|^~", target):
            continue
        path = target.split("#", 1)[0]
        looks_like_file = "/" in path or "." in path
        if looks_like_file and not (file_dir / path).exists():
            errors.append(f"link target missing: {target}")
    for token in BACKTICKED_PATH.findall(prose):
        if token.startswith(BUNDLED_DIRS) and not (skill_dir / token).exists():
            errors.append(f"referenced file missing: {token}")
    for match in BARE_PLACEHOLDER.finditer(INLINE_CODE.sub("", prose)):
        if match.group(1) not in HTML_TAGS:
            errors.append(f"bare placeholder {match.group(0)} is hidden when rendered; put it in backticks")
    for name, principle in SKILL_MENTION.findall(prose):
        candidates = {name, f"principle-{name}"} if principle else {name}
        if not candidates & known_skills:
            errors.append(f"no installed or sibling skill named {name!r}")


def validate(skill_dir, known_skills, codex_policy_generated):
    errors, warnings = [], []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"no SKILL.md in {skill_dir}"], warnings
    raw, body = split_frontmatter(skill_md.read_text())
    meta = check_frontmatter(skill_dir, raw, errors)
    if meta is not None and not codex_policy_generated:
        check_invocation(skill_dir, meta, errors)
    check_references(skill_dir, skill_dir, body, known_skills, errors)
    for extra in skill_dir.rglob("*.md"):
        if extra != skill_md:
            check_references(skill_dir, extra.parent, extra.read_text(), known_skills, errors)
    if body.count("\n") > MAX_BODY_LINES:
        warnings.append(f"body is over {MAX_BODY_LINES} lines; move branch-only material into references/")
    return errors, warnings


def main(argv):
    codex_policy_generated = "--codex-policy-generated" in argv
    argv = [a for a in argv if a != "--codex-policy-generated"]
    if len(argv) == 2 and argv[0] == "--all":
        root = Path(argv[1])
        dirs = sorted(p for p in root.iterdir() if (p / "SKILL.md").exists())
    elif argv and "--all" not in argv:
        dirs = [Path(a) for a in argv]
    else:
        sys.exit(__doc__.strip())

    sibling_roots = {d.resolve().parent for d in dirs}
    known = installed_skill_names(sibling_roots)
    failed = False
    for skill_dir in dirs:
        errors, warnings = validate(skill_dir.resolve(), known, codex_policy_generated)
        for message in errors:
            print(f"ERROR {skill_dir.name}: {message}")
        for message in warnings:
            print(f"WARN  {skill_dir.name}: {message}")
        failed = failed or bool(errors)
    if not failed:
        print(f"OK: {len(dirs)} skill(s) passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
