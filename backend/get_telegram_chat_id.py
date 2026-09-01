
import sys
import httpx


def main():
    if len(sys.argv) != 2:
        print("Использование: python get_telegram_chat_id.py <ТОКЕН_БОТА>")
        sys.exit(1)

    token = sys.argv[1].strip()
    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Не удалось обратиться к Telegram API: {e}")
        print("Проверь токен и интернет-соединение.")
        sys.exit(1)

    data = resp.json()
    results = data.get("result", [])
    if not results:
        print(
            "Обновлений нет. Открой бота в Telegram, напиши ему любое "
            "сообщение (или добавь в группу и напиши там), затем запусти "
            "скрипт ещё раз."
        )
        sys.exit(0)

    seen = set()
    for update in results:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            continue
        chat = msg["chat"]
        key = chat["id"]
        if key in seen:
            continue
        seen.add(key)
        title = chat.get("title") or chat.get("username") or chat.get("first_name") or "—"
        print(f"chat_id = {chat['id']}   (тип: {chat['type']}, название/имя: {title})")

    if not seen:
        print("Сообщения найдены, но chat не распознан — попробуй написать боту снова.")


if __name__ == "__main__":
    main()
