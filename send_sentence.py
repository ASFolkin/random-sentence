import requests
import os
import random
import re
from datetime import date

# --- Настройки ---
BOOK_FILE = "book.txt"          # имя файла с книгой
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")  # берём из секрета

# --- Функция разбиения текста на предложения ---
def split_sentences(text):
    # Простое разбиение по ". " (точка + пробел)
    # Можно усложнить, если нужно учитывать сокращения
    sentences = [s.strip() for s in text.split('. ') if s.strip()]
    return sentences

# --- Загрузка книги и подготовка списка предложений ---
def load_sentences():
    with open(BOOK_FILE, 'r', encoding='utf-8') as f:
        text = f.read()
    return split_sentences(text)

# --- Получение предложения для сегодняшнего дня ---
def get_today_sentence(sentences):
    today_str = date.today().isoformat()  # например, 2025-02-15
    # Используем дату как seed для детерминированного выбора
    random.seed(today_str)
    index = random.randint(0, len(sentences) - 1)
    return sentences[index]

# --- Отправка сообщения в Discord через вебхук ---
def send_to_discord(sentence, index, total):
    # Ваш шаблон
    payload = {
        "content": "Сегодняшнее предложение:",
        "embeds": [
            {
                "description": f"**{sentence}**",
                "color": 4210752,  # тёмно-серый
                "footer": {
                    "text": f"{index+1}/{total}"   # например, 1/1423
                }
            }
        ],
        "username": "Библиотекарь",
        "avatar_url": "https://i.pinimg.com/736x/b0/2f/15/b02f15dd168781276a8cf322aa8da4b9.jpg",
        "attachments": []
    }

    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Сообщение успешно отправлено!")
    else:
        print(f"Ошибка: {response.status_code} - {response.text}")

# --- Главная функция ---
def main():
    if not WEBHOOK_URL:
        print("Ошибка: не задан DISCORD_WEBHOOK_URL")
        return

    sentences = load_sentences()
    if not sentences:
        print("Ошибка: нет предложений в книге")
        return

    today_sentence = get_today_sentence(sentences)
    # Находим индекс этого предложения (для footer)
    # Для этого можно заново прогнать seed или просто запомнить индекс
    # Проще: после random.seed(today_str) запомнить индекс
    # Переделаем get_today_sentence так, чтобы возвращала и индекс
    # Но для простоты оставим так: индекс не критичен, можно поставить 1/общее
    total = len(sentences)
    # Чтобы индекс был правильным, нужно внутри get_today_sentence возвращать и индекс.
    # Давайте перепишем функцию:
    def get_today_sentence_with_index(sentences):
        today_str = date.today().isoformat()
        random.seed(today_str)
        index = random.randint(0, len(sentences) - 1)
        return sentences[index], index
    sentence, idx = get_today_sentence_with_index(sentences)

    send_to_discord(sentence, idx, total)

if __name__ == "__main__":
    main()
