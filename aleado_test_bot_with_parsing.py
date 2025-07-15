
import os
import logging
import asyncio
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv("1.env")
API_TOKEN = os.getenv("API_TOKEN")
PHPSESSID = os.getenv("PHPSESSID")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

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


from aiogram.filters import Command

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Введи марку и модель, например:\n\n<b>Honda Civic</b>")


@dp.message()
async def handle_query(message: types.Message):
    try:
        parts = message.text.upper().split()
        if len(parts) < 2:
            await message.answer("Введите и марку, и модель. Например: <b>Honda Fit</b>")
            return

        brand, model = parts[0], " ".join(parts[1:])
        makes = fetch_makes_from_aleado(session)
        make_id = makes.get(brand)
        if not make_id:
            await message.answer(f"Марка <b>{brand}</b> не найдена.")
            return

        models = fetch_models_by_make(session, make_id)
        model_id = models.get(model)
        if not model_id:
            await message.answer(f"Модель <b>{model}</b> не найдена.")
            return

        await message.answer("Считаю среднюю цену, подожди...")
        avg_price = fetch_stats(make_id, model_id, 2021, 2023)
        await message.answer(f"Средняя цена на <b>{brand} {model}</b> (2021–2023): <b>{avg_price}</b>")
    except Exception as e:
        logging.exception("Ошибка при обработке запроса")
        await message.answer("Произошла ошибка. Попробуй еще раз.")


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
