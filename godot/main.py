import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- КРИТИЧЕСКИ ВАЖНО для браузера
from memory import MemoryManager

# ---------- КОНФИГУРАЦИЯ ----------
# Ключ лучше брать из переменных окружения хостинга, но для теста можно оставить тут
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "твой_ключ_сюда")
MODEL = "deepseek/deepseek-chat"
MAX_TOKENS = 200
TEMPERATURE = 0.8

# Чтение промпта (можно оставить твои файлы или захардкодить)
try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "Ты Итчика. Ты холодная, манипулируешь людьми, говоришь спокойно и загадочно. Ты недоверчива."

# ---------- СЕРВЕР ----------
app = Flask(__name__)
CORS(app)  # <--- Разрешаем запросы с сайта itch.io
memory = MemoryManager()


def chat_with_itchika(user_message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://itch.io",  # Требование OpenRouter
        "X-Title": "Itchika Game",
    }

    # ПРОКСИ ОТКЛЮЧЕН (None), так как на хостинге нет твоего локального Tor
    proxies = None

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            proxies=proxies,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None


# ---------- ЭНДПОИНТ ДЛЯ GODOT ----------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Empty request"}), 400

    # Godot присылает именно эти поля
    user_msg = data.get("user_message", "").strip()
    session_id = data.get("session_id", "default_player")

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    # Получаем историю конкретного игрока
    history = memory.get_history(session_id)

    # Идем к ИИ
    ai_reply = chat_with_itchika(user_msg, history)

    if ai_reply is None:
        return jsonify(
            {"reply": "Ошибка связи с нейросетью. Попробуй позже."}), 200  # Отдаем 200, чтобы Godot не крашился

    # Сохраняем историю для этого игрока
    memory.add_message(session_id, "user", user_msg)
    memory.add_message(session_id, "assistant", ai_reply)

    # Godot ждет поле "reply"
    return jsonify({"reply": ai_reply})


# ---------- ЗАПУСК ----------
if __name__ == "__main__":
    # Хостинги (Render, Railway) сами выдают порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 5001))
    print(f"Starting Itchika server on port {port}")
    app.run(host="0.0.0.0", port=port)