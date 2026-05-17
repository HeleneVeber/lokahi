# Migration FastAPI — Notes d'architecture

## Contexte

MVP actuel en Streamlit avec SQLite. Ce document note les décisions prises pendant le MVP
qui impactent directement la migration vers FastAPI + PostgreSQL.

## Ce qui est déjà prêt

- **Fichiers séparés par entité** (`models/gestor.py`, `models/address.py`, `models/imovel.py`) — scalable tel quel
- **DTOs Pydantic** (`GestorData`, `AddressData`) — à renommer et étendre, pas à réécrire
- **`get_or_create` retourne `(instance, created: bool)`** — pattern compatible avec des endpoints REST
- **`models/__init__.py`** — re-exports en place, pas de changement à faire

## Ce qui devra changer

### 1 — Couche service à extraire

Aujourd'hui `save_many` gère à la fois la logique métier et la transaction (session, commit).
En FastAPI, la session est injectée via `Depends(get_session)` — `save_many` ne doit plus
créer sa propre session.

Cible :
```
routers/gestores.py      ← endpoints HTTP
    └── services/gestor_service.py  ← logique métier, reçoit session en paramètre
            └── Gestor.get_or_create(session, gestor_data)  ← accès DB pur
```

### 2 — DTOs à étendre (pattern SQLModel)

Aujourd'hui `GestorData` sert à la fois pour le form et l'import CSV.
En FastAPI, distinguer les schémas d'entrée et de sortie :

```python
class GestorBase(SQLModel):       # champs communs
class GestorCreate(GestorBase):   # request body — name obligatoire
class GestorPublic(GestorBase):   # response — ajoute id
class Gestor(GestorBase, table=True):  # entité DB
```

Note : `GestorCreate.name` sera `str` (obligatoire), contrairement à `GestorData.name`
qui est `str | None` pour supporter le cas "gestor existant sans nom fourni".

**Pourquoi `GestorBase` est absent du MVP :** un seul héritier (`Gestor`) ne justifie pas
une base intermédiaire. En FastAPI, `GestorCreate` et `GestorPublic` justifient son introduction.

### 3 — `AddressData` rester découplé de `ViaCepData`

`ViaCepData` est un schéma de réponse API externe (ViaCEP). `AddressData` est un DTO de domaine.
Ces deux objets ont les mêmes champs aujourd'hui — c'est une coïncidence, pas une relation d'héritage.

En FastAPI, maintenir la séparation :
- `ViaCepData` reste dans `utils/viacep.py` ou `types.py` — contrat API externe
- `AddressData` / `AddressCreate` restent indépendants — contrat domaine

Si ViaCEP change son format de réponse, le domaine ne doit pas casser.

### 4 — `display()` à supprimer

`display()` mélange logique de présentation dans le modèle.
En FastAPI, remplacer par le schéma `GestorPublic` sérialisé automatiquement.

### 5 — Base de données

SQLite → PostgreSQL schema-per-tenant (voir CLAUDE.md).
Le code SQLAlchemy/SQLModel ne change pas — seule la connexion change.

## Décision actuelle

Compromis accepté pour le MVP : `save_many` gère sa propre session.
À refactorer en priorité lors du passage FastAPI, avant d'écrire les premiers endpoints.
