import asyncio,os
from telethon import TelegramClient,events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import GetForumTopicsRequest
from common import env,configured_groups,GitHubJSON,video_ids,extract_links

async def main():
 c=TelegramClient(StringSession(env('TELEGRAM_SESSION')),int(env('TELEGRAM_API_ID')),env('TELEGRAM_API_HASH'))
 await c.start(phone=os.getenv('TELEGRAM_PHONE'));writer=GitHubJSON()
 try:
  for cfg in configured_groups():
   group=await c.get_entity(cfg['id']);name=cfg['name']
   topics={};offset=0
   while True:
    result=await c(GetForumTopicsRequest(channel=group,offset_date=None,offset_id=0,offset_topic=offset,limit=100))
    batch=result.topics or []
    for t in batch:topics[t.id]=t.title
    if len(batch)<100:break
    offset=batch[-1].id
   print('Watching',name,'with',len(topics),'topics')
   async def handler(event, group_id=cfg['id'], group_name=name, topic_map=topics):
    m=event.message;text=m.message or '';ids=video_ids(text);resources=extract_links(m)
    if not ids and not resources:return
    top=getattr(m,'reply_to_top_id',None) or getattr(m,'reply_to_msg_id',None)
    topic=topic_map.get(top,'General')
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    title=(lines[0][:140] if lines else 'Class materials')
    try:
     if ids:
      for vid in ids:await writer.add(group_id,group_name,topic,title,vid,resources,m.date,m.id)
     else:await writer.add(group_id,group_name,topic,title,None,resources,m.date,m.id)
    except Exception as e:print('Sync error:',group_name,topic,e)
   c.add_event_handler(handler,events.NewMessage(chats=group))
  print('ClassVault multi-group listener active. Waiting for new class links…')
  await c.run_until_disconnected()
 finally:await c.disconnect()

if __name__=='__main__':asyncio.run(main())
