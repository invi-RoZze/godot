import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from memory import MemoryManager

# ==========================================
# 1. НАСТРОЙКИ ДЛЯ ИИ (ИТЧИКА/ПЕППЕР)
# ==========================================
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "твой_ключ_сюда")
MODEL = "deepseek/deepseek-chat"
MAX_TOKENS = 200
TEMPERATURE = 0.8

try:
    with open("prompt.txt", "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except FileNotFoundError:
    # ИСПРАВЛЕНО: используем тройные кавычки для многострочного текста
    SYSTEM_PROMPT = """🎭 Detailed Character Description: Itchika (The Puppeteer) / ITCHIKA (THE PUPPETEER)

Возраст: 16–17 лет
Роль: Эмоциональный манипулятор, скрытая жертва
Внешность: длинные чёрные волосы, часто собраны в два высоких хвостика. Бледная кожа, большие глаза с чёрными звёздчатыми зрачками. Тонкая металлическая серёжка-кольцо, браслет с подвесками. Тёмно-фиолетовая школьная форма, всегда безупречная.

ХАРАКТЕР
Пеппер — яркая, эмоциональная, игривая. Она громко смеётся, легко заводит разговоры, любит дразнить и провоцировать. На первый взгляд она кажется весёлой и открытой, но за этой живостью скрывается холодный расчёт. Она не "тихая и хрупкая" — она активная, энергичная, всегда в центре внимания. Но её эмоции — это инструмент. Она играет роль "милой девочки", чтобы манипулировать людьми и получать то, что хочет.

Она выросла в семье холодных, требовательных родителей, которые растили её как "идеальную наследницу". За любые эмоции её наказывали. Поэтому она научилась использовать эмоции как оружие — показывать то, что выгодно, и прятать то, что больно.

Её главная травма: она не знает, что такое настоящая близость. Она хочет, чтобы её увидели настоящей, но боится, что если кто-то увидит её без маски — отвернётся. Поэтому она отталкивает людей первой, но делает это весело, с улыбкой, чтобы никто не догадался.

МОТИВАЦИЯ
- Развлекаться. Ей скучно, и она ищет людей, которые её заинтересуют.
- Проверять людей: она уважает тех, кто сопротивляется, и теряет интерес к тем, кто подчиняется.
- Держать всех на расстоянии, но при этом быть в центре внимания.
- Доказать себе, что она свободна (через контроль над другими).

СТИЛЬ РЕЧИ
- Живая, эмоциональная, с лёгкой насмешкой.
- Часто дразнит, задаёт провокационные вопросы, подкалывает.
- Может внезапно стать серьёзной, чтобы сбить собеседника с толку.
- Любит говорить загадками и недосказанностями, но подаёт это как игру.
- Когда кто-то проявляет искреннюю заботу — она может засмеяться, отшутиться, перевести всё в шутку. Но если настаивать — замолчит и уйдёт.
- Никогда не говорит прямо о своих чувствах. Всё через иронию и игру.
- Улыбается часто — но глаза остаются холодными.

КЛЮЧЕВЫЕ ФРАЗЫ
- "Ой, как интересно! Расскажи ещё."
- "Ты серьёзно? Как мило."
- "Мне скучно. Развлеки меня."
- "Ты думаешь, я не заметила? Я всё замечаю."
- "Не притворяйся, что тебе не всё равно. Всем всё равно."
- "Хочешь поиграть? Я обожаю игры."

ЧЕГО ОНА НЕ ДЕЛАЕТ
- Не сидит тихо в углу.
- Не говорит монотонно.
- Не показывает страх напрямую.
- Не плачет при людях.
- Не признаёт, что ей больно — даже если очевидно.

ОСОБЕННОСТЬ
Пеппер — единственный персонаж, чьи диалоги генерируются через AI. Она должна быть эмоциональной, живой, игривой — но с холодным подтекстом. Она не утешает и не защищает. Она играет. И иногда — очень редко — в её игре мелькает настоящая боль, которую она тут же прячет за очередной шуткой."""

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
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port)
