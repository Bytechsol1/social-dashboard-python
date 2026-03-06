"""Debug endpoints — gated by DEBUG_MODE=true environment variable."""
import os
from fastapi import APIRouter, HTTPException, Request
from api.services.sync_engine import get_youtube_debug_info, get_manychat_debug_info

router = APIRouter()

DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"


def _require_debug():
    if not DEBUG_MODE:
        raise HTTPException(
            status_code=403,
            detail="Debug endpoints are disabled. Set DEBUG_MODE=true to enable."
        )


@router.get("/youtube/{user_id}")
def debug_youtube(user_id: str, request: Request):
    """
    Returns:
    - Token validity
    - Scopes granted vs requested
    - Channel ID in DB vs what API returns
    - Raw 7-day analytics response
    """
    _require_debug()
    return get_youtube_debug_info(user_id)


@router.get("/manychat/{user_id}")
def debug_manychat(user_id: str, request: Request):
    """
    Returns side-by-side comparison:
    - DB automations (with runs/ctr — should be NULL)
    - Live ManyChat API flow list
    - Explanation of why runs/CTR are not available
    """
    _require_debug()
    return get_manychat_debug_info(user_id)
