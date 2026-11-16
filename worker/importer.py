import asyncio,os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetForumTopicsRequest
from common import env,configured_groups,GitHubJSON,video_ids,extract_links

async def get_topics(c,group):
 topics=[];offset=0
 while True:
  result=await c(GetForumTopicsRequest(channel=group,offset_date=None,offset_id=0,offset_topic=offset,limit=100))
  batch=result.topics or [];topics.extend(batch)
  if len(batch)<100:break
  offset=batch[-1].id
 return topics

async def main():
 c=TelegramClient(StringSession(env('TELEGRAM_SESSION')),int(env('TELEGRAM_API_ID')),env('TELEGRAM_API_HASH'))
 await c.start(phone=os.getenv('TELEGRAM_PHONE'));writer=GitHubJSON()
 try:
  for cfg in configured_groups():
   group=await c.get_entity(cfg['id']);name=cfg['name']
   topics=await get_topics(c,group)
   print('Importing',name,'topics:',len(topics))
   for topic in topics:
    async for m in c.iter_messages(group,reply_to=topic.id,reverse=True):
     text=m.message or '';ids=video_ids(text);resources=extract_links(m)
     if not ids and not resources:continue
     lines=[x.strip() for x in text.splitlines() if x.strip()]
     title=(lines[0][:140] if lines else 'Class in '+topic.title)
     if ids:
      for vid in ids:await writer.add(cfg['id'],name,topic.title,title,vid,resources,m.date,m.id)
     else:
      await writer.add(cfg['id'],name,topic.title,title,None,resources,m.date,m.id)
   print('Finished:',name)
 finally:await c.disconnect()

if __name__=='__main__':asyncio.run(main())
