
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
API_TOKEN = os.getenv("8130338207:AAE-a-t1HKjKDxxu9xmUG98-nfYulRVCDcU")
PHPSESSID = os.getenv("rljv1fddgetonpedep92dpjtnh")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

session = requests.Session()
session.cookies.set("PHPSESSID", PHPSESSID)

def fetch_makes_from_aleado(session):
    url = "https://auctions.aleado.ru/stats/?p=project/searchform&searchtype=max"
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')

    select = soup.find("select", {"name": "mrk"})
    makes = {}
    if not select:
        return makes
    for option in select.find_all("option"):
        value = option.get("value")
        text = option.text.strip().split("\n")[0]
        if value and value.isdigit():
            makes[text.upper()] = value
    return makes

def fetch_models_by_make(session, make_id):
    url = "https://auctions.aleado.ru/stats/?p=project/getmodels"
    response = session.post(url, data={'mrk': make_id})
    soup = BeautifulSoup(response.text, 'lxml')

    select = soup.find('select', {'name': 'mdl'})
    if not select:
        return {}

    options = select.find_all('option')
    models = {}
    for option in options:
        value = option.get('value')
        text = option.text.strip().split('\n')[0]
        if value and value.isdigit():
            models[text.upper()] = value
    return models

def fetch_stats(make_id, model_id, year_from, year_to):
    url = "https://auctions.aleado.ru/stats/?p=project/findlots&s&ld"
    today = datetime.now()
    data = {
        'mrk': make_id,
        'mdl': model_id,
        'result': 1,
        'year1': year_from,
        'year2': year_to,
        'sday': '01',
        'smonth': '01',
        'syear': '2021',
        'fday': today.strftime("%d"),
        'fmonth': today.strftime("%m"),
        'fyear': today.strftime("%Y"),
    }
    response = session.post(url, data=data)
    soup = BeautifulSoup(response.text, 'lxml')
    average_price = soup.find('b', string='Средняя цена:')
    if average_price and average_price.next_sibling:
        return average_price.next_sibling.strip()
    return "не найдена"

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Введи марку и модель, например: \n\n`Honda Civic`", parse_mode="Markdown")

@dp.message_handler()
async def handle_query(message: types.Message):
    try:
        parts = message.text.upper().split()
        if len(parts) < 2:
            await message.reply("Введите и марку, и модель. Например: `Honda Fit`", parse_mode="Markdown")
            return

        brand, model = parts[0], " ".join(parts[1:])
        makes = fetch_makes_from_aleado(session)
        make_id = makes.get(brand)
        if not make_id:
            await message.reply(f"Марка {brand} не найдена.")
            return

        models = fetch_models_by_make(session, make_id)
        model_id = models.get(model)
        if not model_id:
            await message.reply(f"Модель {model} не найдена.")
            return

        await message.reply("Считаю среднюю цену, подожди...")
        avg_price = fetch_stats(make_id, model_id, 2021, 2023)
        await message.reply(f"Средняя цена на {brand} {model} (2021–2023): {avg_price}")
    except Exception as e:
        logging.exception("Ошибка при обработке запроса")
        await message.reply("Произошла ошибка. Попробуй еще раз.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
