# AgenticForce

An AI-powered creative agency platform that produces categorically better output than anyone using LLMs or image generators directly. The IP isn't the AI — it's the five-layer system wrapped around the AI that compounds over time.

## The Five Layers of Creative IP

### Layer 1: Brand-Specific LoRA Models
Per-client fine-tuned LoRA models trained on the brand's visual assets via **Flux** (fal.ai). The model internalizes the brand's visual DNA — color tendencies, composition patterns, photographic style — at the model weight level. Output is inherently on-brand without prompt engineering.

### Layer 2: 6-Stage Creative Pipeline
Not one-shot generation. A structured pipeline that mirrors how the best agencies work:

| Stage | Agent | What Happens |
|-------|-------|-------------|
| 1. Strategic Framing | Strategist | Audience insight, key message, emotional response, differentiation |
| 2. Concept Exploration | Creative Director | 10-20 conceptual directions, top 5 curated for execution |
| 3. Art Direction | Art Director | Detailed visual briefs + Flux image generation prompts |
| 4. Visual Generation | Designer + Flux | Image generation with client LoRA, multiple variants per concept |
| 5. Refinement | Copywriter | Channel-specific copy, headlines, CTAs, text overlay specs |
| 6. Quality Scoring | Auto-Scorer | Multi-dimensional evaluation against Brand Bible |

### Layer 3: Automated Brand Quality Scoring
Every image scored against the Brand Bible before it reaches the founder's review queue:
- **Color Compliance** — dominant colors vs brand palette
- **Composition Quality** — rule-of-thirds, focal point, negative space
- **Brand Consistency** — visual style alignment with brand DNA
- **Technical Quality** — artifacts, resolution, hands/faces
- **Strategic Alignment** — does it communicate the message?
- **Platform Readiness** — correct dimensions, safe zones

Only passing work enters the review queue. The founder never sees bad work.

### Layer 4: Creative Memory
Performance-linked memory that compounds with every engagement:
- **Prompt Library** — effective prompts with quality scores
- **Style Insights** — what visual approaches work for this client
- **Performance Data** — engagement/conversion linked to creative attributes
- **Cross-Client Patterns** — industry-level creative intelligence
- Auto-captured on every approval, feeding back into future generations

### Layer 5: Brand Bible Engine
Structured brand context (30+ fields) injected into every agent automatically:
- Positioning, USP, mission, vision, values
- Color palette (hex codes), typography, photography style
- Tone of voice, voice attributes (is/is not), vocabulary
- Composition rules, visual do's/don'ts
- Channel-specific guidelines, competitive landscape

## Service Blueprint System

Modular client configuration with 6 templates:

| Template | Use Case |
|----------|----------|
| **Social-First** | Fashion, lifestyle — high visual volume, LoRA, 40-60 assets/month |
| **Performance** | DTC e-commerce — paid media, A/B testing, ROAS-driven |
| **Content-Led** | B2B SaaS — blog/SEO, thought leadership, LinkedIn |
| **New Brand** | Full identity build — strategy, visual identity, Brand Bible, launch |
| **Traditional Media** | Print, OOH — CMYK, publication templates, media booking |
| **Full Service** | Everything — all agents, all channels, quarterly strategy |

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- OpenAI API key (GPT-4o for agents + quality scoring)
- fal.ai API key (Flux image generation + LoRA)

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add OPENAI_API_KEY and FAL_KEY
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Workflow

1. **Onboard Client** — Create client → Build Brand Bible (positioning, visual identity, verbal identity) → Choose Service Blueprint template → Register/train LoRA model
2. **Create Project** — Write brief with objective, audience, messages, emotional response, mandatory inclusions
3. **Run 6-Stage Pipeline** — Strategy → Concepts → Art Direction → Visual Generation → Copy → Quality Scoring
4. **Review Queue** — Only quality-scored passing work is presented. Approve, reject, or provide feedback.
5. **Creative Memory** — Every approval auto-captures learnings. System gets better with every engagement.

## Tech Stack

**Backend:** FastAPI, SQLAlchemy (async), SQLite, OpenAI (GPT-4o), fal.ai (Flux + LoRA), Pydantic v2

**Frontend:** Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, Lucide Icons
