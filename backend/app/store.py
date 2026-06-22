"""Persistence for episodes and their artifacts (SQLAlchemy 2.0).

DATABASE_URL drives the backend: SQLite for local/tests, Postgres (Neon) in prod.
Same public ``Store`` contract as Phase 1 (docs/PLAN.md 1.2) — five methods over an
``episodes`` row plus a key/value ``artifacts`` table holding JSON blobs — so the
fixture-first endpoints and their regression tests are unaffected by the engine swap.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Optional

from sqlalchemy import JSON, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)

DEFAULT_DATABASE_URL = "sqlite:///./circle_take.db"


def _normalize_url(arg: Optional[str]) -> str:
    """Turn a DATABASE_URL / bare path into a SQLAlchemy URL.

    - ``None`` -> env ``DATABASE_URL`` or the local SQLite default.
    - bare filesystem path (tests pass ``tempfile`` paths) -> ``sqlite:///`` URL.
    - Neon-style ``postgres://`` / ``postgresql://`` -> pinned ``+psycopg`` driver.
    """
    url = arg or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL
    if "://" not in url:  # bare path -> sqlite (absolute needs 4 slashes)
        return "sqlite:////" + url.lstrip("/") if os.path.isabs(url) else "sqlite:///" + url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


class Base(DeclarativeBase):
    pass


class Episode(Base):
    __tablename__ = "episodes"

    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    state: Mapped[str]
    user_id: Mapped[Optional[str]] = mapped_column(default=None, index=True)


class Artifact(Base):
    __tablename__ = "artifacts"

    episode_id: Mapped[str] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]


def _user_dict(u: Optional[User]) -> Optional[dict]:
    if u is None:
        return None
    return {"id": u.id, "email": u.email, "password_hash": u.password_hash}


class Store:
    def __init__(self, db_path_or_url: Optional[str] = None):
        url = _normalize_url(db_path_or_url)
        # SQLite + FastAPI TestClient/uvicorn can touch a connection across threads.
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, connect_args=connect_args, future=True)
        self._Session = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    def _session(self) -> Session:
        return self._Session()

    def create_episode(
        self, title: str, state: str, user_id: Optional[str] = None
    ) -> str:
        eid = "ep" + uuid.uuid4().hex[:8]
        with self._session() as s:
            s.add(Episode(id=eid, title=title, state=state, user_id=user_id))
            s.commit()
        return eid

    def get_episode(self, eid: str) -> Optional[dict]:
        with self._session() as s:
            ep = s.get(Episode, eid)
            if ep is None:
                return None
            arts = {
                a.key: a.value
                for a in s.scalars(select(Artifact).where(Artifact.episode_id == eid))
            }
            return {
                "episode_id": ep.id,
                "title": ep.title,
                "state": ep.state,
                "user_id": ep.user_id,
                "artifacts": arts,
            }

    def list_episodes(self, user_id: str) -> list[dict]:
        with self._session() as s:
            eps = s.scalars(
                select(Episode).where(Episode.user_id == user_id).order_by(Episode.id)
            )
            return [
                {
                    "episode_id": ep.id,
                    "title": ep.title,
                    "state": ep.state,
                    "user_id": ep.user_id,
                }
                for ep in eps
            ]

    # --- users ---
    def create_user(self, email: str, password_hash: str) -> Optional[str]:
        """Return new user id, or None if the email is already registered."""
        uid = "us" + uuid.uuid4().hex[:8]
        with self._session() as s:
            s.add(User(id=uid, email=email, password_hash=password_hash))
            try:
                s.commit()
            except IntegrityError:
                s.rollback()
                return None
        return uid

    def get_user(self, user_id: str) -> Optional[dict]:
        with self._session() as s:
            return _user_dict(s.get(User, user_id))

    def get_user_by_email(self, email: str) -> Optional[dict]:
        with self._session() as s:
            return _user_dict(s.scalar(select(User).where(User.email == email)))

    def update_status(self, eid: str, state: str) -> None:
        with self._session() as s:
            ep = s.get(Episode, eid)
            if ep is not None:
                ep.state = state
                s.commit()

    def put_artifact(self, eid: str, key: str, value: Any) -> None:
        with self._session() as s:
            art = s.get(Artifact, {"episode_id": eid, "key": key})
            if art is None:
                s.add(Artifact(episode_id=eid, key=key, value=value))
            else:
                art.value = value
            s.commit()

    def get_artifact(self, eid: str, key: str) -> Any:
        with self._session() as s:
            art = s.get(Artifact, {"episode_id": eid, "key": key})
            return art.value if art is not None else None
