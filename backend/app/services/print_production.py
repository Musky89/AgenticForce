"""Print Production Pipeline — handles CMYK conversion, bleed marks, publication templates.

For traditional media clients: broadsheet ads, magazine placements, OOH, POS, brochures.
Output is print-ready PDF with correct color space, resolution, and bleed.
"""
import logging
from pathlib import Path
from PIL import Image, ImageCms
from reportlab.lib.pagesizes import A4, A3, letter
from reportlab.lib.units import mm, inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"
EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"
EXPORTS_DIR.mkdir(exist_ok=True)

PUBLICATION_TEMPLATES = {
    "broadsheet_quarter": {"width_mm": 130, "height_mm": 170, "bleed_mm": 3, "dpi": 300},
    "broadsheet_half": {"width_mm": 265, "height_mm": 170, "bleed_mm": 3, "dpi": 300},
    "broadsheet_full": {"width_mm": 265, "height_mm": 370, "bleed_mm": 3, "dpi": 300},
    "magazine_full": {"width_mm": 210, "height_mm": 297, "bleed_mm": 5, "dpi": 300},
    "magazine_half_h": {"width_mm": 210, "height_mm": 148, "bleed_mm": 5, "dpi": 300},
    "magazine_half_v": {"width_mm": 105, "height_mm": 297, "bleed_mm": 5, "dpi": 300},
    "ooh_6sheet": {"width_mm": 1200, "height_mm": 1800, "bleed_mm": 10, "dpi": 150},
    "ooh_48sheet": {"width_mm": 6096, "height_mm": 3048, "bleed_mm": 25, "dpi": 72},
    "pos_a5": {"width_mm": 148, "height_mm": 210, "bleed_mm": 3, "dpi": 300},
    "pos_a4": {"width_mm": 210, "height_mm": 297, "bleed_mm": 3, "dpi": 300},
    "pos_a3": {"width_mm": 297, "height_mm": 420, "bleed_mm": 3, "dpi": 300},
    "business_card": {"width_mm": 90, "height_mm": 55, "bleed_mm": 3, "dpi": 300},
    "dl_flyer": {"width_mm": 99, "height_mm": 210, "bleed_mm": 3, "dpi": 300},
}

SAFE_ZONE_MM = 5  # Text safety margin inside trim


def get_templates() -> dict:
    return PUBLICATION_TEMPLATES


def convert_to_cmyk(image_path: str) -> str:
    """Convert an RGB image to CMYK color space for print."""
    filepath = Path(image_path)
    if not filepath.exists():
        filepath = IMAGES_DIR / image_path

    img = Image.open(filepath)
    if img.mode == "CMYK":
        return str(filepath)

    if img.mode != "RGB":
        img = img.convert("RGB")

    # Use a simple RGB->CMYK conversion (production would use ICC profiles)
    cmyk = img.convert("CMYK")

    output_name = filepath.stem + "_cmyk" + filepath.suffix
    output_path = filepath.parent / output_name
    cmyk.save(str(output_path))

    logger.info(f"Converted to CMYK: {output_name}")
    return str(output_path)


def ensure_resolution(image_path: str, min_dpi: int = 300, target_width_mm: float = 210) -> str:
    """Check and upscale image to meet minimum print DPI requirements."""
    filepath = Path(image_path)
    if not filepath.exists():
        filepath = IMAGES_DIR / image_path

    img = Image.open(filepath)
    target_width_px = int(target_width_mm / 25.4 * min_dpi)

    if img.width >= target_width_px:
        return str(filepath)

    scale = target_width_px / img.width
    new_size = (int(img.width * scale), int(img.height * scale))
    img_resized = img.resize(new_size, Image.LANCZOS)

    output_name = filepath.stem + f"_{min_dpi}dpi" + filepath.suffix
    output_path = filepath.parent / output_name
    img_resized.save(str(output_path), quality=95)

    logger.info(f"Upscaled to {min_dpi}dpi: {output_name}")
    return str(output_path)


def add_bleed_marks(image_path: str, bleed_mm: float = 3, dpi: int = 300) -> str:
    """Add bleed area and crop marks to an image."""
    filepath = Path(image_path)
    if not filepath.exists():
        filepath = IMAGES_DIR / image_path

    img = Image.open(filepath)
    bleed_px = int(bleed_mm / 25.4 * dpi)
    mark_len = int(5 / 25.4 * dpi)

    new_w = img.width + 2 * bleed_px
    new_h = img.height + 2 * bleed_px
    canvas_img = Image.new(img.mode, (new_w, new_h), (255, 255, 255) if img.mode == "RGB" else (0, 0, 0, 0))
    canvas_img.paste(img, (bleed_px, bleed_px))

    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas_img)
    mark_color = (0, 0, 0) if img.mode == "RGB" else (0, 0, 0, 255)

    corners = [
        (bleed_px, bleed_px),
        (bleed_px + img.width, bleed_px),
        (bleed_px, bleed_px + img.height),
        (bleed_px + img.width, bleed_px + img.height),
    ]
    for cx, cy in corners:
        draw.line([(cx - mark_len, cy), (cx - 2, cy)], fill=mark_color, width=1)
        draw.line([(cx + 2, cy), (cx + mark_len, cy)], fill=mark_color, width=1)
        draw.line([(cx, cy - mark_len), (cx, cy - 2)], fill=mark_color, width=1)
        draw.line([(cx, cy + 2), (cx, cy + mark_len)], fill=mark_color, width=1)

    output_name = filepath.stem + "_bleed" + filepath.suffix
    output_path = filepath.parent / output_name
    canvas_img.save(str(output_path), quality=95)

    logger.info(f"Added bleed marks: {output_name}")
    return str(output_path)


def prepare_for_print(
    image_path: str,
    template_name: str,
) -> dict:
    """Full print preparation pipeline: resize → CMYK → bleed marks."""
    template = PUBLICATION_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(PUBLICATION_TEMPLATES.keys())}")

    result = ensure_resolution(image_path, template["dpi"], template["width_mm"])
    cmyk_path = convert_to_cmyk(result)
    final_path = add_bleed_marks(cmyk_path, template["bleed_mm"], template["dpi"])

    return {
        "output_path": final_path,
        "template": template_name,
        "specs": template,
        "color_space": "CMYK",
        "bleed_mm": template["bleed_mm"],
        "safe_zone_mm": SAFE_ZONE_MM,
    }


def generate_print_spec_sheet(
    project_name: str,
    template_name: str,
    additional_notes: str = "",
) -> str:
    """Generate a print specification PDF for the production team."""
    template = PUBLICATION_TEMPLATES.get(template_name, PUBLICATION_TEMPLATES["magazine_full"])
    filename = f"print_specs_{project_name.replace(' ', '_').lower()}_{template_name}.pdf"
    filepath = EXPORTS_DIR / filename

    c = canvas.Canvas(str(filepath), pagesize=A4)
    w, h = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(30, h - 50, "Print Production Specifications")

    c.setFont("Helvetica", 12)
    y = h - 90
    specs = [
        ("Project", project_name),
        ("Template", template_name.replace("_", " ").title()),
        ("Trim Size", f"{template['width_mm']}mm x {template['height_mm']}mm"),
        ("Bleed", f"{template['bleed_mm']}mm all sides"),
        ("Safe Zone", f"{SAFE_ZONE_MM}mm inside trim"),
        ("Resolution", f"{template['dpi']} DPI minimum"),
        ("Color Space", "CMYK (no RGB, no spot colors unless specified)"),
        ("File Format", "PDF/X-1a or high-res TIFF"),
        ("Total Size with Bleed", f"{template['width_mm'] + 2*template['bleed_mm']}mm x {template['height_mm'] + 2*template['bleed_mm']}mm"),
    ]

    for label, value in specs:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(30, y, f"{label}:")
        c.setFont("Helvetica", 11)
        c.drawString(180, y, value)
        y -= 22

    if additional_notes:
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(30, y, "Additional Notes:")
        y -= 18
        c.setFont("Helvetica", 10)
        for line in additional_notes.split("\n"):
            c.drawString(30, y, line.strip())
            y -= 15

    c.save()
    logger.info(f"Generated print spec sheet: {filename}")
    return filename
