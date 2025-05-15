import os
import time
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.ext import Updater, CommandHandler

BOT_TOKEN = os.getenv('BOT_TOKEN', '7611196549:AAFxMskGafTFhKesiA6HKP5AtUYqHhsaXLk')
USERNAMES = os.getenv('USERNAMES', 'senya_070,grafit66').split(',')

bot = Bot(token=BOT_TOKEN)

previous_odds = {}

def start(update, context):
    update.message.reply_text("Привет! Я буду уведомлять тебя о резком падении коэффициентов на победу и тотал.")

def fetch_odds():
    url = 'https://www.oddsportal.com/inplay-odds/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        odds_data = {}

        # В oddsportal коэффициенты расположены в таблицах с классом "table-main"
        # Найдем все матчи
        matches = soup.select('.table-main tr.deactivate')
        for match in matches:
            cells = match.find_all('td')
            if len(cells) < 5:
                continue
            match_name = cells[1].get_text(strip=True)

            # Коэффициенты для победы (обычно 1х2) - берём первый коэффициент после названия команды
            try:
                win_odd = float(cells[2].get_text(strip=True))
            except:
                win_odd = None
            
            # Коэффициент тотала может быть в другом столбце или нужно точнее смотреть, для простоты возьмём 3-й и 4-й коэффициенты
            try:
                total_odd_1 = float(cells[3].get_text(strip=True))
                total_odd_2 = float(cells[4].get_text(strip=True))
            except:
                total_odd_1 = None
                total_odd_2 = None

            # Сохраним если есть коэффициенты
            if win_odd:
                odds_data[f"{match_name} - Победа"] = win_odd
            if total_odd_1:
                odds_data[f"{match_name} - Тотал 1"] = total_odd_1
            if total_odd_2:
                odds_data[f"{match_name} - Тотал 2"] = total_odd_2

        return odds_data

    except Exception as e:
        print(f"Ошибка при получении коэффициентов: {e}")
        return {}

def check_odds_and_notify():
    global previous_odds
    current_odds = fetch_odds()
    for key, odd in current_odds.items():
        prev_odd = previous_odds.get(key)
        if prev_odd:
            # Проверяем резкое падение >= 20%
            if (prev_odd - odd) / prev_odd >= 0.2:
                message = f"⚠️ Коэффициент '{key}' упал с {prev_odd:.2f} до {odd:.2f}!"
                print(message)
                for username in USERNAMES:
                    try:
                        bot.send_message(chat_id='@' + username, text=message)
                    except Exception as e:
                        print(f"Ошибка при отправке сообщению {username}: {e}")
        previous_odds[key] = odd

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    print("Бот запущен. Отслеживаем коэффициенты...")

    while True:
        check_odds_and_notify()
        time.sleep(60)

if __name__ == '__main__':
    main()
