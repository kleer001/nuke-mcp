"""Version detection and tool gating for Nuke variants and versions."""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class NukeVersion:
    major: int
    minor: int
    patch: str  # e.g., "v1", "v5"
    variant: str  # "Nuke", "NukeX", "NukeStudio"

    @property
    def is_nukex(self) -> bool:
        return self.variant in ("NukeX", "NukeStudio")

    @property
    def is_studio(self) -> bool:
        return self.variant == "NukeStudio"

    def at_least(self, major: int, minor: int = 0) -> bool:
        return (self.major, self.minor) >= (major, minor)

    def __str__(self) -> str:
        return f"{self.variant} {self.major}.{self.minor}{self.patch}"


def parse_version(handshake: dict) -> NukeVersion:
    """Parse a Nuke version from the addon handshake data.

    Expected handshake format:
        {"nuke_version": "17.0v1", "variant": "NukeX", ...}
    """
    version_str = handshake.get("nuke_version", "0.0v0")
    variant = handshake.get("variant", "Nuke")

    match = re.match(r"(\d+)\.(\d+)(v\d+)?", version_str)
    if not match:
        log.warning("Could not parse Nuke version string: %s", version_str)
        return NukeVersion(0, 0, "v0", variant)

    return NukeVersion(
        major=int(match.group(1)),
        minor=int(match.group(2)),
        patch=match.group(3) or "v0",
        variant=variant,
    )
