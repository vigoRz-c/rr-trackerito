# Documentation de Neckhurts (RR Tracker)

## Introduction
Le bot Neckhurts, anciennement axé sur des fonctions humoristiques (troll), intègre désormais des fonctionnalités de suivi de Ranked Rating (RR) pour le jeu Valorant.

## Fonctionnalités Valorant

### 1. Commande `/rr`
Permet de consulter ponctuellement les statistiques d'un joueur.
- **Paramètres** : `nom`, `tag`, `region` (par défaut 'eu').
- **Utilisation** : `/rr nom:TenZ tag:000 region:na`

### 2. Tracker Automatique et Commande `/link`
Permet d'associer un compte Discord à un compte Riot Valorant et de suivre son évolution en arrière-plan.
- **`/link <nom> <tag> <region>`** : Lier son compte Riot à son profil Discord.
- **`/unlink`** : Supprimer l'association.
- **Tâche de fond (Tracker)** : Toutes les 10 minutes, le bot vérifie les statistiques (Elo) de chaque compte enregistré. Si l'Elo a changé (ce qui implique la fin d'une partie compétitive), le bot envoie un message dans un salon dédié (ou dans le système si non configuré) pour afficher le gain ou la perte de RR.

## Installation / Configuration

1. Obtenez une clé API depuis le Discord de [HenrikDev](https://henrikdev.xyz/).
2. Ajoutez la clé dans le fichier `.env` du bot :
```env
DISCORD_TOKEN=votre_token
HENRIK_API_KEY=votre_cle_api
TRACKER_CHANNEL_ID=123456789012345678 (optionnel, l'ID du salon où le bot doit annoncer les changements de RR)
```
3. Installez les dépendances nécessaires : `pip install aiohttp`
4. Lancez le bot via `python neckhurts.py` ou recompilez-le avec `pyinstaller neckhurts.spec`.

## Fichiers de données
Le bot stocke les joueurs enregistrés dans un fichier JSON nommé `tracker_data.json` à la racine du projet. Ce fichier est généré automatiquement lors du premier `/link`.
