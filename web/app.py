from __future__ import annotations

from dataclasses import dataclass, field
from itertools import count
from typing import Dict, List

from fastapi import FastAPI, Form, Request
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


store = InMemoryStore()
app = FastAPI(title="MatchMan Web MVP")
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/women/discover", response_class=HTMLResponse)
def discover_men(request: Request, city: str = "") -> HTMLResponse:
    men = store.men_by_city(city)
    return templates.TemplateResponse(
        "discover.html",
        {
            "request": request,
            "men": men,
            "city": city,
            "subscription_active": True,
        },
    )


@app.post("/women/match")
def create_match(man_id: int = Form(...), woman_id: int = Form(...), woman_name: str = Form(...)) -> RedirectResponse:
    conversation = store.create_match(woman_id=woman_id, woman_name=woman_name, man_id=man_id)
    return RedirectResponse(url=f"/conversations/{conversation.id}", status_code=303)


@app.get("/conversations/{conversation_id}", response_class=HTMLResponse)
def conversation_detail(request: Request, conversation_id: int) -> HTMLResponse:
    conversation = store.conversations[conversation_id]
    return templates.TemplateResponse("conversation.html", {"request": request, "conversation": conversation})


@app.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: int, message: str = Form(...)) -> RedirectResponse:
    store.conversations[conversation_id].messages.append(message)
    return RedirectResponse(url=f"/conversations/{conversation_id}", status_code=303)


@app.get("/men/space", response_class=HTMLResponse)
def men_space(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "men_space.html",
        {
            "request": request,
            "posts": [
                {"title": "Sortie escalade", "views": 51},
                {"title": "Recherche partenaire voyage", "views": 34},
            ],
        },
    )
