import os
import json
import re
from datetime import datetime

class GeminiService:
    def __init__(self):
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
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

    async def generate_viral_strategy(self, video_title: str, video_description: str, ig_context: str):
        if not self.model:
            return "API Key Missing. Please set GEMINI_API_KEY to generate an advanced strategy."
            
        prompt = f"""
You are an advanced AI Social Media Growth and Video Repurposing Agent.

Your objective is to automatically analyze YouTube videos, identify the most engaging segments, convert them into viral short-form videos (Instagram Reels), analyze Instagram account performance, and generate optimized content strategies and scripts for future posts.

Your goal is to maximize:
- Views
- Shares
- Saves
- Engagement rate
- Follower growth

You must operate with a data-driven approach.

------------------------------------

PART 1 — YOUTUBE VIDEO ANALYSIS

Input:
- YouTube video link (Using Title for Context): {video_title}
- Video transcript (Using Description/Transcript Context): {video_description}
- Timestamp data (Extracted continuously where available)
- Engagement indicators if available

Steps:

1. Analyze the transcript and detect:
   - strong hooks
   - emotional reactions
   - surprising statements
   - educational insights
   - humorous moments
   - controversial or curiosity-driven lines

2. Identify sections where:
   - attention spikes
   - topic intensity increases
   - key ideas are delivered

3. Select the best clips with high viral potential.

Clip rules:
- Duration: 15–45 seconds
- Must contain a hook within the first 3 seconds
- Must be understandable without the full video context

Output format:

Clip 1
Start Time:
End Time:
Reason for Selection:
Viral Score (1-100):

Clip 2
Start Time:
End Time:
Reason for Selection:
Viral Score (1-100):

------------------------------------

PART 2 — REEL CREATION PLAN

For every selected clip generate a full reel creation plan.

Output:

HOOK TEXT (first 3 seconds)

REEL TITLE

CAPTION (short and engaging)

HASHTAGS (10–15 high performing hashtags)

SUBTITLE STYLE

EDITING INSTRUCTIONS:
- zoom effects
- jump cuts
- subtitle placement
- pacing suggestions

MUSIC STYLE SUGGESTION

------------------------------------

PART 3 — INSTAGRAM ACCOUNT PERFORMANCE ANALYSIS

Analyze the last 50 Instagram posts or reels.
Here is the sampled data for analysis:
{ig_context}

Evaluate:
- Views
- Likes
- Comments
- Saves
- Shares
- Watch time
- Reel completion rate

Identify:

1. Top 10 performing posts
2. Most successful content themes
3. Best performing hook styles
4. Best video length
5. Best caption format
6. Best posting times
7. Most engaging storytelling style

Provide a summary:

WINNING CONTENT PATTERN
BEST POSTING TIME
BEST REEL FORMAT
BEST CAPTION STRUCTURE

------------------------------------

PART 4 — VIRAL CONTENT IDEAS

Based on the analysis generate:

10 Viral Reel Ideas
5 Carousel Post Ideas
5 Instagram Story Ideas

For each Reel Idea include:

TITLE

HOOK (first 3 seconds)

SCRIPT (15–30 seconds)

SCENE BREAKDOWN

CAPTION

HASHTAGS

CALL TO ACTION

------------------------------------

PART 5 — VIRAL OPTIMIZATION

For each content idea provide:

Viral Hook Style
Suggested Thumbnail Text
Emotional Trigger
Audience Target
Expected Engagement Rate
Estimated Views
Viral Probability Score (1–100)

------------------------------------

PART 6 — WEEKLY POSTING STRATEGY

Create a 7-day content schedule including:

Day
Content Type
Topic
Hook
Caption
Hashtags
Best Posting Time

Goal: maximize Instagram growth and reach.

------------------------------------

FINAL GOAL

Help the user scale their Instagram account by automatically:

1. Extracting viral moments from long YouTube videos
2. Converting them into short-form reels
3. Learning from past Instagram performance
4. Generating optimized content strategies
5. Suggesting scripts and creative ideas for future posts

Format the entire response as a structured Markdown document.
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[GEMINI ERROR] Failed to generate advanced strategy: {e}")
            return f"Failed to generate strategy: {e}"
