import requests
import os
import random
import re
import json
import sys
from datetime import datetime, timedelta

# --- Константы ---
BOOK_FILE = "book.txt"
STATE_FILE = "week_state.json"
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
WEEKLY_TOTAL = 14          # сколько сообщений за неделю
MIN_SENTENCE_LENGTH = 20   # минимальная длина предложения

# --- Функция извлечения предложений из текста ---
def extract_sentences(text):
    """
    Разбивает текст на предложения, учитывая:
    - окончания .?! (но не многоточие)
    - не разбивает на сокращениях типа т.д., т.п.
    - предложения могут начинаться с —
    """
    # Заменяем многоточие на временный маркер, чтобы не разбивать по точкам внутри
    text = re.sub(r'\.\.\.', '…', text)  # заменяем на один символ многоточия

    # Регулярка для границ предложений
    # Ищем .?! после которых пробел и следующая буква заглавная или кавычка или тире
    # Это сложная тема, для простоты используем упрощённый вариант:
    # Разбиваем по .?! за которыми следует пробел и затем не сокращение
    # Но проще сначала разбить принудительно, а потом отфильтровать
    sentences = re.split(r'(?<=[.!?])\s+(?=[А-ЯA-Z"«—])', text)

    # Очищаем от лишних пробелов и пустых строк
    sentences = [s.strip() for s in sentences if s.strip()]

    # Убираем совсем короткие
    sentences = [s for s in sentences if len(s) > MIN_SENTENCE_LENGTH]

    # Возвращаем символ многоточия обратно (если нужно) — но можно оставить
    # sentences = [s.replace('…', '...') for s in sentences]

    return sentences

# --- Загрузка книги и получение списка предложений ---
def load_sentences():
    if not os.path.exists(BOOK_FILE):
        print(f"❌ Файл {BOOK_FILE} не найден")
        return []
    try:
        with open(BOOK_FILE, 'r', encoding='utf-8') as f:
            text = f.read()
        return extract_sentences(text)
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return []

# --- Работа с состоянием ---
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def get_week_number():
    """Возвращает номер недели от начала года (можно использовать для сброса)"""
    return datetime.now().isocalendar()[1]

def update_state(sentences_count):
    state = load_state()
    current_week = get_week_number()

    if state is None or state.get('week') != current_week:
        # Новая неделя — сбрасываем
        state = {
            'week': current_week,
            'used_indices': [],
            'count': 0
        }
    return state

def choose_sentence(sentences, state):
    available = [i for i in range(len(sentences)) if i not in state['used_indices']]
    if not available:
        # Если все предложения использованы (маловероятно), сбрасываем used_indices
        state['used_indices'] = []
        available = list(range(len(sentences)))

    index = random.choice(available)
    state['used_indices'].append(index)
    state['count'] += 1
    return sentences[index], index

# --- Отправка в Discord ---
def send_to_discord(sentence, count, total_sentences):
    if not WEBHOOK_URL:
        print("❌ WEBHOOK_URL не задан!")
        return False

    payload = {
        "content": "Сегодняшнее предложение:",
        "embeds": [
            {
                "description": f"**{sentence}**",
                "color": 4210752,
                "footer": {
                    "text": f"{count}/{WEEKLY_TOTAL}"   # count — текущий номер недели (1..14)
                }
            }
        ],
        "username": "Библиотекарь",
        "avatar_url": "https://i.pinimg.com/736x/b0/2f/15/b02f15dd168781276a8cf322aa8da4b9.jpg",
        "attachments": []
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 204:
            print("✅ Сообщение успешно отправлено!")
            return True
        else:
            print(f"❌ Discord вернул ошибку: {response.status_code}")
            print("Ответ:", response.text)
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при отправке запроса: {e}")
        return False

# --- Главная функция ---
def main():
    print("🔍 Запуск скрипта...")
    sentences = load_sentences()
    if not sentences:
        print("❌ Нет предложений для отправки.")
        sys.exit(1)
    print(f"Загружено предложений: {len(sentences)}")

    state = update_state(len(sentences))
    print(f"Неделя: {state['week']}, уже отправлено: {state['count']}")

    if state['count'] >= WEEKLY_TOTAL:
        print("⚠️ За эту неделю уже отправлено 14 сообщений. Пропускаем отправку.")
        # Можно ничего не отправлять, либо отправить что-то ещё
        sys.exit(0)

    sentence, idx = choose_sentence(sentences, state)
    print(f"Выбрано предложение #{idx}: {sentence[:50]}...")

    success = send_to_discord(sentence, state['count'], len(sentences))
    if success:
        save_state(state)
        print("✅ Состояние сохранено.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
