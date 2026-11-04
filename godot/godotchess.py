import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS  # Обязательно для работы в браузере

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с Itch.io

# --- Настройки API ---
CHESS_API_URL = "https://chess-api.com/v1"
DEPTH = 18  # Глубина анализа (максимум для этого API)


@app.route('/bestmove', methods=['POST'])
def get_best_move():
    data = request.get_json()
    if not data or 'fen' not in data:
        return jsonify({"error": "Missing 'fen' field"}), 400

    fen = data['fen']

    # Формируем запрос к Chess-API
    payload = {
        "fen": fen,
        "depth": DEPTH
    }

    try:
        response = requests.post(CHESS_API_URL, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()

        # Chess-API возвращает ход в поле 'move' (например, "e2e4")
        # или в поле 'lan' (Long Algebraic Notation)
        move = result.get('move') or result.get('lan')

        if not move:
            return jsonify({"error": "No move found in API response", "api_response": result}), 500

        print(f"[Chess-API] FEN: {fen} -> Move: {move}")
        return jsonify({
            "move": move,
            "fen": result.get('fen', fen)  # Возвращаем обновленный FEN, если есть
        })

    except requests.exceptions.RequestException as e:
        print(f"[Chess-API] Request failed: {e}")
        return jsonify({"error": "Chess API is unavailable"}), 503


if __name__ == '__main__':
    # Хостинг сам выдаст нужный порт (переменная PORT)
    port = int(os.environ.get("PORT", 5002))
    print(f"Starting chess server on port {port}")
    app.run(host='0.0.0.0', port=port)
ить