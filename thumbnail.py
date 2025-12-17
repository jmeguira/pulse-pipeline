from PIL import Image, ImageDraw, ImageFont

# --- Settings ---
width, height = 1280, 720  # final YouTube resolution

# Brand colors
primary_color = (255, 31, 143)  # Hot Magenta
secondary_color = (76, 126, 255)  # Electric Blue
accent_color = (255, 231, 76)  # Neon Yellow
stroke_color = primary_color
stroke_width_title = 10
stroke_width_subtitle = 6

title_text = "Top #25 Funny Shorts!"
subtitle_text = "From last week: Dec 8th–Dec 14th"

logo_path = "logo.png"
logo_size = (150, 150)

# Emoji PNGs
emoji_files = ["emoji_4.png", "emoji_2.png", "emoji_5.png"]
emoji_size = (300, 300)  # resize all emojis to this

# --- Create base image ---
img = Image.new("RGB", (width, height), color=(0, 0, 0))  # black background
draw = ImageDraw.Draw(img)

# --- Fonts ---
title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 140)
subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Impact.ttf", 70)

# --- Draw title at top, centered ---
bbox = draw.textbbox((0, 0), title_text, font=title_font, stroke_width=stroke_width_title)
title_w = bbox[2] - bbox[0]
draw.text(
    ((width - title_w) / 2, 30),
    title_text,
    font=title_font,
    fill=stroke_color,
    stroke_width=stroke_width_title,
    stroke_fill="white",
)

# --- Draw emojis centered horizontally ---
total_width = len(emoji_files) * emoji_size[0] + (len(emoji_files) - 1) * 40  # 40 px spacing
x_start = (width - total_width) / 2
y_center = height * 0.55 - emoji_size[1] / 2

for emoji_file in emoji_files:
    try:
        emoji_img = Image.open(emoji_file).convert("RGBA")
        emoji_img = emoji_img.resize(emoji_size, resample=Image.LANCZOS)
        img.paste(emoji_img, (int(x_start), int(y_center)), mask=emoji_img)
    except FileNotFoundError:
        print(f"⚠ Emoji file not found: {emoji_file}")
    x_start += emoji_size[0] + 40  # move to next position

# --- Draw subtitle at bottom, left-aligned ---
bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font, stroke_width=stroke_width_subtitle)
subtitle_h = bbox[3] - bbox[1]
draw.text(
    (30, height - subtitle_h - 30),
    subtitle_text,
    font=subtitle_font,
    fill=stroke_color,
    stroke_width=stroke_width_subtitle,
    stroke_fill="white",
)

# --- Add logo if exists ---
if logo_path:
    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo.thumbnail(logo_size)
        img.paste(logo, (width - logo_size[0] - 30, height - logo_size[1] - 30), mask=logo)
    except FileNotFoundError:
        print(f"⚠ Logo not found at {logo_path}, skipping.")

# --- Save thumbnail ---
img.save("thumbnail.png")
print("✅ Brand-colored thumbnail with centered PNG emojis saved as thumbnail.png")
