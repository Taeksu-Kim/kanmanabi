from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from .auth import router as auth_router
from .conjugation import router as conjugation_router
from .db import get_db
from .learn import router as learn_router
from .study import router as study_router
from .vocab import router as vocab_router

app = FastAPI(title="korean_helper API")
app.include_router(auth_router)
app.include_router(conjugation_router)
app.include_router(study_router)
app.include_router(learn_router)
app.include_router(vocab_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}
