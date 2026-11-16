import os, secrets
from pathlib import Path
from fastapi import Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from dotenv import load_dotenv
from setup_api import app
from common import GitHubJSON
import httpx

load_dotenv()
ROOT=Path(__file__).resolve().parent.parent
def serializer():
    secret=os.getenv("CLASS29_SECRET_KEY")
    if not secret: raise RuntimeError("CLASS29_SECRET_KEY is not configured")
    return URLSafeTimedSerializer(secret,salt="class29-private-site")
def valid_cookie(value):
    try:
        data=serializer().loads(value,max_age=60*60*24*14)
        return data.get("user")=="owner"
    except (BadSignature,SignatureExpired,Exception):
        return False

@app.middleware("http")
async def require_owner(request:Request,call_next):
    path=request.url.path
    if path in ("/login","/auth/login","/health") or path.startswith("/favicon"):
        return await call_next(request)
    if not valid_cookie(request.cookies.get("class29_auth","")):
        if path.startswith("/api/") or path.startswith("/auth/"):
            return JSONResponse({"detail":"Please sign in to your private Class 29 library."},status_code=401)
        return RedirectResponse("/login",status_code=303)
    return await call_next(request)

@app.get("/login")
async def login_page():
    return FileResponse(ROOT/"login.html")

@app.post("/auth/login")
async def owner_login(request:Request):
    body=await request.json()
    expected=os.getenv("CLASS29_PASSWORD","")
    supplied=str(body.get("password",""))
    if len(expected)<16 or not secrets.compare_digest(supplied,expected):
        raise HTTPException(401,"Incorrect password.")
    response=JSONResponse({"ok":True})
    response.set_cookie("class29_auth",serializer().dumps({"user":"owner"}),httponly=True,secure=True,samesite="strict",max_age=60*60*24*14,path="/")
    return response

@app.post("/auth/logout")
async def owner_logout():
    response=JSONResponse({"ok":True})
    response.delete_cookie("class29_auth",path="/")
    return response

@app.get("/api/classes")
async def private_classes():
    writer=GitHubJSON()
    async with httpx.AsyncClient(timeout=30) as client:
        data,_=await writer.read(client)
    return data

@app.get("/health")
async def private_health():
    return {"ok":True}

app.mount("/",StaticFiles(directory=str(ROOT),html=True),name="private-site")
