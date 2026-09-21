from datetime import datetime, timezone
from typing import Any, Optional
from app.core.database import get_db


async def log_action(
    actor_id: Optional[str],
    actor_type: str,  # "admin" | "customer" | "system"
    action: str,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> None:
    db = get_db()
    doc = {
        "actor_id": actor_id,
        "actor_type": actor_type,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "details": details or {},
        "ip": ip,
        "user_agent": user_agent,
        "created_at": datetime.now(timezone.utc),
    }
    await db.audit_logs.insert_one(doc)