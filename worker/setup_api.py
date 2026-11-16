import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

load_dotenv()
app=FastAPI(title="Class 29 Private Library")
pending={}
def guard(k):
    # All routes in this app are protected by the signed owner cookie middleware in private_app.py.
    return None
def creds():
    try:return int(os.environ["TELEGRAM_API_ID"]),os.environ["TELEGRAM_API_HASH"]
    except Exception:raise HTTPException(500,"Set TELEGRAM_API_ID and TELEGRAM_API_HASH in the Render service first.")
class Start(BaseModel):
    phone:str
class Verify(BaseModel):
    phone:str
    code:str
    password:str=""
@app.get("/health")
def health():return {"ok":True}
@app.post("/health")
def health_post(x_setup_key:str=Header(default="")):
    guard(x_setup_key);return {"ok":True}
@app.post("/auth/start")
async def auth_start(data:Start,x_setup_key:str=Header(default="")):
    guard(x_setup_key)
    api_id,api_hash=creds()
    phone=data.phone.strip()
    if not phone.startswith("+"):raise HTTPException(400,"Use the full phone number with country code.")
    old=pending.pop(phone,None)
    if old:
        try:await old["client"].disconnect()
        except:pass
    client=TelegramClient(StringSession(),api_id,api_hash)
    await client.connect()
    try:
        sent=await client.send_code_request(phone)
        pending[phone]={"client":client,"hash":sent.phone_code_hash}
        return {"sent":True}
    except Exception as e:
        await client.disconnect()
        raise HTTPException(400,str(e))
@app.post("/auth/verify")
async def auth_verify(data:Verify,x_setup_key:str=Header(default="")):
    guard(x_setup_key)
    item=pending.get(data.phone)
    if not item:raise HTTPException(400,"Request a fresh login code first.")
    c=item["client"]
    try:
        try:await c.sign_in(data.phone,data.code,phone_code_hash=item["hash"])
        except SessionPasswordNeededError:
            if not data.password:raise HTTPException(401,"This account needs its 2-Step Verification password.")
            await c.sign_in(password=data.password)
        dialogs=await c.get_dialogs(limit=None)
        groups=[]
        for d in dialogs:
            e=d.entity
            if getattr(e,"megagroup",False):
                groups.append({"id":int("-100"+str(e.id)),"title":d.name,"forum":bool(getattr(e,"forum",False))})
        session=c.session.save()
        pending.pop(data.phone,None)
        await c.disconnect()
        return {"session":session,"groups":groups}
    except HTTPException:raise
    except Exception as e:raise HTTPException(400,str(e))
