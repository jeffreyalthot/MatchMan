# MatchMan

MVP web Python d'une plateforme de rencontre où les profils hommes sont visibles et où les utilisatrices femmes initient le match.

## Fonctionnalités livrées (alignées roadmap)
- Espace femme avec recherche des profils hommes par ville.
- Match initié uniquement côté femme.
- Création automatique d'une conversation privée après match.
- Espace homme avec aperçu des annonces/posts et statistiques simples.
- Base de données SQLite branchée au serveur FastAPI via SQLAlchemy.

## Lancer en local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn web.app:app --reload
```

Application: `http://127.0.0.1:8000`

## Tests
```bash
pytest
```
