# server_fastapi.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from db.database import Base, engine
from routers import plaid, auth
import db.models

load_dotenv(verbose=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=plaid.router)
app.include_router(router=auth.router)

# Make sure tables exist
print(">>> Creating tables now")
Base.metadata.create_all(bind=engine)