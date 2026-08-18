"""Сборка изображений лендинга: WebP-варианты, иконки и обложка для соцсетей.

Запуск из корня сайта:

    python tools/build_assets.py

Скрипт не удаляет исходные PNG — они остаются как fallback в <picture>.
"""

from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")

# Ширины в CSS-пикселях, умноженные на 2 для экранов высокой плотности.
PHONE_WIDTHS = (360, 720)
PROMO_WIDTHS = (320, 640)
ICON_WIDTHS = (96, 192)

WEBP = {"format": "WEBP", "quality": 82, "method": 6}

FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"
FONT_SEMIBOLD = r"C:\Windows\Fonts\seguisb.ttf"


def resized_webp(source: str, widths: tuple[int, ...]) -> list[str]:
    """Сохраняет WebP каждой ширины рядом с исходником и возвращает пути."""
    created = []
    with Image.open(source) as image:
        image = image.convert("RGBA")
        base, _ = os.path.splitext(source)
        for width in widths:
            height = round(image.height * width / image.width)
            variant = image.resize((width, height), Image.LANCZOS)
            target = f"{base}-{width}.webp"
            variant.save(target, **WEBP)
            created.append(target)
    return created


def build_phone_shots() -> None:
    for name in ("home.png", "progress.png"):
        source = os.path.join(ASSETS, "screenshots", name)
        if os.path.exists(source):
            report(resized_webp(source, PHONE_WIDTHS))


def build_promo_shots() -> None:
    promo = os.path.join(ASSETS, "promo")
    for name in sorted(os.listdir(promo)):
        if name.endswith(".png"):
            report(resized_webp(os.path.join(promo, name), PROMO_WIDTHS))


def build_icons() -> None:
    source = os.path.join(ASSETS, "app-icon.png")
    report(resized_webp(source, ICON_WIDTHS))
    with Image.open(source) as image:
        image = image.convert("RGBA")
        for width, target in ((96, "app-icon-96.png"), (180, "apple-touch-icon.png")):
            height = round(image.height * width / image.width)
            image.resize((width, height), Image.LANCZOS).save(
                os.path.join(ASSETS, target), optimize=True
            )
            report([os.path.join(ASSETS, target)])


def rounded_shadow(canvas: Image.Image, box: tuple[int, int, int, int], radius: int) -> None:
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(box, radius=radius, fill=(31, 61, 65, 38))
    canvas.alpha_composite(shadow)


def build_social_cover() -> None:
    """Обложка 1200×630 для og:image — вертикальный скриншот для неё не подходит."""
    width, height = 1200, 630
    cover = Image.new("RGBA", (width, height), "#f7faf7")
    draw = ImageDraw.Draw(cover)

    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((-180, 180, 420, 780), fill=(220, 239, 237, 210))
    glow_draw.ellipse((820, -220, 1400, 360), fill=(236, 226, 247, 190))
    cover.alpha_composite(glow)

    icon_box = (96, 150, 96 + 200, 150 + 200)
    rounded_shadow(cover, (icon_box[0] + 6, icon_box[1] + 18, icon_box[2] + 6, icon_box[3] + 18), 54)
    with Image.open(os.path.join(ASSETS, "app-icon.png")) as icon:
        icon = icon.convert("RGBA").resize((200, 200), Image.LANCZOS)
        mask = Image.new("L", (200, 200), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, 199, 199), radius=54, fill=255)
        cover.paste(icon, (icon_box[0], icon_box[1]), mask)

    title = ImageFont.truetype(FONT_BOLD, 96)
    lead = ImageFont.truetype(FONT_REGULAR, 36)
    chip = ImageFont.truetype(FONT_SEMIBOLD, 27)

    draw.text((344, 168), "BrainStep", font=title, fill="#172124")
    draw.text(
        (348, 288),
        "Короткие тренировки внимания, памяти,\nреакции, логики и счёта",
        font=lead,
        fill="#4c5a5e",
        spacing=14,
    )

    x = 348
    for label in ("Без регистрации", "Без рекламы", "Работает офлайн"):
        text_width = draw.textlength(label, font=chip)
        draw.rounded_rectangle(
            (x, 428, x + text_width + 44, 484), radius=28, fill="#ffffff", outline="#d6e4e0"
        )
        draw.text((x + 22, 442), label, font=chip, fill="#315f67")
        x += text_width + 62

    cover.convert("RGB").save(os.path.join(ASSETS, "social-cover.png"), optimize=True)
    report([os.path.join(ASSETS, "social-cover.png")])


def report(paths: list[str]) -> None:
    for path in paths:
        size = os.path.getsize(path) / 1024
        print(f"{os.path.relpath(path, ROOT):<52} {size:7.0f} KB")


if __name__ == "__main__":
    build_phone_shots()
    build_promo_shots()
    build_icons()
    build_social_cover()
