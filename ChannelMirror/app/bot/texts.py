START = (
    "ChannelMirror — зеркало каналов в твои.\n\n"
    "1) Добавь бота админом в свой канал (право постить)\n"
    "2) Перешли любой пост из своего канала сюда → цель\n"
    "3) Публичный источник: @channel / https://t.me/channel\n"
    "4) Приватный: кнопка «Приватный источник» → forward или инвайт t.me/+\n"
    "5) При создании маршрута выбери: с источником или без\n\n"
    "«С источником» добавляет в конец поста текст вида:\n"
    'Источник: "Рога и копыта"\n'
    "(только название канала, без ссылки и без перехода).\n\n"
    "Нужен Telethon-аккаунт внутри источника (для приватных — вступить по инвайту).\n"
    "ИИ пока выключен."
)

HELP = (
    "Команды:\n"
    "/dests — твои каналы-цели\n"
    "/sources — источники\n"
    "/routes — маршруты источник→цель\n"
    "/del_route ID — удалить маршрут\n"
    "/toggle_route ID — вкл/выкл маршрут\n"
    "/toggle_source ID — вкл/выкл подпись Источник\n"
    "/interval ID СЕК — интервал маршрута (0 = сразу, напр. /interval 1 3600)\n"
    "/cancel — отмена\n\n"
    "Добавить цель: перешли пост из своего канала.\n"
    "Публичный источник: @channel или https://t.me/channel\n"
    "Приватный: кнопка «Приватный источник» → forward поста или t.me/+инвайт\n"
    "Подпись источника — только текст названия, не ссылка."
)

PRIVATE_SOURCE_HINT = (
    "Приватный источник.\n\n"
    "1) Telethon-аккаунт должен быть участником канала (или вступит по инвайту)\n"
    "2) Перешли сюда любой пост из того канала\n"
    "   ИЛИ пришли инвайт: https://t.me/+XXXX\n\n"
    "/cancel — отмена"
)

SOURCE_LABEL_ASK = (
    "Указывать источник текстом в конце поста?\n\n"
    'Пример: Источник: "Рога и копыта"\n'
    "(только название канала — без ссылки и без перехода)"
)


def dest_line(d) -> str:
    name = d.title or d.username or str(d.chat_id)
    uname = f" @{d.username}" if d.username else ""
    return f"#{d.id} {name}{uname} (`{d.chat_id}`)"


def source_line(s) -> str:
    title = f" — {s.title}" if s.title else ""
    cid = f" `{s.chat_id}`" if s.chat_id else ""
    if s.username and str(s.username).startswith("id"):
        label = s.title or s.username
        return f"#{s.id} [private] {label}{cid}"
    return f"#{s.id} @{s.username}{title}{cid}"


def route_line(r) -> str:
    if r.source and r.source.username and not str(r.source.username).startswith("id"):
        src = f"@{r.source.username}"
    elif r.source:
        src = r.source.title or str(r.source.chat_id or r.source.username)
    else:
        src = "?"
    dest = r.destination.title or (
        f"@{r.destination.username}"
        if r.destination and r.destination.username
        else str(r.destination.chat_id if r.destination else "?")
    )
    flag = "on" if r.is_active else "off"
    src_flag = "src" if getattr(r, "show_source_label", False) else "silent"
    return f"#{r.id} {src} → {dest} [{flag}|{src_flag}] every {r.interval_seconds}s"
