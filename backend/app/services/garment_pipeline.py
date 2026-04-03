"""Virtual Garment Pipeline — for fashion/textiles clients.

Handles fabric-on-model compositing:
1. Fabric ingestion: process swatches into tileable textures
2. Model generation: AI models using brand LoRA
3. Garment compositing: drape fabric onto models (via specialized image gen prompts)
4. Post-processing: color correction, lighting harmonization
5. Output: production-ready social assets

Since true virtual try-on models (IDM-VTON etc) require specialized GPU infrastructure,
this pipeline uses a practical approach: detailed Flux prompts that incorporate the
fabric description + brand LoRA to generate models wearing garments that match
the fabric's visual characteristics.
"""
import logging
import json
from pathlib import Path
from PIL import Image
from openai import AsyncOpenAI

from app.config import get_settings
from app.services.image_gen import generate_image

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"


async def analyze_fabric(image_path: str) -> dict:
    """Analyze a fabric swatch image using GPT-4o Vision to extract visual properties."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    filepath = Path(image_path)
    if not filepath.exists():
        filepath = IMAGES_DIR / image_path
    if not filepath.exists():
        raise FileNotFoundError(f"Fabric image not found: {image_path}")

    import base64
    image_data = base64.b64encode(filepath.read_bytes()).decode("utf-8")

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """Analyze this fabric swatch and extract detailed visual properties for image generation.
Return ONLY a JSON object:
{
  "fabric_type": "silk/cotton/linen/denim/chiffon/velvet/knit/etc",
  "pattern": "solid/striped/floral/geometric/abstract/plaid/etc",
  "pattern_description": "detailed description of the pattern",
  "primary_colors": ["#hex1", "#hex2"],
  "secondary_colors": ["#hex3"],
  "texture": "smooth/rough/ribbed/woven/knitted/sheer/etc",
  "weight": "lightweight/medium/heavy",
  "draping": "flowing/structured/stiff/clingy",
  "sheen": "matte/satin/glossy/metallic",
  "visual_prompt_fragment": "a detailed text fragment describing this fabric for image generation"
}""",
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this fabric swatch:"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}", "detail": "high"}},
                ],
            },
        ],
        temperature=0.2,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse fabric analysis: {raw[:200]}")
        return {"fabric_type": "unknown", "visual_prompt_fragment": "fabric material", "primary_colors": []}


async def generate_garment_concepts(
    fabric_analysis: dict,
    brand_context: dict,
    num_concepts: int = 4,
    garment_types: list[str] | None = None,
) -> list[dict]:
    """Generate art direction concepts for garments using the analyzed fabric."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    if garment_types is None:
        garment_types = ["flowing dress", "tailored blazer", "draped wrap top", "wide-leg trousers"]

    fabric_desc = fabric_analysis.get("visual_prompt_fragment", "fabric")
    fabric_type = fabric_analysis.get("fabric_type", "fabric")
    colors = ", ".join(fabric_analysis.get("primary_colors", []))
    draping = fabric_analysis.get("draping", "natural")
    sheen = fabric_analysis.get("sheen", "matte")

    brand_name = brand_context.get("client", {}).get("name", "the brand")
    photo_style = brand_context.get("brand_bible", {}).get("photography_style", "editorial fashion photography")

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": f"""You are a fashion art director creating image generation prompts for a virtual photoshoot.

The fabric is: {fabric_desc}
Fabric type: {fabric_type}, colors: {colors}, draping: {draping}, sheen: {sheen}
Brand photography style: {photo_style}

For each garment type, create a detailed Flux image generation prompt that produces a photorealistic fashion image of a model wearing a garment made from this specific fabric. The prompt must capture the fabric's texture, color, draping behavior, and sheen accurately.

Return ONLY a JSON array of objects:
[{{
  "garment_type": "...",
  "prompt": "detailed prompt for image generation",
  "aspect_ratio": "3:4",
  "label": "descriptive label",
  "styling_notes": "brief styling direction"
}}]""",
            },
            {
                "role": "user",
                "content": f"Create {num_concepts} garment concepts for these garment types: {', '.join(garment_types[:num_concepts])}",
            },
        ],
        temperature=0.6,
        max_tokens=2500,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse garment concepts: {raw[:200]}")
        return [{"garment_type": g, "prompt": f"Fashion model wearing a {g} made of {fabric_desc}, {photo_style}", "aspect_ratio": "3:4", "label": g.title()} for g in garment_types[:num_concepts]]


async def generate_garment_images(
    concepts: list[dict],
    lora_url: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    """Generate images for each garment concept."""
    ASPECT_MAP = {"1:1": (1024, 1024), "3:4": (1024, 1344), "4:3": (1344, 1024), "9:16": (1024, 1792), "16:9": (1792, 1024)}

    all_results = []
    for concept in concepts:
        ar = concept.get("aspect_ratio", "3:4")
        dims = ASPECT_MAP.get(ar, (1024, 1344))
        try:
            images = await generate_image(
                prompt=concept["prompt"],
                width=dims[0],
                height=dims[1],
                num_images=2,
                lora_url=lora_url,
                provider=provider,
            )
            for img in images:
                img["label"] = concept.get("label", concept.get("garment_type", "Garment"))
                img["garment_type"] = concept.get("garment_type")
                img["styling_notes"] = concept.get("styling_notes", "")
            all_results.extend(images)
        except Exception as e:
            logger.error(f"Garment image generation failed for {concept.get('garment_type')}: {e}")
            all_results.append({"error": str(e), "label": concept.get("label", "Failed"), "prompt": concept["prompt"]})

    return all_results


async def run_garment_pipeline(
    fabric_image_path: str,
    brand_context: dict,
    lora_url: str | None = None,
    garment_types: list[str] | None = None,
    num_concepts: int = 4,
    provider: str | None = None,
) -> dict:
    """Full garment pipeline: analyze fabric → generate concepts → generate images."""
    logger.info(f"Starting garment pipeline for fabric: {fabric_image_path}")

    fabric_analysis = await analyze_fabric(fabric_image_path)
    logger.info(f"Fabric analyzed: {fabric_analysis.get('fabric_type')} / {fabric_analysis.get('pattern')}")

    concepts = await generate_garment_concepts(fabric_analysis, brand_context, num_concepts, garment_types)
    logger.info(f"Generated {len(concepts)} garment concepts")

    images = await generate_garment_images(concepts, lora_url, provider)
    successful = [img for img in images if "error" not in img]
    logger.info(f"Generated {len(successful)} garment images ({len(images) - len(successful)} failed)")

    return {
        "fabric_analysis": fabric_analysis,
        "concepts": concepts,
        "images": images,
        "successful_count": len(successful),
        "failed_count": len(images) - len(successful),
    }
