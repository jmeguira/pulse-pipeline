from moviepy import (
    CompositeVideoClip,
    ColorClip,
    TextClip,
)


def get_outro_clip(output_width=1920, output_height=1080, duration=3.0) -> CompositeVideoClip:
    bg = ColorClip(size=(output_width, output_height), color=(0, 0, 0), duration=duration)

    top_text = TextClip(
        text="THANKS FOR WATCHING!",
        font_size=int(output_height * 0.15),
        size=(output_width, output_height),
        color="white",
        font="Impact",
        vertical_align="top",
        duration=duration,
    )

    bottom_text = TextClip(
        text="SUBSCRIBE FOR MORE",
        font_size=int(output_height * 0.15),
        size=(output_width, output_height),
        color="white",
        font="Impact",
        duration=duration,
    )

    return CompositeVideoClip([bg, top_text, bottom_text])
