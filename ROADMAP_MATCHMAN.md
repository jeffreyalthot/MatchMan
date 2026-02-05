# Workmap (feuille de route) — Plateforme de rencontre orientée « profils hommes visibles, abonnement femme »

## 0) Vision produit
Créer une plateforme de rencontre où :
- **Les hommes** créent et enrichissent leur profil (username, photos, vidéos, bio, goûts), publient des mini-annonces, puis attendent les matchs.
- **Les femmes** paient un abonnement Stripe pour consulter les profils hommes de leur ville/région, initier un match, puis discuter.
- Quand la femme déclenche le match, une **messagerie privée** s’active entre les deux utilisateurs.

Le projet est livré en **3 volets distincts** :
1. **Server (API + logique métier + base de données)** en Python.
2. **Site web** en Python (frontend web).
3. **Application Android** en Kivy (Python).

---

## 1) Règles métier essentielles

## 1.1 Rôles utilisateurs
- **Homme**
  - Peut créer/éditer son profil (username, photos, vidéos, bio, goûts).
  - Ne paie pas pour être visible.
  - Peut publier des **posts/annonces** (texte + image + vidéo).
  - Peut consulter ses propres posts et les statistiques de base (vues, likes si activé).
  - Peut consulter le profil d’une femme **uniquement si conversation active** (après match initié par elle).

- **Femme**
  - Doit avoir un abonnement actif (Stripe) pour voir la liste des profils hommes.
  - Filtre les hommes par ville/région.
  - Peut initier un match avec un homme.
  - Peut accéder à la messagerie après création du match.
  - N’a pas de fil d’actualité global, mais voit les posts des hommes consultés.

## 1.2 Match & messagerie
- Le match est créé **exclusivement par la femme**.
- Dès création du match, un canal de discussion privé est automatiquement créé.
- L’homme peut alors consulter le profil de la femme liée à cette discussion.

## 1.3 Paiement Stripe
- Gestion de l’abonnement femme via Stripe :
  - Checkout Session
  - Webhook de confirmation paiement
  - Mise à jour statut abonnement (active, past_due, canceled)
- Blocage des endpoints premium si abonnement inactif.

---

## 2) Architecture technique recommandée

## 2.1 Stack Python proposée
- **Backend/API** : FastAPI
- **Base de données** : PostgreSQL
- **ORM** : SQLAlchemy + Alembic
- **Authentification** : JWT + refresh tokens
- **Temps réel messagerie** : WebSocket (FastAPI) ou Redis Pub/Sub
- **Tâches asynchrones** : Celery + Redis (optionnel)
- **Stockage médias** : S3 compatible (AWS S3, MinIO)
- **Paiement** : Stripe SDK Python

## 2.2 Site web Python
Deux options réalistes :
- **Option A (rapide)** : Django + templates server-side.
- **Option B (moderne python-first)** : FastAPI backend + frontend HTMX/Jinja2.

Recommandation : **Django** si équipe débutante; sinon FastAPI + Jinja2 pour alignement API/web.

## 2.3 Application Android Kivy
- Kivy + KivyMD (UI)
- Communication API REST + WebSocket
- Upload médias depuis téléphone
- Notifications push (phase 2, via Firebase si besoin)

---

## 3) Découpage en modules

## 3.1 Module Server (coeur métier)
1. **Auth & comptes**
   - Inscription/connexion
   - Rôle homme/femme
   - Vérification email/téléphone
2. **Profils**
   - CRUD profil homme
   - CRUD profil femme
   - Upload photo/vidéo
3. **Découverte**
   - Liste hommes par région/ville
   - Filtres (âge, centres d’intérêt, activité)
4. **Matchs**
   - Endpoint « femme crée match »
   - Prévention doublons de match
5. **Messagerie**
   - Création auto conversation
   - Envoi texte/image/vidéo
   - Historique
6. **Posts hommes**
   - CRUD posts annonces
   - Flux posts visible depuis profil homme
7. **Abonnements Stripe**
   - Checkout
   - Webhook
   - Contrôle d’accès premium
8. **Modération & sécurité**
   - Signalements
   - Anti-spam
   - Limitation de débit

## 3.2 Module Site web Python
- Espace homme : édition profil + posts + stats + messagerie.
- Espace femme : abonnement + recherche hommes + match + messagerie.
- Pages légales : CGU, confidentialité, consentement, suppression compte.

## 3.3 Module Android Kivy
- Onboarding + authentification.
- Dashboard adapté au rôle.
- Ecran profils, match, chat, abonnement Stripe (via redirection web sécurisée).
- Upload médias et prévisualisation.

---

## 4) Modèle de données (MVP)

Tables principales :
- `users` (id, role, email, password_hash, created_at)
- `profiles_men` (user_id, username, bio, tastes, city, region, avatar_url)
- `profiles_women` (user_id, username, bio, city, region, avatar_url)
- `media` (id, user_id, type[photo|video], url, created_at)
- `subscriptions` (user_id, stripe_customer_id, stripe_subscription_id, status, period_end)
- `male_posts` (id, man_user_id, text, media_url, created_at)
- `matches` (id, woman_user_id, man_user_id, created_at, status)
- `conversations` (id, match_id, created_at)
- `messages` (id, conversation_id, sender_id, type[text|image|video], body, created_at)
- `reports` (id, reporter_id, target_user_id, reason, created_at)

---

## 5) API endpoints clés (exemple)

- `POST /auth/register`
- `POST /auth/login`
- `GET /men?region=&city=` (femme abonnée)
- `POST /matches` (femme initie)
- `GET /conversations/{id}`
- `POST /conversations/{id}/messages`
- `POST /men/posts`
- `GET /men/{id}/posts`
- `POST /stripe/create-checkout-session`
- `POST /stripe/webhook`

---

## 6) Plan de livraison par phases

## Phase 1 — Fondations (2 à 3 semaines)
- Setup repo mono-projet : `server/`, `web/`, `android_kivy/`
- Authentification + rôles
- Schéma DB initial + migrations
- Upload média basique
- UI minimale web + Kivy

## Phase 2 — Cœur fonctionnel (3 à 4 semaines)
- Recherche hommes par ville/région
- Création de match (femme)
- Messagerie privée temps réel
- Profil homme complet + posts annonces

## Phase 3 — Monétisation Stripe (1 à 2 semaines)
- Checkout femme
- Webhooks + état abonnement
- Restriction d’accès premium

## Phase 4 — Qualité & sécurité (2 semaines)
- Modération, blocage, signalement
- Logs, monitoring, audit sécurité
- Tests charge sur messagerie

## Phase 5 — Release (1 semaine)
- Déploiement staging puis production
- Publication APK Android interne
- Corrections post-lancement

---

## 7) Sécurité, conformité et confiance
- Chiffrement mot de passe (Argon2/Bcrypt)
- Validation médias (taille, type MIME, scan antivirus)
- Contrôle d’accès strict par rôle et état abonnement
- Journalisation des actions sensibles
- Mécanisme de suppression compte + données RGPD
- Conditions d’utilisation claires (contenu adulte, harcèlement, fake profils)

---

## 8) Import externe (intégrations recommandées)
Pour « utiliser l’import externe » efficacement en Python :
- `stripe` pour abonnements.
- `fastapi`, `sqlalchemy`, `alembic`, `pydantic` pour l’API.
- `python-multipart` pour uploads.
- `boto3` pour stockage S3.
- `websockets`/support FastAPI pour chat temps réel.
- `kivy`, `kivymd`, `requests`, `websocket-client` pour Android.

Exemple d’imports Python (serveur) :
```python
from fastapi import FastAPI, Depends, WebSocket
from sqlalchemy.orm import Session
import stripe
```

---

## 9) Backlog MVP priorisé
1. Auth + rôles homme/femme
2. Création profil homme/femme
3. Abonnement Stripe femme
4. Liste hommes par région/ville
5. Match initié par femme
6. Ouverture conversation automatique
7. Messagerie textuelle
8. Upload image/vidéo profil
9. Posts annonces homme
10. Modération minimale (report + blocage)

---

## 10) Critères de succès MVP
- Une femme abonnée peut trouver des hommes de sa région et initier un match.
- Le chat s’ouvre immédiatement après match et les deux parties échangent.
- Un homme peut publier des annonces enrichissant son profil.
- Le système Stripe verrouille correctement l’accès premium.
- Les trois volets (server, site web Python, Android Kivy) communiquent avec la même API.
