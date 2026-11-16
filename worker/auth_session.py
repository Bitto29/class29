import asyncio,os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
load_dotenv()
async def main():
 c=TelegramClient(StringSession(),int(os.environ['TELEGRAM_API_ID']),os.environ['TELEGRAM_API_HASH'])
 await c.start(phone=os.getenv('TELEGRAM_PHONE'))
 print('Copy this session into the private TELEGRAM_SESSION secret. Never publish it:\n')
 print(c.session.save())
 await c.disconnect()
if __name__=='__main__':asyncio.run(main())
