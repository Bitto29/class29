import asyncio,os
from telethon import TelegramClient,events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetForumTopicsRequest
from common import env,GitHubJSON,video_ids
async def main():
 c=TelegramClient(StringSession(env('TELEGRAM_SESSION')),int(env('TELEGRAM_API_ID')),env('TELEGRAM_API_HASH'))
 await c.start(phone=os.getenv('TELEGRAM_PHONE'));group=await c.get_entity(int(env('TELEGRAM_GROUP_ID')))
 writer=GitHubJSON();result=await c(GetForumTopicsRequest(channel=group,offset_date=None,offset_id=0,offset_topic=0,limit=100))
 topic_names={t.id:t.title for t in result.topics}
 @c.on(events.NewMessage(chats=group))
 async def handler(event):
  m=event.message;ids=video_ids(m.message or '')
  if not ids:return
  top=getattr(m,'reply_to_top_id',None) or getattr(m,'reply_to_msg_id',None)
  topic=topic_names.get(top,'General')
  lines=(m.message or '').strip().splitlines();title=lines[0][:140] if lines else 'Class in '+topic
  for vid in ids:
   try:await writer.add(topic,title,vid,m.date,m.id)
   except Exception as e:print('Sync error:',e)
 print('ClassVault listener active. Waiting for new Telegram classes…')
 await c.run_until_disconnected()
if __name__=='__main__':asyncio.run(main())
