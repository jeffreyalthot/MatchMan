from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from web.database import (
    ConversationModel,
    MaleProfileModel,
    MatchModel,
    MessageModel,
    SessionLocal,
    UserModel,
    init_database,
)


@dataclass
class MaleProfile:
    id: int
    username: str
    city: str
    region: str
    bio: str
    tastes: str


@dataclass
class Conversation:
    id: int
    woman_name: str
    man_name: str
    messages: List[str] = field(default_factory=list)


@dataclass
class User:
    id: int
    email: str
    password: str
    role: str
    username: str


class SqlStore:
    """Stockage SQLite pour le MVP web."""

    def __init__(self) -> None:
        init_database()
        self._seed_if_empty()

    def _seed_if_empty(self) -> None:
        with SessionLocal() as session:
            has_men = session.scalar(select(MaleProfileModel.id).limit(1))
            if has_men:
                return

            session.add_all(
                [
                    MaleProfileModel(
                        id=1,
                        username="NoahFit",
                        city="Paris",
                        region="Île-de-France",
                        bio="Coach sportif, humour et voyages.",
                        tastes="Sport, cinéma",
                    ),
                    MaleProfileModel(
                        id=2,
                        username="LeoArt",
                        city="Lyon",
                        region="Auvergne-Rhône-Alpes",
                        bio="Photographe passionné, calme.",
                        tastes="Photo, randonnées",
                    ),
                    MaleProfileModel(
                        id=3,
                        username="SamCode",
                        city="Paris",
                        region="Île-de-France",
                        bio="Développeur, jeux de société et brunch.",
                        tastes="Tech, jeux",
                    ),
                ]
            )

            session.add_all(
                [
                    UserModel(id=7, email="alice@example.com", password="secret123", role="woman", username="Alice"),
                    UserModel(id=10, email="noah@example.com", password="secret123", role="man", username="NoahFit"),
                ]
            )
            session.commit()

    def men_by_city(self, city: str) -> List[MaleProfile]:
        with SessionLocal() as session:
            query = select(MaleProfileModel)
            if city:
                query = query.where(MaleProfileModel.city.ilike(city))
            men = session.scalars(query.order_by(MaleProfileModel.id)).all()
            return [
                MaleProfile(id=man.id, username=man.username, city=man.city, region=man.region, bio=man.bio, tastes=man.tastes)
                for man in men
            ]

    def create_match(self, woman_id: int, woman_name: str, man_id: int) -> Conversation:
        with SessionLocal() as session:
            existing_match = session.scalar(
                select(MatchModel).where(MatchModel.woman_id == woman_id, MatchModel.man_id == man_id)
            )
            if existing_match:
                conversation = session.scalar(select(ConversationModel).where(ConversationModel.match_id == existing_match.id))
                if not conversation:
                    raise ValueError("Conversation introuvable")
                return self._to_conversation(conversation)

            man = session.get(MaleProfileModel, man_id)
            if not man:
                raise ValueError("Profil homme introuvable")

            match = MatchModel(woman_id=woman_id, man_id=man_id)
            session.add(match)
            session.flush()

            conversation = ConversationModel(
                match_id=match.id,
                woman_name=woman_name,
                man_name=man.username,
            )
            session.add(conversation)
            session.flush()

            session.add(
                MessageModel(
                    conversation_id=conversation.id,
                    body=f"Match activé entre {woman_name} et {man.username}.",
                )
            )
            session.commit()
            return self._to_conversation(conversation)

    def register_user(self, email: str, password: str, role: str, username: str) -> User:
        normalized_email = email.lower().strip()
        with SessionLocal() as session:
            existing = session.scalar(select(UserModel).where(UserModel.email == normalized_email))
            if existing:
                raise ValueError("Un compte existe déjà avec cet email.")
            user = UserModel(email=normalized_email, password=password, role=role, username=username)
            session.add(user)
            session.commit()
            session.refresh(user)
            return User(id=user.id, email=user.email, password=user.password, role=user.role, username=user.username)

    def authenticate(self, email: str, password: str) -> Optional[User]:
        normalized_email = email.lower().strip()
        with SessionLocal() as session:
            user = session.scalar(select(UserModel).where(UserModel.email == normalized_email))
            if not user or user.password != password:
                return None
            return User(id=user.id, email=user.email, password=user.password, role=user.role, username=user.username)

    def user_by_email(self, email: str) -> Optional[User]:
        with SessionLocal() as session:
            user = session.scalar(select(UserModel).where(UserModel.email == email.lower().strip()))
            if not user:
                return None
            return User(id=user.id, email=user.email, password=user.password, role=user.role, username=user.username)

    def conversation_by_id(self, conversation_id: int) -> Conversation:
        with SessionLocal() as session:
            conversation = session.get(ConversationModel, conversation_id)
            if not conversation:
                raise KeyError(conversation_id)
            return self._to_conversation(conversation)

    def append_message(self, conversation_id: int, message: str) -> None:
        with SessionLocal() as session:
            conversation = session.get(ConversationModel, conversation_id)
            if not conversation:
                raise KeyError(conversation_id)
            session.add(MessageModel(conversation_id=conversation.id, body=message))
            session.commit()

    def _to_conversation(self, conversation: ConversationModel) -> Conversation:
        sorted_messages = sorted(conversation.messages, key=lambda m: m.id)
        return Conversation(
            id=conversation.id,
            woman_name=conversation.woman_name,
            man_name=conversation.man_name,
            messages=[message.body for message in sorted_messages],
        )


store = SqlStore()
app = FastAPI(title="MatchMan Web MVP")
app.add_middleware(SessionMiddleware, secret_key="matchman-dev-secret", max_age=60 * 60 * 24 * 7)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


def current_user(request: Request) -> Optional[User]:
    email = request.session.get("user_email")
    if not email:
        return None
    return store.user_by_email(email)


def redirect_if_anonymous(request: Request) -> Optional[RedirectResponse]:
    if current_user(request):
        return None
    return RedirectResponse(url="/auth/login", status_code=303)


def template_context(request: Request, **context: object) -> Dict[str, object]:
    return {"request": request, "current_user": current_user(request), **context}


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home.html", template_context(request))


@app.get("/auth/register", response_class=HTMLResponse)
def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", template_context(request, error=None))


@app.post("/auth/register")
def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    username: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    if role not in {"man", "woman"}:
        return templates.TemplateResponse("register.html", template_context(request, error="Rôle invalide."), status_code=400)

    try:
        user = store.register_user(email=email, password=password, role=role, username=username)
    except ValueError as error:
        return templates.TemplateResponse("register.html", template_context(request, error=str(error)), status_code=400)

    request.session["user_email"] = user.email
    if user.role == "woman":
        return RedirectResponse(url="/women/discover", status_code=303)
    return RedirectResponse(url="/men/space", status_code=303)


@app.get("/auth/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", template_context(request, error=None))


@app.post("/auth/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)) -> HTMLResponse | RedirectResponse:
    user = store.authenticate(email=email, password=password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            template_context(request, error="Identifiants invalides."),
            status_code=401,
        )

    request.session["user_email"] = user.email
    if user.role == "woman":
        return RedirectResponse(url="/women/discover", status_code=303)
    return RedirectResponse(url="/men/space", status_code=303)


@app.post("/auth/logout")
def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/women/discover", response_class=HTMLResponse)
def discover_men(request: Request, city: str = "") -> HTMLResponse:
    redirect = redirect_if_anonymous(request)
    if redirect:
        return redirect

    user = current_user(request)
    if not user or user.role != "woman":
        return RedirectResponse(url="/", status_code=303)

    men = store.men_by_city(city)
    return templates.TemplateResponse(
        "discover.html",
        template_context(
            request,
            men=men,
            city=city,
            subscription_active=True,
        ),
    )


@app.post("/women/match")
def create_match(
    request: Request,
    man_id: int = Form(...),
    woman_id: int = Form(...),
    woman_name: str = Form(...),
) -> RedirectResponse:
    user = current_user(request)
    if not user or user.role != "woman":
        return RedirectResponse(url="/auth/login", status_code=303)

    conversation = store.create_match(woman_id=user.id, woman_name=user.username, man_id=man_id)
    return RedirectResponse(url=f"/conversations/{conversation.id}", status_code=303)


@app.get("/conversations/{conversation_id}", response_class=HTMLResponse)
def conversation_detail(request: Request, conversation_id: int) -> HTMLResponse:
    redirect = redirect_if_anonymous(request)
    if redirect:
        return redirect

    conversation = store.conversation_by_id(conversation_id)
    return templates.TemplateResponse("conversation.html", template_context(request, conversation=conversation))


@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: int, message: str = Form(...)) -> RedirectResponse:
    store.append_message(conversation_id, message)
    return RedirectResponse(url=f"/conversations/{conversation_id}", status_code=303)


@app.get("/men/space", response_class=HTMLResponse)
def men_space(request: Request) -> HTMLResponse:
    redirect = redirect_if_anonymous(request)
    if redirect:
        return redirect

    user = current_user(request)
    if not user or user.role != "man":
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "men_space.html",
        template_context(
            request,
            posts=[
                {"title": "Sortie escalade", "views": 51},
                {"title": "Recherche partenaire voyage", "views": 34},
            ],
        ),
    )
