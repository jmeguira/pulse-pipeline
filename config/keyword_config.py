from domain.keyword_config import KeywordConfig

KEYWORD_CONFIG: dict[str, KeywordConfig] = {
    "cat": KeywordConfig(
        thumbnail_emojis=["😺", "🐾", "😻"],
        title_emojis=["😺"],
        description_emojis=["🐾"],
        tags=["cat", "cats", "cat shorts", "funny cats", "cute animals"],
        hashtags=["#cat", "#cats", "#catshorts", "#funnycats", "#cute"],
    ),
    "funny": KeywordConfig(
        thumbnail_emojis=["😂", "🤣", "😹"],
        title_emojis=["😂"],
        description_emojis=["🤣"],
        tags=["funny", "funny videos", "try not to laugh", "comedy"],
        hashtags=["#funny", "#comedy", "#lol", "#viral"],
    ),
    "gaming": KeywordConfig(
        thumbnail_emojis=["🎮", "🔥", "💥"],
        title_emojis=["🎮"],
        description_emojis=["🔥"],
        tags=["gaming", "gaming shorts", "funny gaming", "viral gaming"],
        hashtags=["#gaming", "#gamingshorts", "#gamer", "#viral"],
    ),
    "dogs": KeywordConfig(
        thumbnail_emojis=["🐶", "🐾", "❤️"],
        title_emojis=["🐶"],
        description_emojis=["🐾"],
        tags=["dogs", "dog shorts", "funny dogs", "cute dogs"],
        hashtags=["#dogs", "#dogshorts", "#funnypets", "#cute"],
    ),
    "fails": KeywordConfig(
        thumbnail_emojis=["💥", "😬", "🤣"],
        title_emojis=["💥"],
        description_emojis=["🤣"],
        tags=["fails", "funny fails", "epic fails", "fail compilation"],
        hashtags=["#fails", "#epicfail", "#funnyfails"],
    ),
    "satisfying": KeywordConfig(
        thumbnail_emojis=["✨", "🧼", "👌"],
        title_emojis=["✨"],
        description_emojis=["👌"],
        tags=["satisfying", "oddly satisfying", "relaxing videos"],
        hashtags=["#satisfying", "#oddlysatisfying", "#relaxing"],
    ),
    "memes": KeywordConfig(
        thumbnail_emojis=["🧠", "🤣", "🔥"],
        title_emojis=["🤣"],
        description_emojis=["🔥"],
        tags=["memes", "viral memes", "internet memes"],
        hashtags=["#memes", "#viral", "#internetmemes"],
    ),
}
