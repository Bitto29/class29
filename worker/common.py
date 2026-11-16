import os,re,json,base64,asyncio
from datetime import datetime,timezone
import httpx
from dotenv import load_dotenv
load_dotenv()
YT=re.compile(r'(?:https?://)?(?:www\\.|m\\.)?(?:youtube\\.com/(?:watch\\?v=|shorts/|live/)|youtu\\.be/)([A-Za-z0-9_-]{11})',re.I)
def env(k):
 v=os.getenv(k)
 if not v: raise RuntimeError('Missing environment variable: '+k)
 return v
def video_ids(text): return list(dict.fromkeys(YT.findall(text or '')))
def now(): return datetime.now(timezone.utc).isoformat()
class GitHubJSON:
 def __init__(self):
  self.token=env('GITHUB_TOKEN');self.repo=env('GITHUB_REPOSITORY');self.branch=os.getenv('GITHUB_BRANCH','main');self.path=os.getenv('DATA_PATH','data/classes.json')
  self.url='https://api.github.com/repos/'+self.repo+'/contents/'+self.path
  self.headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}
 async def read(self,c):
  r=await c.get(self.url,headers=self.headers,params={'ref':self.branch})
  if r.status_code==404:return {'version':1,'updated_at':None,'subjects':[]},None
  r.raise_for_status();p=r.json();return json.loads(base64.b64decode(p['content']).decode()),p['sha']
 async def add(self,subject,title,vid,date,msgid):
  async with httpx.AsyncClient(timeout=30) as c:
   for attempt in range(5):
    data,sha=await self.read(c);groups=data.setdefault('subjects',[])
    group=next((x for x in groups if x.get('name','').casefold()==subject.casefold()),None)
    if group is None:group={'name':subject,'classes':[]};groups.append(group)
    if any(x.get('video_id')==vid for g in groups for x in g.get('classes',[])):return False
    group.setdefault('classes',[]).append({'id':vid,'video_id':vid,'title':title or 'Class '+vid,'topic':subject,'url':'https://www.youtube.com/watch?v='+vid,'date':date.isoformat() if date else now(),'telegram_message_id':msgid})
    for g in groups:g['classes'].sort(key=lambda x:x.get('date',''),reverse=True)
    groups.sort(key=lambda x:x.get('name','').casefold());data['updated_at']=now()
    body={'message':'Sync class '+vid,'content':base64.b64encode(json.dumps(data,ensure_ascii=False,indent=2).encode()).decode(),'branch':self.branch}
    if sha:body['sha']=sha
    r=await c.put(self.url,headers=self.headers,json=body)
    if r.status_code in (409,422) and attempt<4:await asyncio.sleep(.7*(attempt+1));continue
    r.raise_for_status();print('Synced',vid,'to',subject);return True
  raise RuntimeError('GitHub JSON update failed after retries')
