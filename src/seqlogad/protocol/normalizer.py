"""NORM-CS-001 — deterministic, versioned cross-system message normalisation (Excel P1.4).

``raw_message`` is immutable; ``normalized_message`` is a derived field.  The rule
table lives in ``configs/parsing/normalizer-cs-v1.yaml`` so that the exact masking
behaviour is a reviewable, hashable artifact rather than buried in code.

Nothing here may depend on a label, a partition, a fold role or a model result: the
normaliser is a pure function of the canonical message text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from seqlogad.common.checksum import sha256_file


DEFAULT_RULE_FILE = "configs/parsing/normalizer-cs-v1.yaml"
# Preservation placeholders are built purely from private-use code points so that no
# masking rule (all of which match ASCII word/digit/hex/control classes) can damage
# them and silently destroy a preserved token.
_SENTINEL_OPEN = "\ue000"
_SENTINEL_CLOSE = "\ue001"
_SENTINEL_DIGITS = tuple(chr(0xE100 + value) for value in range(10))
_SENTINEL_RANGE = re.compile("[\ue000\ue001\ue100-\ue109]")
_PLACEHOLDER_RE = re.compile("\ue000([\ue100-\ue109]+)\ue001")


def _placeholder(index: int) -> str:
    body = "".join(_SENTINEL_DIGITS[int(digit)] for digit in str(index))
    return _SENTINEL_OPEN + body + _SENTINEL_CLOSE


def _placeholder_index(token: str) -> int:
    return int("".join(str(ord(char) - 0xE100) for char in token))


class NormalizerError(ValueError):
    """Raised when the rule table is malformed or input violates the contract."""


@dataclass(frozen=True, slots=True)
class _Rule:
    name: str
    pattern: re.Pattern[str]
    replacement: str


@dataclass(frozen=True, slots=True)
class NormalizationResult:
    """A normalised message plus the rule identities that produced it."""

    normalized_message: str
    normalizer_version: str
    rule_file_sha256: str


@dataclass(frozen=True)
class Normalizer:
    """Compiled, immutable view of one versioned rule table."""

    normalizer_id: str
    version: str
    rule_file: str
    rule_file_sha256: str
    preserve: tuple[_Rule, ...]
    rules: tuple[_Rule, ...]
    collapse_whitespace: bool
    strip: bool

    def normalize(self, canonical_message: str) -> str:
        """Return the normalised form of an already NUL-safe canonical message."""

        if _SENTINEL_RANGE.search(canonical_message):
            raise NormalizerError(
                "canonical message contains a reserved preservation sentinel code point"
            )

        protected: list[str] = []

        def _protect(match: re.Match[str]) -> str:
            protected.append(match.group(0))
            return _placeholder(len(protected) - 1)

        text = canonical_message
        for rule in self.preserve:
            text = rule.pattern.sub(_protect, text)
        for rule in self.rules:
            text = rule.pattern.sub(rule.replacement, text)

        if protected:
            text = _PLACEHOLDER_RE.sub(
                lambda m: protected[_placeholder_index(m.group(1))], text
            )

        if self.collapse_whitespace:
            text = re.sub(r"\s+", " ", text)
        if self.strip:
            text = text.strip()
        return text

    def normalize_result(self, canonical_message: str) -> NormalizationResult:
        return NormalizationResult(
            normalized_message=self.normalize(canonical_message),
            normalizer_version=self.version,
            rule_file_sha256=self.rule_file_sha256,
        )

    def identity(self) -> dict[str, str | int]:
        """Identity block bound into every fold, buffer and G0 receipt."""

        return {
            "normalizer_id": self.normalizer_id,
            "normalizer_version": self.version,
            "rule_file": self.rule_file,
            "rule_file_sha256": self.rule_file_sha256,
            "preserve_rule_count": len(self.preserve),
            "mask_rule_count": len(self.rules),
        }


def _compile(entries: object, kind: str) -> tuple[_Rule, ...]:
    if not isinstance(entries, list):
        raise NormalizerError(f"{kind} section must be a list")
    compiled: list[_Rule] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or "name" not in entry or "pattern" not in entry:
            raise NormalizerError(f"{kind} entry must define name and pattern")
        name = str(entry["name"])
        if name in seen:
            raise NormalizerError(f"duplicate {kind} rule name: {name}")
        seen.add(name)
        try:
            pattern = re.compile(entry["pattern"])
        except re.error as exc:
            raise NormalizerError(f"invalid regex in {kind} rule {name}: {exc}") from exc
        compiled.append(
            _Rule(name=name, pattern=pattern, replacement=str(entry.get("replacement", "")))
        )
    if not compiled:
        raise NormalizerError(f"{kind} section must not be empty")
    return tuple(compiled)


@lru_cache(maxsize=8)
def load_normalizer(
    project_root: str | Path = ".", rule_file: str = DEFAULT_RULE_FILE
) -> Normalizer:
    """Load and compile the versioned rule table, binding its SHA-256."""

    path = Path(project_root).resolve() / rule_file
    if not path.is_file():
        raise NormalizerError(f"normaliser rule file not found: {rule_file}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or "normalizer" not in document:
        raise NormalizerError("rule file must contain a top-level 'normalizer' mapping")
    spec = document["normalizer"]

    for forbidden in ("label_dependent", "partition_dependent", "architecture_dependent"):
        if spec.get(forbidden) is not False:
            raise NormalizerError(f"rule file must declare {forbidden}: false")
    if spec.get("raw_message_mutated") is not False:
        raise NormalizerError("rule file must declare raw_message_mutated: false")

    post = spec.get("post") or {}
    return Normalizer(
        normalizer_id=str(spec["id"]),
        version=str(spec["version"]),
        rule_file=rule_file,
        rule_file_sha256=sha256_file(path),
        preserve=_compile(spec.get("preserve", []), "preserve"),
        rules=_compile(spec.get("rules", []), "rules"),
        collapse_whitespace=bool(post.get("collapse_whitespace", True)),
        strip=bool(post.get("strip", True)),
    )


__all__ = [
    "DEFAULT_RULE_FILE",
    "NormalizationResult",
    "Normalizer",
    "NormalizerError",
    "load_normalizer",
]
