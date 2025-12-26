from dataclasses import dataclass
from typing import Any, Mapping

from domain.log_level import LogLevel


@dataclass(frozen=True)
class RuntimeFlags:
    log_level: LogLevel = LogLevel.NORMAL
    dry_run: bool = False
    strict: bool = False
    save_intermediates: bool = False
    profile: bool = False

    @staticmethod
    def from_mapping(d: Mapping[str, Any]) -> "RuntimeFlags":
        return RuntimeFlags(
            log_level=LogLevel(d.get("log_level", LogLevel.NORMAL)),
            dry_run=bool(d.get("dry_run", False)),
            strict=bool(d.get("strict", False)),
            save_intermediates=bool(d.get("save_intermediates", False)),
            profile=bool(d.get("profile", False)),
        )

    def __repr__(self) -> str:
        return (
            "RuntimeFlags("
            f"log_level={self.log_level.name}, "
            f"dry_run={self.dry_run}, "
            f"strict={self.strict}, "
            f"save_intermediates={self.save_intermediates}, "
            f"profile={self.profile}"
            ")"
        )
