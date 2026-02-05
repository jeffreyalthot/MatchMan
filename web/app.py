from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, Request
from fastapi.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


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


class InMemoryStore:
    """Mini stockage mémoire pour démontrer le MVP web."""

    def __init__(self) -> None:
        self.men: List[MaleProfile] = [
            MaleProfile(1, "NoahFit", "Paris", "Île-de-France", "Coach sportif, humour et voyages.", "Sport, cinéma"),
            MaleProfile(2, "LeoArt", "Lyon", "Auvergne-Rhône-Alpes", "Photographe passionné, calme.", "Photo, randonnées"),
            MaleProfile(3, "SamCode", "Paris", "Île-de-France", "Développeur, jeux de société et brunch.", "Tech, jeux"),
        ]
        self.matches: Dict[int, List[int]] = {}
        self.conversations: Dict[int, Conversation] = {}
        self.conversation_ids = count(1)
        self.users: Dict[str, User] = {
            "alice@example.com": User(id=7, email="alice@example.com", password="secret123", role="woman", username="Alice"),
            "noah@example.com": User(id=10, email="noah@example.com", password="secret123", role="man", username="NoahFit"),
        }
        self.user_ids = count(11)

    def men_by_city(self, city: str) -> List[MaleProfile]:
        if not city:
            return self.men
        return [profile for profile in self.men if profile.city.lower() == city.lower()]

    def create_match(self, woman_id: int, woman_name: str, man_id: int) -> Conversation:
        matched_ids = self.matches.setdefault(woman_id, [])
        if man_id not in matched_ids:
            matched_ids.append(man_id)
            man = next(profile for profile in self.men if profile.id == man_id)
            conversation_id = next(self.conversation_ids)
            conversation = Conversation(
                id=conversation_id,
                woman_name=woman_name,
                man_name=man.username,
                messages=[f"Match activé entre {woman_name} et {man.username}."],
            )
            self.conversations[conversation_id] = conversation
            return conversation

        for conversation in self.conversations.values():
            if conversation.woman_name == woman_name and any(profile.id == man_id and profile.username == conversation.man_name for profile in self.men):
                return conversation

        raise ValueError("Conversation introuvable")

    def register_user(self, email: str, password: str, role: str, username: str) -> User:
        normalized_email = email.lower().strip()
        if normalized_email in self.users:
            raise ValueError("Un compte existe déjà avec cet email.")
        user = User(id=next(self.user_ids), email=normalized_email, password=password, role=role, username=username)
        self.users[normalized_email] = user
        return user

    def authenticate(self, email: str, password: str) -> Optional[User]:
        user = self.users.get(email.lower().strip())
        if not user or user.password != password:
            return None
        return user


store = InMemoryStore()
app = FastAPI(title="MatchMan Web MVP")
app.add_middleware(SessionMiddleware, secret_key="matchman-dev-secret", max_age=60 * 60 * 24 * 7)
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


def current_user(request: Request) -> Optional[User]:
    email = request.session.get("user_email")
    if not email:
        return None
    return store.users.get(email)


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

    conversation = store.create_match(woman_id=woman_id, woman_name=woman_name, man_id=man_id)
    return RedirectResponse(url=f"/conversations/{conversation.id}", status_code=303)


@app.get("/conversations/{conversation_id}", response_class=HTMLResponse)
def conversation_detail(request: Request, conversation_id: int) -> HTMLResponse:
    redirect = redirect_if_anonymous(request)
    if redirect:
        return redirect

    conversation = store.conversations[conversation_id]
    return templates.TemplateResponse("conversation.html", template_context(request, conversation=conversation))


@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: int, message: str = Form(...)) -> RedirectResponse:
    store.conversations[conversation_id].messages.append(message)
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
