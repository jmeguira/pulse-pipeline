from dataclasses import dataclass, field
from typing import List


@dataclass
class KeywordConfig:
    query_include: List[str] = field(default_factory=list)
    query_exclude: List[str] = field(default_factory=list)
    thumbnail_emojis: List[str] = field(default_factory=list)
    title_emojis: List[str] = field(default_factory=list)
    description_emojis: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
