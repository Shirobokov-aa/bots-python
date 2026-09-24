START = (
    "ChannelMirror — зеркало открытых каналов в твои.\n\n"
    "1) Добавь бота админом в свой канал (право постить)\n"
    "2) Перешли любой пост из своего канала сюда → цель\n"
    "3) Пришли ссылку/@юзернейм источника → выбери куда лить\n\n"
    "Посты копируются без ссылки на источник (silent copy).\n"
    "Интервал публикации по умолчанию ~1.5 ч.\n"
    "ИИ пока выключен."
)

HELP = (
    "Команды:\n"
    "/dests — твои каналы-цели\n"
    "/sources — источники\n"
    "/routes — маршруты источник→цель\n"
    "/del_route ID — удалить маршрут\n"
    "/toggle_route ID — вкл/выкл\n"
    "/interval ID СЕК — интервал маршрута (напр. 3600)\n"
    "/cancel — отмена\n\n"
    "Добавить цель: перешли пост из своего канала.\n"
    "Добавить источник: @channel или https://t.me/channel"
)


def dest_line(d) -> str:
    name = d.title or d.username or str(d.chat_id)
    uname = f" @{d.username}" if d.username else ""
    return f"#{d.id} {name}{uname} (`{d.chat_id}`)"


def source_line(s) -> str:
    title = f" — {s.title}" if s.title else ""
    return f"#{s.id} @{s.username}{title}"


def route_line(r) -> str:
    src = f"@{r.source.username}" if r.source else "?"
    dest = r.destination.title or (f"@{r.destination.username}" if r.destination and r.destination.username else str(r.destination.chat_id if r.destination else "?"))
    flag = "on" if r.is_active else "off"
    return f"#{r.id} {src} → {dest} [{flag}] every {r.interval_seconds}s"
