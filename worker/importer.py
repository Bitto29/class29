import asyncio,os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetForumTopicsRequest
from common import env,GitHubJSON,video_ids
async def main():
 c=TelegramClient(StringSession(env('TELEGRAM_SESSION')),int(env('TELEGRAM_API_ID')),env('TELEGRAM_API_HASH'))
 await c.start(phone=os.getenv('TELEGRAM_PHONE'));group=await c.get_entity(int(env('TELEGRAM_GROUP_ID')))
 writer=GitHubJSON();topics=[];offset=0
 while True:
  result=await c(GetForumTopicsRequest(channel=group,offset_date=None,offset_id=0,offset_topic=offset,limit=100))
  batch=result.topics or [];topics.extend(batch)
  if len(batch)<100:break
  offset=batch[-1].id
 print('Forum topics found:',len(topics))
 for topic in topics:
  async for m in c.iter_messages(group,reply_to=topic.id,reverse=True):
   ids=video_ids(m.message or '')
   if not ids:continue
   lines=(m.message or '').strip().splitlines()
   title=(lines[0][:140] if lines else 'Class in '+topic.title)
   for vid in ids:await writer.add(topic.title,title,vid,m.date,m.id)
 await c.disconnect()
if __name__=='__main__':asyncio.run(main())
