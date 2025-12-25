import json
from pathlib import Path
from typing import Optional

from domain.runtime_flags import RuntimeFlags


def load_flags(path: Optional[Path]) -> RuntimeFlags:
    if not path or not path.exists():
        return RuntimeFlags()

    data = json.loads(path.read_text())
    if not isinstance(data, dict):
        raise ValueError("flags.json must contain a JSON object")

    return RuntimeFlags.from_mapping(data)
