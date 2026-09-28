from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceAlert, User


async def add_alert(
    session: AsyncSession,
    user: User,
    origin: str,
    destination: str,
    max_price: int,
) -> PriceAlert:
    alert = PriceAlert(
        user_id=user.id,
        origin=origin.upper(),
        destination=destination.upper(),
        max_price=max_price,
        is_active=True,
    )
    session.add(alert)
    await session.flush()
    return alert


async def list_alerts(session: AsyncSession, user_id: int) -> list[PriceAlert]:
    result = await session.execute(
        select(PriceAlert).where(PriceAlert.user_id == user_id).order_by(PriceAlert.id.desc())
    )
    return list(result.scalars().all())


async def deactivate_alert(session: AsyncSession, user_id: int, alert_id: int) -> bool:
    result = await session.execute(
        select(PriceAlert).where(PriceAlert.id == alert_id, PriceAlert.user_id == user_id)
    )
    alert = result.scalar_one_or_none()
    if alert is None:
        return False
    alert.is_active = False
    return True
