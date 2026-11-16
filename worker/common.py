import os,re,json,base64,asyncio
from datetime import datetime,timezone
from urllib.parse import urlparse
import httpx
from dotenv import load_dotenv
load_dotenv()

YT=re.compile(r'(?:https?://)?(?:www\\.|m\\.)?(?:youtube\\.com/(?:watch\\?v=|shorts/|live/)|youtu\\.be/)([A-Za-z0-9_-]{11})',re.I)
URL=re.compile(r'https?://[^\\s<>\\])}]+',re.I)

def env(k):
 v=os.getenv(k)
 if not v: raise RuntimeError('Missing environment variable: '+k)
 return v

def configured_groups():
 raw=env('TELEGRAM_GROUPS_JSON')
 groups=json.loads(raw)
 if not isinstance(groups,list) or not groups: raise RuntimeError('TELEGRAM_GROUPS_JSON must be a non-empty JSON array')
 clean=[]
 for item in groups:
  if not isinstance(item,dict) or 'id' not in item: raise RuntimeError('Each group needs an id and optional name')
  clean.append({'id':int(item['id']),'name':str(item.get('name') or item['id'])})
 return clean

def video_ids(text):
 return list(dict.fromkeys(YT.findall(text or '')))

def extract_links(message):
 text=message.message or ''
 found=[]
 for raw in URL.findall(text):
  u=raw.rstrip('.,;:!?')
  if u not in found and not YT.search(u): found.append(u)
 for entity in (message.entities or []):
  u=getattr(entity,'url',None)
  if u and u not in found and not YT.search(u): found.append(u)
 return [{'url':u,'label':resource_label(u)} for u in found]

def resource_label(url):
 host=urlparse(url).netloc.lower()
 if 'drive.google.com' in host: return 'Google Drive'
 if 'docs.google.com' in host: return 'Google Slides / Docs'
 if urlparse(url).path.lower().endswith('.pdf'): return 'PDF'
 return host or 'Resource'

def now(): return datetime.now(timezone.utc).isoformat()

class GitHubJSON:
 def __init__(self):
  self.token=env('GITHUB_TOKEN');self.repo=env('GITHUB_REPOSITORY');self.branch=os.getenv('GITHUB_BRANCH','main');self.path=os.getenv('DATA_PATH','data/classes.json')
  self.url='https://api.github.com/repos/'+self.repo+'/contents/'+self.path
  self.headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}

 async def read(self,c):
  r=await c.get(self.url,headers=self.headers,params={'ref':self.branch})
  if r.status_code==404:return {'version':2,'updated_at':None,'groups':[]},None
  r.raise_for_status();p=r.json();data=json.loads(base64.b64decode(p['content']).decode())
  data.setdefault('groups',[])
  return data,p['sha']

 async def add(self,group_id,group_name,topic,title,vid,resources,date,msgid):
  async with httpx.AsyncClient(timeout=30) as c:
   for attempt in range(5):
    data,sha=await self.read(c);groups=data.setdefault('groups',[])
    group=next((x for x in groups if str(x.get('id'))==str(group_id)),None)
    if group is None:group={'id':str(group_id),'name':group_name,'topics':[]};groups.append(group)
    group['name']=group_name or group.get('name') or str(group_id)
    topics=group.setdefault('topics',[])
    section=next((x for x in topics if x.get('name','').casefold()==topic.casefold()),None)
    if section is None:section={'name':topic,'classes':[]};topics.append(section)
    key=str(group_id)+':'+str(msgid)+':'+(vid or 'links')
    if any(x.get('source_key')==key for t in topics for x in t.get('classes',[])):return False
    item={'id':'cv-'+re.sub(r'[^a-zA-Z0-9_-]','-',key),'source_key':key,'title':title or ('Class '+vid if vid else 'Class materials'),'topic':topic,'date':date.isoformat() if date else now(),'telegram_message_id':msgid,'resources':resources or []}
    if vid:
     item.update({'video_id':vid,'url':'https://www.youtube.com/watch?v='+vid})
    section.setdefault('classes',[]).append(item)
    for t in topics:t['classes'].sort(key=lambda x:x.get('date',''),reverse=True)
    topics.sort(key=lambda x:x.get('name','').casefold());groups.sort(key=lambda x:x.get('name','').casefold())
    data['version']=2;data['updated_at']=now()
    body={'message':'Sync Telegram class materials','content':base64.b64encode(json.dumps(data,ensure_ascii=False,indent=2).encode()).decode(),'branch':self.branch}
    if sha:body['sha']=sha
    r=await c.put(self.url,headers=self.headers,json=body)
    if r.status_code in (409,422) and attempt<4:await asyncio.sleep(.7*(attempt+1));continue
    r.raise_for_status();print('Synced',key,'to',group_name,'/',topic);return True
  raise RuntimeError('GitHub JSON update failed after retries')
