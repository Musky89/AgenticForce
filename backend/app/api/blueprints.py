from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import ServiceBlueprint, Client, BlueprintTemplate
from app.schemas.schemas import ServiceBlueprintCreate, ServiceBlueprintUpdate, ServiceBlueprintOut

router = APIRouter(prefix="/blueprints", tags=["service-blueprints"])

TEMPLATE_DEFAULTS = {
    BlueprintTemplate.SOCIAL_FIRST: {
        "active_services": [
            {"service": "social_content", "cadence": "weekly", "volume": "10-15 assets/week"},
            {"service": "community_management", "cadence": "daily"},
            {"service": "paid_social", "cadence": "monthly"},
        ],
        "quality_thresholds": {"color_compliance": 7, "brand_consistency": 8, "composition_quality": 7, "composite_minimum": 7},
        "approval_rules": {"founder_review": ["hero_visuals", "campaign_launches"], "auto_publish": ["routine_posts"]},
    },
    BlueprintTemplate.PERFORMANCE: {
        "active_services": [
            {"service": "paid_media", "cadence": "continuous"},
            {"service": "ad_creative", "cadence": "bi-weekly"},
            {"service": "landing_pages", "cadence": "monthly"},
            {"service": "email_sequences", "cadence": "monthly"},
        ],
        "quality_thresholds": {"strategic_alignment": 8, "composite_minimum": 7},
    },
    BlueprintTemplate.CONTENT_LED: {
        "active_services": [
            {"service": "blog_seo", "cadence": "weekly"},
            {"service": "thought_leadership", "cadence": "bi-weekly"},
            {"service": "email_nurture", "cadence": "weekly"},
            {"service": "linkedin_content", "cadence": "daily"},
        ],
    },
    BlueprintTemplate.NEW_BRAND: {
        "active_services": [
            {"service": "brand_strategy", "cadence": "project"},
            {"service": "visual_identity", "cadence": "project"},
            {"service": "brand_bible", "cadence": "project"},
            {"service": "launch_campaign", "cadence": "project"},
        ],
        "approval_rules": {"founder_review": ["all"]},
    },
    BlueprintTemplate.TRADITIONAL_MEDIA: {
        "active_services": [
            {"service": "print_ads", "cadence": "monthly"},
            {"service": "ooh_concepts", "cadence": "quarterly"},
            {"service": "press_releases", "cadence": "monthly"},
        ],
        "special_pipelines": [{"type": "print_production", "specs": {"color_space": "CMYK", "resolution": 300}}],
    },
    BlueprintTemplate.FULL_SERVICE: {
        "active_services": [
            {"service": "strategy", "cadence": "quarterly"},
            {"service": "creative", "cadence": "weekly"},
            {"service": "social_content", "cadence": "daily"},
            {"service": "paid_media", "cadence": "continuous"},
            {"service": "email", "cadence": "weekly"},
            {"service": "seo", "cadence": "monthly"},
            {"service": "reporting", "cadence": "monthly"},
        ],
        "quality_thresholds": {"color_compliance": 8, "brand_consistency": 8, "composition_quality": 8, "strategic_alignment": 8, "composite_minimum": 8},
        "approval_rules": {"founder_review": ["campaign_launches", "brand_evolution"], "auto_publish": ["routine_content"]},
    },
}


@router.get("/templates")
async def list_templates():
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title(), "defaults": TEMPLATE_DEFAULTS.get(t, {})}
        for t in BlueprintTemplate
    ]


@router.post("", response_model=ServiceBlueprintOut, status_code=201)
async def create_blueprint(payload: ServiceBlueprintCreate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(404, "Client not found")

    existing = await db.execute(select(ServiceBlueprint).where(ServiceBlueprint.client_id == payload.client_id))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Blueprint already exists. Use PATCH to update.")

    data = payload.model_dump()
    defaults = TEMPLATE_DEFAULTS.get(payload.template_type, {})
    for key, default_val in defaults.items():
        if data.get(key) is None:
            data[key] = default_val

    bp = ServiceBlueprint(**data)
    db.add(bp)
    await db.flush()
    await db.refresh(bp)
    return bp


@router.get("/client/{client_id}", response_model=ServiceBlueprintOut)
async def get_by_client(client_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ServiceBlueprint).where(ServiceBlueprint.client_id == client_id))
    bp = result.scalar_one_or_none()
    if not bp:
        raise HTTPException(404, "No blueprint found")
    return bp


@router.patch("/{bp_id}", response_model=ServiceBlueprintOut)
async def update_blueprint(bp_id: str, payload: ServiceBlueprintUpdate, db: AsyncSession = Depends(get_db)):
    bp = await db.get(ServiceBlueprint, bp_id)
    if not bp:
        raise HTTPException(404, "Blueprint not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(bp, k, v)
    await db.flush()
    await db.refresh(bp)
    return bp
