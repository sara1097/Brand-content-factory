from pydantic import BaseModel
from typing import Any, Dict


class MarketingInput(BaseModel):
    campaign_context: Dict[str, Any]
    target_persona: Dict[str, Any]
    platform_context: Dict[str, Any]
    content_input: Dict[str, Any]
    creative_constraints: Dict[str, Any]