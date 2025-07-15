import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv("1.env")
API_TOKEN = os.getenv("BOT_TOKEN")
PHPSESSID = os.getenv("PHPSESSID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

session = requests.Session()
session.cookies.set("PHPSESSID", PHPSESSID)

class Form(StatesGroup):
    brand = State()
    model = State()
    body = State()
    year_from = State()
    year_to = State()

def fetch_makes_from_aleado():
    url = "https://auctions.aleado.ru/stats/?p=project/searchform&searchtype=max"
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    select = soup.find("select", {"name": "mrk"})
    makes = {}
    for option in select.find_all("option"):
        val = option.get("value")
        name = option.text.strip().split("
")[0]
        if val and val.isdigit():
            makes[name.upper()] = val
    return makes

def fetch_models_by_make(make_id):
    url = "https://auctions.aleado.ru/stats/?p=project/getmodels"
    response = session.post(url, data={'mrk': make_id})
    soup = BeautifulSoup(response.text, 'lxml')
    select = soup.find("select", {"name": "mdl"})
    models = {}
    if select:
        for option in select.find_all("option"):
            val = option.get("value")
            name = option.text.strip().split("
")[0]
            if val and val.isdigit():
                models[name.upper()] = val
    return models

def fetch_stats(make_id, model_id, body, year_from, year_to):
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
    if body != "0":
        data['type'] = body
    response = session.post(url, data=data)
    soup = BeautifulSoup(response.text, 'lxml')
    avg = soup.find("b", string="Средняя цена:")
    return avg.next_sibling.strip() if avg and avg.next_sibling else "не найдена"

@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Привет! Напиши на английском только марку, например: Honda")
    await state.set_state(Form.brand)

@dp.message(Form.brand)
async def get_brand(message: Message, state: FSMContext):
    await state.update_data(brand=message.text.strip().upper())
    await message.answer("Теперь напишите модель английскими буквами без ошибок")
    await state.set_state(Form.model)

@dp.message(Form.model)
async def get_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text.strip().upper())
    await message.answer("Напишите марку кузова. Если не знаете — напишите 0")
    await state.set_state(Form.body)

@dp.message(Form.body)
async def get_body(message: Message, state: FSMContext):
    await state.update_data(body=message.text.strip())
    await message.answer("Введите ГОД ОТ (например: 2021)")
    await state.set_state(Form.year_from)

@dp.message(Form.year_from)
async def get_year_from(message: Message, state: FSMContext):
    await state.update_data(year_from=message.text.strip())
    await message.answer("Теперь введите ГОД ДО (например: 2023)")
    await state.set_state(Form.year_to)

@dp.message(Form.year_to)
async def get_year_to(message: Message, state: FSMContext):
    data = await state.update_data(year_to=message.text.strip())
    try:
        makes = fetch_makes_from_aleado()
        make_id = makes.get(data["brand"])
        if not make_id:
            await message.answer("Марка не найдена.")
            return
        models = fetch_models_by_make(make_id)
        model_id = models.get(data["model"])
        if not model_id:
            await message.answer("Модель не найдена.")
            return
        avg = fetch_stats(make_id, model_id, data["body"], data["year_from"], data["year_to"])
        await message.answer(f"<b>Средняя цена:</b> {avg} иен")
    except Exception as e:
        logging.exception("Ошибка при обработке запроса")
        await message.answer("Произошла ошибка, попробуйте ещё раз.")
    finally:
        await state.clear()

if __name__ == "__main__":
    import asyncio
    from aiogram import Router
    router = Router()
    dp.include_router(router)
    asyncio.run(dp.start_polling(bot))
