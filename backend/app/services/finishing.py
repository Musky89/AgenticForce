"""Finishing Service — Layer 5 of the creative IP engine.

Applies text overlays, color grading, format adaptation, and logo placement
using Pillow for image processing. All outputs saved alongside originals in
generated_images/.
"""
import colorsys
import logging
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageStat

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)

FORMAT_SIZES = {
    "instagram_square": (1080, 1080),
    "instagram_portrait": (1080, 1350),
    "instagram_story": (1080, 1920),
    "facebook_link": (1200, 628),
    "profile_pic": (400, 400),
}


def _out_path(original: str, suffix: str) -> Path:
    stem = Path(original).stem
    return IMAGES_DIR / f"{stem}_{suffix}_{uuid.uuid4().hex[:8]}.png"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _luminance(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


def _pick_contrast_color(
    bg_rgb: tuple[int, int, int],
    brand_colors: list[str],
) -> tuple[int, int, int]:
    """Pick the brand color with best contrast against the background."""
    bg_lum = _luminance(*bg_rgb)
    best_color = (255, 255, 255) if bg_lum < 128 else (0, 0, 0)
    best_ratio = 0.0

    for hex_c in brand_colors:
        try:
            rgb = _hex_to_rgb(hex_c)
        except (ValueError, IndexError):
            continue
        c_lum = _luminance(*rgb)
        ratio = abs(bg_lum - c_lum)
        if ratio > best_ratio:
            best_ratio = ratio
            best_color = rgb

    return best_color


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except (OSError, IOError):
            return ImageFont.load_default()


def _sample_region_color(img: Image.Image, region: tuple[int, int, int, int]) -> tuple[int, int, int]:
    """Sample average color from a region of the image."""
    cropped = img.crop(region)
    stat = ImageStat.Stat(cropped.convert("RGB"))
    return tuple(int(c) for c in stat.mean[:3])


def apply_text_overlay(
    image_path: str,
    headline: str,
    body_text: str = "",
    cta: str = "",
    brand_bible: dict | None = None,
) -> str:
    """Apply text overlay with optimal placement and brand-aware contrast colors."""
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    brand_colors = []
    if brand_bible and brand_bible.get("color_palette"):
        palette = brand_bible["color_palette"]
        for key in ("primary", "secondary", "accent"):
            colors = palette.get(key, [])
            if isinstance(colors, list):
                brand_colors.extend(colors)
            elif isinstance(colors, str):
                brand_colors.append(colors)

    if not brand_colors:
        brand_colors = ["#FFFFFF", "#000000"]

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    margin_x = int(w * 0.08)
    text_y = int(h * 0.65)

    bg_region = (margin_x, text_y, w - margin_x, min(text_y + int(h * 0.3), h))
    bg_color = _sample_region_color(img, bg_region)
    text_color = _pick_contrast_color(bg_color, brand_colors)

    scrim_box = (0, text_y - int(h * 0.02), w, h)
    draw.rectangle(scrim_box, fill=(0, 0, 0, 120))

    headline_size = max(int(h * 0.06), 24)
    headline_font = _get_font(headline_size)
    draw.text((margin_x, text_y), headline, fill=(*text_color, 255), font=headline_font)

    current_y = text_y + headline_size + int(h * 0.02)

    if body_text:
        body_size = max(int(h * 0.03), 14)
        body_font = _get_font(body_size)
        max_width = w - 2 * margin_x
        words = body_text.split()
        lines = []
        line = ""
        for word in words:
            test = f"{line} {word}".strip()
            bbox = draw.textbbox((0, 0), test, font=body_font)
            if bbox[2] - bbox[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = test
        if line:
            lines.append(line)

        for ln in lines[:4]:
            draw.text((margin_x, current_y), ln, fill=(*text_color, 230), font=body_font)
            current_y += body_size + 4

    if cta:
        cta_size = max(int(h * 0.035), 16)
        cta_font = _get_font(cta_size)
        current_y += int(h * 0.02)
        cta_bbox = draw.textbbox((margin_x, current_y), cta, font=cta_font)
        padding = 12
        cta_bg = (
            cta_bbox[0] - padding,
            cta_bbox[1] - padding // 2,
            cta_bbox[2] + padding,
            cta_bbox[3] + padding // 2,
        )
        cta_bg_color = brand_colors[0] if brand_colors else "#FFFFFF"
        try:
            cta_bg_rgb = _hex_to_rgb(cta_bg_color)
        except (ValueError, IndexError):
            cta_bg_rgb = (255, 255, 255)
        draw.rounded_rectangle(cta_bg, radius=6, fill=(*cta_bg_rgb, 220))
        cta_text_color = _pick_contrast_color(cta_bg_rgb, ["#FFFFFF", "#000000"])
        draw.text((margin_x, current_y), cta, fill=(*cta_text_color, 255), font=cta_font)

    result = Image.alpha_composite(img, overlay).convert("RGB")
    out = _out_path(image_path, "text")
    result.save(str(out), "PNG")
    logger.info(f"Text overlay applied: {out.name}")
    return str(out)


def apply_color_grading(
    image_path: str,
    brand_palette: dict | None = None,
) -> str:
    """Adjust image color temperature/saturation to match brand palette warmth/coolness."""
    img = Image.open(image_path).convert("RGB")

    target_warmth = 0.0
    target_saturation = 1.0

    if brand_palette:
        all_colors = []
        for key in ("primary", "secondary", "accent"):
            colors = brand_palette.get(key, [])
            if isinstance(colors, list):
                all_colors.extend(colors)
            elif isinstance(colors, str):
                all_colors.append(colors)

        if all_colors:
            total_hue = 0.0
            total_sat = 0.0
            count = 0
            for hex_c in all_colors:
                try:
                    r, g, b = _hex_to_rgb(hex_c)
                    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                    total_hue += h
                    total_sat += s
                    count += 1
                except (ValueError, IndexError):
                    continue
            if count > 0:
                avg_hue = total_hue / count
                avg_sat = total_sat / count
                target_warmth = 0.1 if avg_hue < 0.17 or avg_hue > 0.8 else -0.05
                target_saturation = 0.8 + avg_sat * 0.4

    if abs(target_warmth) > 0.01:
        r, g, b = img.split()
        if target_warmth > 0:
            r = r.point(lambda x: min(255, int(x * (1 + target_warmth))))
            b = b.point(lambda x: max(0, int(x * (1 - target_warmth * 0.5))))
        else:
            b = b.point(lambda x: min(255, int(x * (1 + abs(target_warmth)))))
            r = r.point(lambda x: max(0, int(x * (1 - abs(target_warmth) * 0.5))))
        img = Image.merge("RGB", (r, g, b))

    if abs(target_saturation - 1.0) > 0.05:
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(target_saturation)

    out = _out_path(image_path, "graded")
    img.save(str(out), "PNG")
    logger.info(f"Color grading applied: {out.name}")
    return str(out)


def adapt_format(
    image_path: str,
    formats: list[str] | None = None,
) -> list[str]:
    """Smart crop image to multiple standard ad/social formats."""
    if not formats:
        formats = list(FORMAT_SIZES.keys())

    img = Image.open(image_path).convert("RGB")
    src_w, src_h = img.size
    results = []

    for fmt in formats:
        target = FORMAT_SIZES.get(fmt)
        if not target:
            try:
                parts = fmt.lower().split("x")
                target = (int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                logger.warning(f"Unknown format: {fmt}, skipping")
                continue

        tw, th = target
        target_ratio = tw / th
        src_ratio = src_w / src_h

        if src_ratio > target_ratio:
            new_w = int(src_h * target_ratio)
            left = (src_w - new_w) // 2
            crop_box = (left, 0, left + new_w, src_h)
        else:
            new_h = int(src_w / target_ratio)
            top = (src_h - new_h) // 2
            crop_box = (0, top, src_w, top + new_h)

        cropped = img.crop(crop_box)
        resized = cropped.resize((tw, th), Image.LANCZOS)

        fmt_label = fmt.replace("x", "x").replace(" ", "_")
        out = _out_path(image_path, fmt_label)
        resized.save(str(out), "PNG")
        results.append(str(out))
        logger.info(f"Adapted to {fmt} ({tw}x{th}): {out.name}")

    return results


def apply_logo(
    image_path: str,
    logo_path: str,
    position: str = "bottom_right",
    clear_space: int = 20,
) -> str:
    """Place logo on image with clear space rules and proportional scaling."""
    img = Image.open(image_path).convert("RGBA")
    logo = Image.open(logo_path).convert("RGBA")
    w, h = img.size

    max_logo_w = int(w * 0.15)
    max_logo_h = int(h * 0.08)
    logo_ratio = logo.width / logo.height

    if logo.width / max_logo_w > logo.height / max_logo_h:
        new_w = max_logo_w
        new_h = int(new_w / logo_ratio)
    else:
        new_h = max_logo_h
        new_w = int(new_h * logo_ratio)

    logo = logo.resize((new_w, new_h), Image.LANCZOS)

    positions = {
        "top_left": (clear_space, clear_space),
        "top_right": (w - new_w - clear_space, clear_space),
        "bottom_left": (clear_space, h - new_h - clear_space),
        "bottom_right": (w - new_w - clear_space, h - new_h - clear_space),
        "center": ((w - new_w) // 2, (h - new_h) // 2),
    }
    x, y = positions.get(position, positions["bottom_right"])

    pad = clear_space
    clear_region = Image.new("RGBA", (new_w + 2 * pad, new_h + 2 * pad), (255, 255, 255, 0))
    img.paste(clear_region, (x - pad, y - pad), clear_region)

    img.paste(logo, (x, y), logo)

    result = img.convert("RGB")
    out = _out_path(image_path, "logo")
    result.save(str(out), "PNG")
    logger.info(f"Logo applied at {position}: {out.name}")
    return str(out)


def batch_finish(
    image_path: str,
    brand_bible: dict | None = None,
    formats: list[str] | None = None,
    headline: str = "",
    body_text: str = "",
    cta: str = "",
    logo_path: str | None = None,
    logo_position: str = "bottom_right",
) -> dict:
    """Run full finishing pipeline on an image.

    Steps:
    1. Color grading based on brand palette
    2. Text overlay (if headline provided)
    3. Logo placement (if logo_path provided)
    4. Format adaptation to all requested sizes
    """
    results = {"source": image_path, "outputs": {}}
    current_path = image_path

    brand_palette = None
    if brand_bible and brand_bible.get("color_palette"):
        brand_palette = brand_bible["color_palette"]

    graded = apply_color_grading(current_path, brand_palette)
    results["outputs"]["color_graded"] = graded
    current_path = graded

    if headline:
        with_text = apply_text_overlay(current_path, headline, body_text, cta, brand_bible)
        results["outputs"]["text_overlay"] = with_text
        current_path = with_text

    if logo_path and Path(logo_path).exists():
        with_logo = apply_logo(current_path, logo_path, logo_position)
        results["outputs"]["logo"] = with_logo
        current_path = with_logo

    adapted = adapt_format(current_path, formats)
    results["outputs"]["formats"] = adapted

    logger.info(f"Batch finishing complete: {len(adapted)} format(s) produced")
    return results
