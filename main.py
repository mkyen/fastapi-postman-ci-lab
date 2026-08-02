"""
Minimal FastAPI + JWT lab project.
Single file, SQLite, no complex package structure — built specifically
so it just runs, for practicing Postman (Collections, Environment
Variables, Authorization/JWT automation).

Run:
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/docs to see all endpoints.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ── Config (normally in app/core/config.py, kept inline here on purpose) ──
SECRET_KEY = "lab-secret-key-change-in-real-projects"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── Database ───────────────────────────────────────────────────────────
engine = create_engine("sqlite:///./lab.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ────────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    title: str
    done: bool = False


# ── Password / JWT helpers ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_error
    return user


# ── App ────────────────────────────────────────────────────────────────
app = FastAPI(title="Lab API", version="1.0.0")


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


@app.post("/auth/register", tags=["auth"], status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token(subject=user.email)
    return Token(access_token=token)


@app.get("/users/me", tags=["users"])
def read_current_user(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email}


# ── A simple protected resource, to give Postman something extra to hit ──
_fake_tasks_db: list[dict] = []


@app.post("/tasks", tags=["tasks"], status_code=201)
def create_task(payload: TaskCreate, current_user: User = Depends(get_current_user)):
    task = {"id": len(_fake_tasks_db) + 1, "owner": current_user.email, **payload.model_dump()}
    _fake_tasks_db.append(task)
    return task


@app.get("/tasks", tags=["tasks"])
def list_tasks(current_user: User = Depends(get_current_user)):
    return [t for t in _fake_tasks_db if t["owner"] == current_user.email]