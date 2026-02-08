from openai import AsyncOpenAI
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL
)

async def generate_templates(keyword: str, videos: list):
    """
    Generates 10 reusable title templates based on top performing videos.
    videos: List of dicts with 'title' and 'views_num'.
    """
    if not videos:
        return []

    # Sort validation: ensure we have titles
    video_titles = [v['title'] for v in videos if v.get('title')]
    
    prompt = f"""
    Analyze these top-performing YouTube video titles for the keyword "{keyword}":
    {json.dumps(video_titles, ensure_ascii=False)}

    Create 10 reusable "winning" title templates that would work well for this niche in Indonesia (Bahasa Indonesia).
    Each template should be a generic structure (using brackets like [Topic]) derived from the patterns in the successful videos.
    Provide 2 concrete examples for each template.

    Return ONLY a JSON array of objects with keys: "template_text", "example_1", "example_2".
    Do not include markdown formatting or explanations.
    """

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a YouTube expert specializing in the Indonesian market."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        # Clean potential markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        templates = json.loads(content)
        return templates
    except Exception as e:
        logger.error(f"Error generating templates: {e}")
        return []
