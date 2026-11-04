import subprocess
import sys
import os

def run_servers():
    print("🚀 Запуск всех серверов...")
    
    # Запускаем main.py (ИИ Итчика на порту 5001)
    print("🤖 Запуск AI-сервера (main.py)...")
    ai_process = subprocess.Popen([sys.executable, "main.py"])
    
    # Запускаем godotchess.py (Шахматы на порту 5002)
    print("♟️ Запуск Шахматного сервера (godotchess.py)...")
    chess_process = subprocess.Popen([sys.executable, "godotchess.py"])
    
    try:
        # Ждем, пока оба процесса не завершатся (или пока ты не нажмешь Ctrl+C)
        ai_process.wait()
        chess_process.wait()
    except KeyboardInterrupt:
        print("\n⏹️ Остановка серверов...")
        ai_process.terminate()
        chess_process.terminate()
        print("✅ Серверы остановлены.")

if __name__ == "__main__":
    run_servers()
