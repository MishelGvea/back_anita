from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, verificacion, totp  # ← Agregar totp

app = FastAPI(title="Sistema de Autenticación")

# 🚨 Asegúrate de incluir AMBOS (localhost y 127.0.0.1)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router, prefix="/api/auth", tags=["autenticacion"])
app.include_router(verificacion.router, prefix="/api/verificacion", tags=["verificacion"])
app.include_router(totp.router)  # ← El router ya tiene prefix="/api/totp"

@app.get("/")
def read_root():
    return {"message": "API de autenticación funcionando"}