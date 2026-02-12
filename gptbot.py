import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from openai import AsyncClient

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError

# Bot token can be obtained via https://t.me/BotFather
TOKEN =""
AI_TOKEN = ""
# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()
user_history = {}

client = AsyncClient(
    base_url="https://openrouter.ai/api/v1",
    api_key=AI_TOKEN,
    )


@retry(
    stop=stop_after_attempt(5),  # 5 попыток
    wait=wait_exponential(multiplier=1, min=2, max=10),  # экспоненциальная задержка
    retry=retry_if_exception_type(RateLimitError)  # только для 429 ошибок
)

async def openai_generate(user_id: int, prompt: str) -> str:
    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model="openai/gpt-4.1-nano",  # или твоя модель
        messages=user_history[user_id],
        extra_body={}
    )
    
    reply = response.choices[0].message.content

    user_history[user_id].append({"role": "assistant", "content": reply})
    return reply




@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_id = message.from_user.id
    if user_id in user_history:
        del user_history[user_id]
    await message.answer(f"Привет, это бот и я создан для того, чтобы подсказывать! \n"
                         f"Напиши любое сообщение")


@dp.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "Я ещё маленький бот и много команд не знаю.\n"
        "Но я очень умный, потому что я нейросеть!\n\n"
        "Просто напиши что-нибудь — я отвечу.\n"
        "А /start — начать диалог заново."
    )


@dp.message()
async def echo_handler(message: Message) -> None:
        msg = await message.answer("Нейросеть генерирует...")
        response = await openai_generate(message.from_user.id, message.text)
        await msg.delete()
        await message.answer(f'{response}')


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=None))

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

    