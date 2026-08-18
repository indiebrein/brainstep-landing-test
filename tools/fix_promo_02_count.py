"""Обновляет цифру упражнений на карточке 02_exercise_catalog.png.

Запускать на чистом оригинале (скопировать заново из
C:\\project\\site\\assets\\promo\\02_exercise_catalog.png), иначе стирание
не сможет убрать уже перерисованную предыдущую цифру.

Использует тот же приём стирания старого текста, что и в
generate_promo_1_0_3.py (erase_template_text), и перерисовывает
эйбрау/заголовок/подзаголовок теми же шрифтами и координатами.
"""

from pathlib import Path

from PIL import Image, ImageDraw

import numpy as np

from generate_promo_1_0_3 import PROMO_DIR, FONT_BOLD, FONT_REGULAR, font, centered_text

PATH = PROMO_DIR / "02_exercise_catalog.png"


def erase_bands(image: Image.Image) -> Image.Image:
    """Stronger inpaint than the shared helper: wider threshold, more
    dilation and enough diffusion passes to fully clear a bold 66px band."""
    pixels = np.asarray(image.convert("RGB"), dtype=np.float32)
    luminance = pixels.mean(axis=2)
    mask = np.zeros(luminance.shape, dtype=bool)

    for top, bottom in ((55, 118), (118, 320), (320, 390)):
        mask[top : bottom + 1] = luminance[top : bottom + 1] < 220

    for _ in range(4):
        expanded = mask.copy()
        expanded[1:] |= mask[:-1]
        expanded[:-1] |= mask[1:]
        expanded[:, 1:] |= mask[:, :-1]
        expanded[:, :-1] |= mask[:, 1:]
        mask = expanded

    mask3 = mask[..., None]
    restored = pixels.copy()
    restored[mask] = np.nan
    for _ in range(600):
        padded = np.pad(restored, ((1, 1), (1, 1), (0, 0)), mode="edge")
        neigh = np.stack(
            [padded[:-2, 1:-1], padded[2:, 1:-1], padded[1:-1, :-2], padded[1:-1, 2:]],
            axis=0,
        )
        with np.errstate(invalid="ignore"):
            avg = np.nanmean(neigh, axis=0)
        still_nan = np.isnan(restored)
        fill = np.where(still_nan & ~np.isnan(avg), avg, restored)
        restored = np.where(mask3, fill, restored)

    restored = np.nan_to_num(restored, nan=225.0)
    alpha = np.asarray(image.getchannel("A"), dtype=np.uint8)[..., None]
    rgba = np.concatenate((np.clip(restored, 0, 255).astype(np.uint8), alpha), axis=2)
    return Image.fromarray(rgba, mode="RGBA")


def main() -> None:
    image = Image.open(PATH).convert("RGBA")
    image = erase_bands(image)

    draw = ImageDraw.Draw(image)
    ink = (10, 31, 39)
    muted = (48, 78, 84)
    accent = (37, 96, 102)

    centered_text(draw, 79, "BRAINSTEP · КАТАЛОГ", font(FONT_BOLD, 25), accent)
    centered_text(draw, 140, "19 УПРАЖНЕНИЙ\nДЛЯ РАЗНЫХ НАВЫКОВ", font(FONT_BOLD, 66), ink, spacing=11)
    centered_text(draw, 337, "Выбирайте то, что хотите развивать", font(FONT_REGULAR, 30), muted)

    image.convert("RGB").save(PATH, quality=95)
    print("updated", PATH)


if __name__ == "__main__":
    main()
