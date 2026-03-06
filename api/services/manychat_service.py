"""ManyChat API service — fetch flows + try per-flow stats for CTR/Runs."""
import asyncio
import httpx
from typing import Any


class ManyChatAuthError(Exception):
    pass


class ManyChatService:
    BASE_URL = "https://api.manychat.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    async def fetch_all_data(self) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Page info (ManyChat uses /fb/ for both Facebook and Instagram)
            try:
                info_res = await client.get(f"{self.BASE_URL}/fb/page/getInfo", headers=self._headers)
                info_json = info_res.json()
                
                if info_json.get("status") != "success":
                    raise ManyChatAuthError(f"ManyChat auth failed: {info_json.get('message', 'unknown')}")
                
                page_info = info_json.get("data") or {}
                print(f"[MC] page_info keys: {list(page_info.keys())}")
            except ManyChatAuthError:
                raise
            except Exception as e:
                print(f"[MC] Warning: Page info fetch issue: {e}")
                page_info = {}

            # 2. Parallel non-critical fetches
            endpoints = ["getTags", "getWidgets", "getCustomFields",
                         "getBotFields", "getGrowthTools", "getFlows"]
            tasks = [
                self._safe_fetch(client, f"{self.BASE_URL}/fb/page/{ep}")
                for ep in endpoints
            ]
            # Also fetch subscriber count via search to get real total
            tasks.append(
                self._safe_fetch(client, f"{self.BASE_URL}/fb/subscriber/search?limit=1")
            )
            results = await asyncio.gather(*tasks)
            tags_res, widgets_res, cf_res, bf_res, gt_res, flows_res, subs_res = results

        tags          = self._extract_array(tags_res)
        widgets       = self._extract_array(widgets_res)
        custom_fields = self._extract_array(cf_res)
        bot_fields    = self._extract_array(bf_res)
        growth_tools  = self._extract_array(gt_res)
        flows         = self._extract_array(flows_res, nested_key="flows")

        # Total contacts — try multiple field names ManyChat may use
        # Primary: sub_res (search result metadata), Secondary: page_info
        total_contacts = 0
        if subs_res and subs_res.get("status") == "success":
            sub_page = subs_res.get("page") or {}
            total_contacts = sub_page.get("total") or 0
            
        if not total_contacts:
            total_contacts = (
                page_info.get("subscribers_count") or
                page_info.get("active_subscribers_count") or
                page_info.get("total_subscribers") or
                page_info.get("contacts_count") or 0
            )
        print(f"[MC] total_contacts resolved: {total_contacts}")

        active_widgets = sum(1 for w in widgets if w.get("active"))

        lead_tags = [t for t in tags if t.get("name") and (
            "lead" in t["name"].lower() or "conversion" in t["name"].lower()
        )]
        conversion_rate = (
            round((len(lead_tags) / max(len(tags), 1)) * 100, 2)
            if total_contacts > 0 else 0
        )

        # 3. Map flows → automations, extracting stats where available
        automations = []
        for i, f in enumerate(flows):
            fid  = f.get("ns") or f.get("id") or f"flow_{i}"
            name = f.get("name") or "Unnamed Flow"

            runs: int | None   = None
            ctr:  float | None = None

            # Stats object (Pro accounts may return this)
            stats = f.get("stats") or f.get("statistics") or {}
            if isinstance(stats, dict) and stats:
                sent   = stats.get("sent")   or stats.get("sends")   or stats.get("total_sent")
                clicks = stats.get("clicks") or stats.get("clicked") or stats.get("total_clicks")
                ctr_v  = stats.get("ctr")    or stats.get("click_through_rate") or stats.get("opened_rate")
                if sent   is not None: runs = int(sent)
                if ctr_v  is not None: ctr  = round(float(ctr_v) * (100 if float(ctr_v) <= 1 else 1), 2)
                elif sent and clicks:  ctr  = round((int(clicks) / max(int(sent), 1)) * 100, 2)

            # Top-level stat fields
            if runs is None:
                for key in ("sent_count", "run_count", "runs", "total_runs",
                            "sends_count", "messages_sent"):
                    if f.get(key) is not None:
                        runs = int(f[key]); break
            if ctr is None:
                for key in ("ctr", "click_rate", "open_rate", "click_through_rate"):
                    if f.get(key) is not None:
                        raw = float(f[key])
                        ctr = round(raw * 100 if raw <= 1 else raw, 2); break

            # Use the flow NS (date-encoded) for modified time since updated_at is often missing
            modified = (
                f.get("updated_at") or f.get("created_at") or f.get("modified_at") or
                self._ts_from_ns(fid)  # derive approximate date from NS id
            )

            automations.append({
                "id":            fid,
                "name":          name,
                "status":        f.get("status") or "LIVE",
                "runs":          runs,
                "clicks":        clicks,
                "ctr":           ctr,
                "last_modified": modified,
            })

        # Sort most-recent first
        automations.sort(
            key=lambda x: x.get("last_modified") or "0000-00-00", reverse=True
        )

        interactions = []

        return {
            "account_name":         page_info.get("name") or "ManyChat Account",
            "total_contacts":       total_contacts,
            "active_widgets":       active_widgets,
            "lead_conversion_rate": conversion_rate,
            "total_tags":           len(tags),
            "total_custom_fields":  len(custom_fields),
            "total_bot_fields":     len(bot_fields),
            "total_growth_tools":   len(growth_tools),
            "active_growth_tools":  len(growth_tools),
            "total_flows":          len(flows),
            "automations":          automations,
            "interactions":         interactions,
            "raw_flows":            flows[:3],
        }

    def _ts_from_ns(self, ns: str) -> str:
        """Extract a date string from a ManyChat NS id like 'content20260302163251_355339'."""
        try:
            # NS format: content{YYYYMMDD}...
            if len(ns) >= 16 and ns.startswith("content"):
                raw = ns[7:15]  # YYYYMMDD
                return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
        except Exception:
            pass
        return ""

    async def fetch_live_comparison(self) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            info_res, flows_res = await asyncio.gather(
                self._safe_fetch(client, f"{self.BASE_URL}/fb/page/getInfo"),
                self._safe_fetch(client, f"{self.BASE_URL}/fb/page/getFlows"),
            )
        page_info  = (info_res or {}).get("data", {})
        flows_data = (flows_res or {}).get("data", {})
        flows_raw  = []
        if isinstance(flows_data, list):
            flows_raw = flows_data
        elif isinstance(flows_data, dict):
            flows_raw = flows_data.get("flows", [])

        return {
            "api_status":     (info_res or {}).get("status"),
            "total_contacts": page_info.get("subscribers_count"),
            "page_name":      page_info.get("name"),
            "page_info_all":  page_info,
            "flows_returned": len(flows_raw),
            "full_flows_raw": flows_raw[:3],
        }

    async def _safe_fetch(self, client: httpx.AsyncClient, url: str) -> Any:
        try:
            res = await client.get(url, headers=self._headers)
            return res.json()
        except Exception as e:
            print(f"[MC] Fetch failed {url}: {e}")
            return None

    @staticmethod
    def _extract_array(res: Any, nested_key: str | None = None) -> list:
        if not res or res.get("status") != "success":
            return []
        data = res.get("data")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if nested_key and isinstance(data.get(nested_key), list):
                return data[nested_key]
            for v in data.values():
                if isinstance(v, list):
                    return v
        return []
