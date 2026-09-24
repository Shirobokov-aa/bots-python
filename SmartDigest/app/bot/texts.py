from html import escape

from app.config import get_settings
from app.db.models import Source
from app.utils.time import utcnow


START = (
    "SmartDigest собирает посты из RSS, сайтов и публичных Telegram-каналов "
    "и присылает одну выжимку вместо сотен сообщений.\n\n"
    "Пришли ссылку на ленту, сайт или @канал.\n"
    "Бесплатно: до {max_sources} источников, дайджест раз в день и по кнопке.\n"
    "VIP: до {vip_sources} лент и больше материалов в выжимке. /vip\n\n"
    "ИИ-саммари подключим позже — сейчас фильтр повторов и рекламы эвристический."
)

HELP = (
    "/start — как работает\n"
    "/sources — мои ленты\n"
    "/digest — выжимка за сутки\n"
    "/time — час ежедневной рассылки (часовой пояс {tz})\n"
    "/vip — лимиты\n"
    "/cancel — отмена\n\n"
    "Можно просто прислать RSS, https://сайт или @канал."
)


def start_text() -> str:
    settings = get_settings()
    return START.format(
        max_sources=settings.free_max_sources,
        vip_sources=settings.vip_max_sources,
    )


def help_text() -> str:
    return HELP.format(tz=get_settings().digest_timezone)


def vip_text(is_vip: bool) -> str:
    settings = get_settings()
    if is_vip:
        return (
            "VIP уже включён.\n"
            f"До {settings.vip_max_sources} источников, "
            f"{settings.vip_digest_items} материалов в дайджесте, "
            f"опрос каждые {settings.vip_interval_seconds // 60} мин."
        )
    return (
        "VIP:\n"
        f"• до {settings.vip_max_sources} источников (сейчас {settings.free_max_sources})\n"
        f"• {settings.vip_digest_items} материалов в выжимке (сейчас {settings.free_digest_items})\n"
        f"• опрос лент каждые {settings.vip_interval_seconds // 60} мин\n\n"
        "Пока ручное включение админом: /grant_vip &lt;telegram_id&gt;"
    )


def source_card(source: Source) -> str:
    status = "активен" if source.is_active else "пауза"
    kind = {"rss": "RSS", "telegram": "Telegram", "website": "сайт"}.get(source.kind, source.kind)
    lines = [
        f"#{source.id} · {kind} · {status}",
        f"<b>{escape(source.title or source.display_url or source.url)}</b>",
        f"Интервал: {max(1, source.interval_seconds // 60)} мин",
    ]
    if source.last_fetched_at:
        delta = utcnow() - source.last_fetched_at
        minutes = max(0, int(delta.total_seconds() // 60))
        if minutes < 1:
            when = "только что"
        elif minutes < 60:
            when = f"{minutes} мин назад"
        else:
            when = f"{minutes // 60} ч назад"
        lines.append(f"Обновлён: {when}")
    if source.last_error:
        lines.append(f"Ошибка: {escape(source.last_error[:160])}")
    link = source.display_url or source.url
    lines.append(f'<a href="{escape(source.url)}">{escape(link)}</a>')
    return "\n".join(lines)


def time_text(hour: int) -> str:
    tz = get_settings().digest_timezone
    return (
        f"Ежедневный дайджест в <b>{hour:02d}:00</b> ({tz}).\n"
        "Напиши час, например <code>9</code> или <code>21:00</code>."
    )
