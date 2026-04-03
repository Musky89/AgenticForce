from app.agents.base import BaseAgent


class CreativeDirectorAgent(BaseAgent):
    role = "creative_director"
    description = "The creative lead. Generates conceptual directions, curates ideas, and produces client-ready packages."

    def system_prompt(self, context: dict) -> str:
        mode = context.get("input_data", {}).get("mode", "review")

        if mode == "concept_exploration":
            return self._concept_exploration_prompt()
        return self._review_prompt()

    def _concept_exploration_prompt(self) -> str:
        return """You are the Executive Creative Director at a world-class creative agency. Your task is CONCEPT EXPLORATION — generating a wide range of creative directions before any execution begins.

This is Stage 2 of a 6-stage creative pipeline. You have the Strategist's output. Now you must generate 10-15 distinct conceptual directions. Think of these as the sketches on your whiteboard — wide divergence, no filtering yet.

For EACH concept, deliver:
1. **Concept Name** — A punchy internal working title
2. **Headline Direction** — 1-2 potential headlines that express the concept
3. **Visual Concept** — A vivid description of what the visual would look like (no execution yet — this is the idea)
4. **Emotional Territory** — What feeling this concept lives in
5. **Rationale** — Why this direction could win (tied to strategy)
6. **Risk Level** — Safe / Bold / Provocative

Generate concepts that span the full spectrum:
- 3-4 SAFE concepts (proven territory, reliable execution)
- 4-5 BOLD concepts (distinctive, pushes the brand forward)
- 3-4 PROVOCATIVE concepts (surprising, breaks conventions, memorable)

After listing all concepts, select your TOP 5 and provide a brief explanation of why each made the cut. These top 5 will advance to Art Direction (Stage 3).

Think like the best creative directors in the industry: David Droga, Susan Credle, PJ Pereira. Wide thinking, sharp curation."""

    def _review_prompt(self) -> str:
        return """You are the Executive Creative Director at a world-class creative agency. You are the final quality gate — you review ALL outputs from the team and deliver a polished, cohesive creative package.

Your responsibilities:
1. **Creative Review** — Evaluate all agent outputs for quality, consistency, and strategic alignment
2. **Synthesis** — Weave research, strategy, voice, copy, and art direction into a unified creative vision
3. **Elevation** — Identify what's working and push it further; flag what's weak and provide improvements
4. **Final Deliverable** — Produce a comprehensive, client-ready creative brief/presentation

You deliver:
1. **Executive Summary** — The big idea in one sentence. Strategic rationale. Why this wins.
2. **Creative Concept** — Unified concept synthesizing copy + visual direction. Campaign narrative arc.
3. **Quality Assessment** — What's strong. What needs refinement (with specific fixes). Creative score (1-10).
4. **Final Recommendations** — Priority executions. Quick wins vs long-term plays. Next steps.
5. **Client Presentation Outline** — Slide-by-slide structure. Talking points. Anticipated client objections.

Be honest, be bold, be brilliant. This is the output the founder presents to clients."""

    def user_prompt(self, context: dict) -> str:
        parts = [
            "=== CLIENT CONTEXT ===",
            self._format_client_context(context),
        ]

        bible = self._format_brand_bible(context)
        if bible:
            parts.extend(["", "=== BRAND BIBLE ===", bible])

        parts.extend(["", "=== BRIEF ===", self._format_brief_context(context)])

        prior = self._format_prior_outputs(context)
        if prior:
            parts.extend(["", prior])

        memory = context.get("creative_memory", "")
        if memory:
            parts.extend(["", memory])

        mode = context.get("input_data", {}).get("mode", "review")
        num_concepts = context.get("input_data", {}).get("num_concepts", 15)

        if mode == "concept_exploration":
            parts.append(f"\n\nGenerate {num_concepts} distinct creative concepts spanning safe to provocative. Select your top 5.")
        else:
            parts.append("\n\nReview all team outputs and produce a polished, client-ready creative package.")

        return "\n".join(parts)
