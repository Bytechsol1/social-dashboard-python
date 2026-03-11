import os
import httpx
from datetime import datetime, timezone
from typing import Optional, List, Dict

class InstagramService:
    BASE_URL = "https://graph.facebook.com/v19.0"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30)
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def get_user_id(self) -> Optional[str]:
        """Fetch the Instagram Business Account ID associated with the token."""
        try:
            client = await self._get_client()
            res = await client.get(
                f"{self.BASE_URL}/me/accounts",
                params={"access_token": self.access_token}
            )
            data = res.json()
            print(f"[IG SERVICE] /me/accounts response: {data}")
            
            if "data" not in data or not data["data"]:
                print("[IG SERVICE] No Facebook Pages found for this token.")
                return None
            
            # For each page, check for an attached Instagram Business account
            for page in data["data"]:
                page_id = page["id"]
                page_name = page.get("name", "Unknown")
                print(f"[IG SERVICE] Checking page: {page_name} ({page_id})")
                res_ig = await client.get(
                    f"{self.BASE_URL}/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": self.access_token
                    }
                )
                ig_data = res_ig.json()
                print(f"[IG SERVICE] Page {page_id} IG data: {ig_data}")
                if "instagram_business_account" in ig_data:
                    ig_id = ig_data["instagram_business_account"]["id"]
                    print(f"[IG SERVICE] Found Instagram Business Account: {ig_id}")
                    return ig_id
            print("[IG SERVICE] No linked Instagram Business Account found across all pages.")
            return None
        except Exception as e:
            print(f"[IG SERVICE] Error fetching user ID: {e}")
            import traceback
            print(traceback.format_exc())
            return None

    async def get_profile_info(self, ig_user_id: str) -> Dict:
        """Fetch basic profile stats (followers, media count)."""
        client = await self._get_client()
        res = await client.get(
            f"{self.BASE_URL}/{ig_user_id}",
            params={
                "fields": "username,followers_count,media_count",
                "access_token": self.access_token
            }
        )
        return res.json()

    async def get_user_insights(self, ig_user_id: str) -> List[Dict]:
        """Fetch user-level insights (reach, impressions)."""
        client = await self._get_client()
        # Fetch both daily and 28-day data for better coverage
        res = await client.get(
            f"{self.BASE_URL}/{ig_user_id}/insights",
            params={
                "metric": "reach,impressions",
                "period": "days_28",
                "access_token": self.access_token
            }
        )
        data = res.json()
        return data.get("data", [])

    async def get_audience_insights(self, ig_user_id: str) -> List[Dict]:
        """Fetch audience demographics (city, country, gender_age)."""
        try:
            client = await self._get_client()
            res = await client.get(
                f"{self.BASE_URL}/{ig_user_id}/insights",
                params={
                    "metric": "reached_audience_demographics,follower_demographics",
                    "period": "lifetime",
                    "access_token": self.access_token
                }
            )
            data = res.json()
            if "error" in data:
                print(f"[IG SERVICE] Audience insights error: {data['error'].get('message')}")
                return []
            return data.get("data", [])
        except Exception as e:
            print(f"[IG SERVICE] Audience insights failure: {e}")
            return []

    async def get_media_list(self, ig_user_id: str, limit: int = 20) -> List[Dict]:
        """Fetch recent media (posts/reels) with core fields and insights in one go."""
        # Using field expansion to get insights without dozens of extra calls
        fields = (
            "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count,"
            "insights.metric(impressions,reach,saved,video_views)"
        )
        try:
            client = await self._get_client()
            res = await client.get(
                f"{self.BASE_URL}/{ig_user_id}/media",
                params={
                    "fields": fields,
                    "limit": limit,
                    "access_token": self.access_token
                }
            )
            data = res.json()
            media_list = data.get("data", [])
            
            # Flatten the expanded insights for each media item
            for item in media_list:
                if "insights" in item:
                    for insight in item["insights"].get("data", []):
                        # Usually values[0] is the current value
                        if insight.get("values"):
                            item[insight["name"]] = insight["values"][0]["value"]
                    del item["insights"]
            return media_list
        except Exception as e:
            print(f"[IG SERVICE] Error fetching media list: {e}")
            return []
