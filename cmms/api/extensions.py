from fastapi import FastAPI
from fastapi_login import LoginManager
from fastapi.middleware.cors import CORSMiddleware
from cmms.config import SECRET_KEY


app = FastAPI()
login_manager = LoginManager(SECRET_KEY, token_url='/auth/token')

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

