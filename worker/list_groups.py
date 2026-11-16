import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from common import env

async def main():
 c=TelegramClient(StringSession(env('TELEGRAM_SESSION')),int(env('TELEGRAM_API_ID')),env('TELEGRAM_API_HASH'))
 await c.start()
 try:
  async for d in c.iter_dialogs():
   entity=d.entity
   if getattr(entity,'megagroup',False) or getattr(entity,'forum',False):
    print(f"{d.name}\t{entity.id}\tforum={bool(getattr(entity,'forum',False))}")
 finally:await c.disconnect()

if __name__=='__main__':asyncio.run(main())
