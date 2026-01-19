# server_fastapi.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import features.plaid.routes as plaid_routes
import features.users.routes as users_routes

load_dotenv(verbose=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=plaid_routes.router)
app.include_router(router=users_routes.router)
