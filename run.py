import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from memory import MemoryManager

# ==========================================
# 1. НАСТРОЙКИ ДЛЯ ИИ (ИТЧИКА)
# ==========================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "твой_ключ_сюда")
MODEL = "deepseek/deepseek-chat"
MAX_TOKENS = 200
TEMPERATURE = 0.8

try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT = "Ты Итчика. Ты холодная, манипулируешь людьми, говоришь спокойно и загадочно."

# ==========================================
# 2. НАСТРОЙКИ ДЛЯ ШАХМАТ
# ==========================================
CHESS_API_URL = "https://chess-api.com/v1"
CHESS_DEPTH = 18

# ==========================================
# 3. ИНИЦИАЛИЗАЦИЯ СЕРВЕРА
# ==========================================
app = Flask(__name__)
CORS(app) 
memory = MemoryManager()

# ==========================================
# 4. ЭНДПОИНТ ДЛЯ ИИ (/chat)
# ==========================================
def chat_with_itchika(user_message, history):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://itch.io",
        "X-Title": "Itchika Game",
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenRouter error: {e}")
        return None

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data: return jsonify({"error": "Empty request"}), 400

    user_msg = data.get("user_message", "").strip()
    session_id = data.get("session_id", "default_player")
    if not user_msg: return jsonify({"error": "Empty message"}), 400

    history = memory.get_history(session_id)
    ai_reply = chat_with_itchika(user_msg, history)

    if ai_reply is None:
        return jsonify({"reply": "Ошибка связи с нейросетью."}), 200

    memory.add_message(session_id, "user", user_msg)
    memory.add_message(session_id, "assistant", ai_reply)
    return jsonify({"reply": ai_reply})

# ==========================================
# 5. ЭНДПОИНТ ДЛЯ ШАХМАТ (/bestmove)
# ==========================================
@app.route("/bestmove", methods=["POST"])
def bestmove():
    data = request.get_json()
    if not data or 'fen' not in data:
        return jsonify({"error": "Missing 'fen' field"}), 400

    fen = data['fen']
    payload = {"fen": fen, "depth": CHESS_DEPTH}
    
    try:
        response = requests.post(CHESS_API_URL, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        move = result.get('move') or result.get('lan')
        
        if not move:
            return jsonify({"error": "No move found"}), 500
            
        return jsonify({"move": move, "fen": result.get('fen', fen)})
    except Exception as e:
        print(f"Chess API error: {e}")
        return jsonify({"error": "Chess API unavailable"}), 503

# ==========================================
# 6. ЗАПУСК (ВАЖНО ДЛЯ RENDER)
# ==========================================
if __name__ == "__main__":
    # Render сам подставит свой порт сюда
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port)
