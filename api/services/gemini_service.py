import os
import json
import re
import google.generativeai as genai
from datetime import datetime

class GeminiService:
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        else:
            self.model = None

    def _extract_json(self, text: str):
        """Robustly extract JSON array from response text."""
        # Try to find JSON inside markdown code blocks first
        code_block = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if code_block:
            return json.loads(code_block.group(1))
        # Fallback: find raw array
        start = text.find("[")
        end = text.rfind("]") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        return []

    async def generate_video_ideas(self, channel_context: str = ""):
        if not self.model:
            return [{
                "title": "API Key Missing",
                "description": "Please set GEMINI_API_KEY in your .env file.",
                "suggested_month_year": datetime.now().strftime("%B %Y"),
                "short_hook": "",
                "short_script": "",
                "trending_keyword": "",
                "trending_url": ""
            }]
        
        current_date = datetime.now().strftime("%B %Y")
        prompt = f"""
        Act as a YouTube Content Strategist. Based on the current date ({current_date}),
        suggest 10 viral video ideas for a YouTube channel.
        Channel context: {channel_context}

        For each idea, also provide:
        - A short-form (YouTube Shorts) hook — the opening 1-2 sentences to grab attention
        - A brief short script outline (2-3 bullet points of what the Short would cover)
        - A trending search keyword related to this topic
        - A YouTube search URL for that keyword (format: https://www.youtube.com/results?search_query=KEYWORD+2026)

        Return ONLY a valid JSON array with these exact fields (no extra text):
        [
          {{
            "title": "Video title",
            "description": "Full video description",
            "suggested_month_year": "{current_date}",
            "short_hook": "Opening hook for the Short version",
            "short_script": "• Point 1\\n• Point 2\\n• Point 3",
            "trending_keyword": "keyword phrase",
            "trending_url": "https://www.youtube.com/results?search_query=keyword+2026"
          }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._extract_json(response.text)
        except Exception as e:
            print(f"[GEMINI ERROR] Failed to generate ideas: {e}")
            return []

    async def suggest_shorts_timestamps(self, video_title: str, video_description: str):
        if not self.model:
            return []
            
        prompt = f"""
        Analyze this YouTube video and identify 3 segments perfect for YouTube Shorts (under 60 seconds each).

        Video Title: {video_title}
        Video Description: {video_description}

        For each segment, think about what makes it highly shareable.
        Return ONLY a valid JSON array:
        [
          {{
            "start_time": "01:20",
            "stop_time": "01:50",
            "reason": "Why this segment works as a Short",
            "hook": "Opening line to grab attention in the Short"
          }}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            return self._extract_json(response.text)
        except Exception as e:
            print(f"[GEMINI ERROR] Failed to suggest shorts: {e}")
            return []
