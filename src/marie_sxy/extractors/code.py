"""Detect programming language from file extension, shebang, and content hints."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Extension → language name
_EXT_MAP: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".jsx": "JavaScript/React",
    ".rs": "Rust",
    ".go": "Go",
    ".java": "Java",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".hpp": "C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".r": "R",
    ".rmd": "R Markdown",
    ".lua": "Lua",
    ".pl": "Perl",
    ".sh": "Shell",
    ".bash": "Bash",
    ".zsh": "Zsh",
    ".fish": "Fish",
    ".ps1": "PowerShell",
    ".scala": "Scala",
    ".clj": "Clojure",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".ml": "OCaml",
    ".mli": "OCaml",
    ".dart": "Dart",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".tf": "Terraform",
    ".sql": "SQL",
    ".html": "HTML",
    ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
    ".md": "Markdown",
    ".ipynb": "Jupyter Notebook",
    ".dockerfile": "Dockerfile",
}

# Shebang prefix → language name
_SHEBANG_MAP: list[tuple[str, str]] = [
    ("python", "Python"),
    ("node", "JavaScript"),
    ("ruby", "Ruby"),
    ("perl", "Perl"),
    ("php", "PHP"),
    ("bash", "Bash"),
    ("zsh", "Zsh"),
    ("sh", "Shell"),
    ("fish", "Fish"),
    ("deno", "TypeScript"),
    ("lua", "Lua"),
    ("rscript", "R"),
]


def extract_code_language(path: Path) -> str:
    """Return a human-readable language name or empty string if not a code file.

    Checks extension first; falls back to shebang on the first line.
    """
    suffix = path.suffix.lower()

    # Special case: Dockerfile (no extension or named exactly "Dockerfile")
    if path.name in {"Dockerfile", "Containerfile"}:
        return "Dockerfile"

    if suffix in _EXT_MAP:
        return _EXT_MAP[suffix]

    # Try shebang for extensionless / ambiguous files
    try:
        with path.open("rb") as fh:
            first_line = fh.readline(256).decode("utf-8", errors="replace").strip()
        if first_line.startswith("#!"):
            shebang = first_line[2:].lower()
            for keyword, lang in _SHEBANG_MAP:
                if keyword in shebang:
                    return lang
    except OSError:
        pass

    return ""
