import asyncio
import json
import os
from pprint import pprint
import time

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart
from dotenv import load_dotenv
import websockets

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = os.getenv("USER_ID")

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()

binance_url = "wss://fstream.binance.com/ws/btcusdt@aggTrade"
binance_multisteram_url = "wss://fstream.binance.com/stream?streams=btcusdt@aggTrade/ethusdt@aggTrade"

btcstream = 'btcusdt@aggTrade'
ethstream = 'ethusdt@aggTrade'

last_send_time = 0
is_eth_received = False
is_btc_received = False


async def get_user_id(message: Message):
    user_id = message.from_user.id
    return user_id


@dp.message(CommandStart())
async def get_start(message: Message):
    user_id =  message.from_user.id
    await message.answer(f"{user_id=}")
    

async def fetch_binance_trades(url: str):
    global last_send_time
    global is_eth_received
    global is_btc_received
    async with websockets.connect(url) as ws:
        async for msg in ws:
            msg_dict = json.loads(msg)
            data = msg_dict["data"]
            stream = msg_dict["stream"]
            price = data["p"]
            if stream == ethstream:
                msg_eth = f"Current price ETH/USDT: {price}"
                is_eth_received = True
            elif stream == btcstream:
                msg_btc = f"Current price BTC/USDT: {price}"
                is_btc_received = True
            if is_eth_received and is_btc_received:
                if time.time() - last_send_time > 5:
                    await send_message_to_tg(
                        msg=msg_eth+'\n'+msg_btc
                    )
                    is_eth_received = False
                    is_btc_received = False
                    last_send_time = time.time()
                    
            
            
async def send_message_to_tg(msg: str):
    await bot.send_message(
        chat_id=USER_ID,
        text=msg,
    )
            
            
async def main():
    async with asyncio.TaskGroup() as taskgroup:
        taskgroup.create_task(fetch_binance_trades(binance_multisteram_url))
        taskgroup.create_task(dp.start_polling(bot, handle_signals=False))
    # await fetch_binance_trades(binance_multisteram_url)
    # await dp.start_polling(bot)
    
    
if __name__ == "__main__":
    asyncio.run(main())