
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8130338207:AAE-a-t1HKjKDxxu9xmUG98-nfYulRVCDcU"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚗 Рассчитать авто (Aleado)")],
    ],
    resize_keyboard=True
)

class CarSearch(StatesGroup):
    waiting_for_make = State()
    waiting_for_model = State()
    waiting_for_year_from = State()
    waiting_for_year_to = State()

# --- Заглушка парсера Aleado ---
def fake_parse_aleado_stats(make, model, year_from, year_to):
    # Имитация парсинга Aleado
    example_data = [
        {"дата": "2024-06-01", "оценка": "4", "цена": 580000},
        {"дата": "2024-06-04", "оценка": "3.5", "цена": 610000},
        {"дата": "2024-06-08", "оценка": "4", "цена": 595000},
        {"дата": "2024-06-12", "оценка": "4.5", "цена": 620000},
        {"дата": "2024-06-15", "оценка": "3.5", "цена": 570000},
    ]
    средняя = int(sum(x["цена"] for x in example_data) / len(example_data))
    return example_data, средняя

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Привет! Я помогу рассчитать стоимость авто по статистике Aleado. Нажми кнопку ниже 👇", reply_markup=menu)

@dp.message(lambda message: message.text == "🚗 Рассчитать авто (Aleado)")
async def start_car_search(message: Message, state: FSMContext):
    await message.answer("Введите марку автомобиля (например, Honda):")
    await state.set_state(CarSearch.waiting_for_make)

@dp.message(CarSearch.waiting_for_make)
async def car_make_received(message: Message, state: FSMContext):
    await state.update_data(make=message.text)
    await message.answer("Введите модель автомобиля (например, Civic):")
    await state.set_state(CarSearch.waiting_for_model)

@dp.message(CarSearch.waiting_for_model)
async def car_model_received(message: Message, state: FSMContext):
    await state.update_data(model=message.text)
    await message.answer("Введите год ОТ:")
    await state.set_state(CarSearch.waiting_for_year_from)

@dp.message(CarSearch.waiting_for_year_from)
async def car_year_from_received(message: Message, state: FSMContext):
    await state.update_data(year_from=message.text)
    await message.answer("Введите год ДО:")
    await state.set_state(CarSearch.waiting_for_year_to)

@dp.message(CarSearch.waiting_for_year_to)
async def car_year_to_received(message: Message, state: FSMContext):
    data = await state.update_data(year_to=message.text)
    await state.clear()

    make = data['make']
    model = data['model']
    year_from = data['year_from']
    year_to = data['year_to']

    await message.answer(
        f"<b>🔍 Поиск:</b>\nМарка: {make}\nМодель: {model}\nГод: {year_from}–{year_to}\n\nПарсим Aleado..."
    )

    results, avg_price = fake_parse_aleado_stats(make, model, year_from, year_to)

    text = "<b>📊 Последние продажи:</b>\n\n"
    for r in results:
        text += f"{r['дата']}: оценка {r['оценка']}, цена {r['цена']:,} ¥\n"
    text += f"\n<b>Средняя цена:</b> {avg_price:,} ¥"

    await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
