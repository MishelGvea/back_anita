from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, verificacion

app = FastAPI(title="Sistema de Autenticación")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["autenticacion"])
app.include_router(verificacion.router, prefix="/api/verificacion", tags=["verificacion"])

@app.get("/")
def read_root():
    return {"message": "API de autenticación funcionando"}