from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROMO_DIR = ROOT / "assets" / "promo"
SCREEN_DIR = Path(r"C:\project\screen\1.0.3")
ICON_PATH = Path(r"C:\project\icon\icon_no_background.png")
NUMBER_SEARCH_TEMPLATE = PROMO_DIR / "05_find_pair.png"

WIDTH = 1080
HEIGHT = 1920
FONT_REGULAR = r"C:\Windows\Fonts\arial.ttf"
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"
FONT_NARROW_BOLD = r"C:\Windows\Fonts\ARIALNB.TTF"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    spacing: int = 8,
) -> int:
    box = draw.multiline_textbbox((0, 0), text, font=text_font, spacing=spacing, align="center")
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    draw.multiline_text(
        ((WIDTH - text_width) / 2, y - box[1]),
        text,
        font=text_font,
        fill=fill,
        spacing=spacing,
        align="center",
    )
    return y + text_height


def draw_background(
    base: tuple[int, int, int],
    circles: tuple[tuple[tuple[int, int, int], tuple[int, int, int, int]], ...],
) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), base)
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for color, bounds in circles:
        draw.ellipse(bounds, fill=(*color, 82))
    return Image.alpha_composite(image.convert("RGBA"), overlay)


def add_phone(image: Image.Image, screenshot_path: Path) -> None:
    phone_x = 154
    phone_y = 505
    phone_width = 772
    phone_height = 1640
    radius = 86

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (phone_x + 15, phone_y + 18, phone_x + phone_width + 15, phone_y + phone_height + 18),
        radius=radius,
        fill=(35, 66, 70, 52),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    image.alpha_composite(shadow)

    frame = Image.new("RGBA", image.size, (0, 0, 0, 0))
    frame_draw = ImageDraw.Draw(frame)
    frame_draw.rounded_rectangle(
        (phone_x, phone_y, phone_x + phone_width, phone_y + phone_height),
        radius=radius,
        fill=(249, 251, 249, 255),
        outline=(220, 226, 224, 255),
        width=3,
    )
    image.alpha_composite(frame)

    screenshot = Image.open(screenshot_path).convert("RGBA")
    app_background = screenshot.getpixel((540, 150))

    # Remove only the black exterior around the source phone silhouette.
    # Keep the status indicators on the right, as in the 1.0.2 promo set.
    top = screenshot.crop((0, 0, screenshot.width, 220))
    for seed in ((0, 0), (top.width - 1, 0)):
        ImageDraw.floodfill(top, seed, app_background, thresh=32)
    screenshot.paste(top, (0, 0))

    clean_draw = ImageDraw.Draw(screenshot)
    clean_draw.rectangle((0, 0, 700, 140), fill=app_background)
    clean_draw.rectangle((900, 0, screenshot.width, 50), fill=app_background)
    clean_draw.rectangle((1000, 0, screenshot.width, 140), fill=app_background)

    inner_x = phone_x + 20
    inner_y = phone_y + 20
    inner_width = phone_width - 40
    scaled_height = round(screenshot.height * inner_width / screenshot.width)
    screenshot = screenshot.resize((inner_width, scaled_height), Image.Resampling.LANCZOS)

    mask = Image.new("L", screenshot.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, screenshot.width, screenshot.height + radius), radius=68, fill=255)
    image.paste(screenshot, (inner_x, inner_y), mask)


def create_slide(
    output_name: str,
    screenshot_name: str,
    base: tuple[int, int, int],
    circles: tuple[tuple[tuple[int, int, int], tuple[int, int, int, int]], ...],
    eyebrow: str,
    headline: str,
    subtitle: str,
    skill_chip: str,
    accent: tuple[int, int, int],
) -> None:
    image = draw_background(base, circles)
    draw = ImageDraw.Draw(image)
    ink = (10, 31, 39)
    muted = (48, 78, 84)

    centered_text(draw, 79, eyebrow, font(FONT_BOLD, 25), accent)
    centered_text(draw, 140, headline, font(FONT_BOLD, 66), ink, spacing=11)
    centered_text(draw, 337, subtitle, font(FONT_REGULAR, 30), muted)

    chip_width = 510
    chip_height = 68
    chip_x = (WIDTH - chip_width) // 2
    chip_y = 404
    draw.rounded_rectangle(
        (chip_x + 6, chip_y + 10, chip_x + chip_width + 6, chip_y + chip_height + 10),
        radius=34,
        fill=(41, 73, 78, 35),
    )
    draw.rounded_rectangle(
        (chip_x, chip_y, chip_x + chip_width, chip_y + chip_height),
        radius=34,
        fill=(250, 250, 250, 248),
        outline=(*accent, 100),
        width=2,
    )
    chip_font = font(FONT_BOLD, 27)
    chip_box = draw.textbbox((0, 0), skill_chip, font=chip_font)
    draw.text(
        ((WIDTH - (chip_box[2] - chip_box[0])) / 2, chip_y + 18 - chip_box[1]),
        skill_chip,
        font=chip_font,
        fill=accent,
    )

    add_phone(image, SCREEN_DIR / screenshot_name)
    image.convert("RGB").save(PROMO_DIR / output_name, quality=95)


def erase_template_text(image: Image.Image) -> Image.Image:
    """Remove only the old glyphs while retaining the circular background."""
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
    luminance = pixels.mean(axis=2)
    mask = np.zeros(luminance.shape, dtype=bool)

    for top, bottom in ((62, 112), (120, 315), (326, 383)):
        mask[top : bottom + 1] = luminance[top : bottom + 1] < 185

    # Include antialiased edges without turning the entire headline area into
    # a flat interpolated band.
    for _ in range(2):
        expanded = mask.copy()
        expanded[1:] |= mask[:-1]
        expanded[:-1] |= mask[1:]
        expanded[:, 1:] |= mask[:, :-1]
        expanded[:, :-1] |= mask[:, 1:]
        mask = expanded

    restored = pixels.copy()
    restored[mask] = (223, 232, 228)
    for _ in range(120):
        padded = np.pad(restored, ((1, 1), (1, 1), (0, 0)), mode="edge")
        average = (
            padded[:-2, 1:-1]
            + padded[2:, 1:-1]
            + padded[1:-1, :-2]
            + padded[1:-1, 2:]
        ) * 0.25
        restored[mask] = average[mask]

    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)[..., None]
    rgba = np.concatenate((np.clip(restored, 0, 255).astype(np.uint8), alpha), axis=2)
    return Image.fromarray(rgba, mode="RGBA")


def create_number_search_slide() -> None:
    # Reuse the original 1.0.2 slide rather than redrawing its phone. This
    # preserves its silhouette, shadow, corner radii and status icons exactly.
    image = Image.open(NUMBER_SEARCH_TEMPLATE).convert("RGBA")
    image = erase_template_text(image)

    draw = ImageDraw.Draw(image)
    ink = (10, 31, 39)
    muted = (48, 78, 84)
    accent = (42, 109, 116)
    centered_text(draw, 80, "BRAINSTEP · ПОИСК ЧИСЛА", font(FONT_BOLD, 25), accent)
    headline_font = font(FONT_BOLD, 74)
    centered_text(draw, 132, "НАЙДИТЕ ЧИСЛО", headline_font, ink)
    centered_text(draw, 230, "СРЕДИ ПОМЕХ", headline_font, ink)
    centered_text(draw, 340, "Поле растёт, а числа становятся всё хитрее", font(FONT_REGULAR, 30), muted)

    screenshot = Image.open(SCREEN_DIR / "Screenshot_20260806_225605.png").convert("RGBA")
    content = screenshot.crop((0, 140, screenshot.width, screenshot.height))
    content_width = 732
    content_height = round(content.height * content_width / content.width)
    content = content.resize((content_width, content_height), Image.Resampling.LANCZOS)
    image.alpha_composite(content, (174, 627))
    image.convert("RGB").save(PROMO_DIR / "09_number_search.png", dpi=(144, 144), quality=95)


def replace_future_logo() -> None:
    path = PROMO_DIR / "10_future_updates.png"
    image = Image.open(path).convert("RGBA")
    draw = ImageDraw.Draw(image)
    card_color = image.getpixel((540, 560))
    draw.rectangle((320, 580, 760, 1018), fill=card_color)

    logo = Image.open(ICON_PATH).convert("RGBA")
    logo.thumbnail((382, 382), Image.Resampling.LANCZOS)
    x = (WIDTH - logo.width) // 2
    y = 610
    image.alpha_composite(logo, (x, y))
    image.convert("RGB").save(path, quality=95)


def main() -> None:
    create_number_search_slide()
    replace_future_logo()


if __name__ == "__main__":
    main()
