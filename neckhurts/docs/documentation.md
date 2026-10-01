# Documentation de Neckhurts (RR Tracker Valorant)

## Introduction
Le bot Neckhurts est un bot Discord 100% dédié au suivi des statistiques et des parties classées (Ranked Rating) sur le jeu Valorant. Toutes les anciennes fonctionnalités (troll, etc.) ont été complètement retirées pour se concentrer sur l'API Valorant.

## Fonctionnalités Valorant

### 1. Commande `/rr`
Permet de consulter ponctuellement les statistiques d'un joueur sans l'enregistrer dans le tracker.
- **Paramètres** : `nom`, `tag`, `region` (par défaut 'eu').
- **Utilisation** : `/rr nom:TenZ tag:000 region:na`

### 2. Tracker Automatique et Commande `/link`
Permet d'associer un compte Discord à un compte Riot Valorant et de suivre son évolution de RR en arrière-plan.
- **`/link <nom> <tag> <region>`** : Lier son compte Riot à son profil Discord.
- **`/unlink`** : Supprimer l'association.
- **Tâche de fond (Tracker)** : Toutes les 10 minutes, le bot vérifie les statistiques (Elo) de chaque compte enregistré. Si l'Elo a changé (fin d'une partie), le bot récupère **les statistiques de ce dernier match** (Map, Score final, Agent joué, KDA) et envoie un récapitulatif détaillé sous forme d'Embed (encart graphique) dans un salon dédié (ou en message privé).

## Installation / Configuration

1. Obtenez une clé API depuis le portail de développeur [HenrikDev](https://dev.henrikdev.xyz/).
2. Créez un fichier `.env` à la racine du projet (ce fichier ne doit jamais être partagé ou commité) :
```env
DISCORD_TOKEN=votre_token_discord
HENRIK_API_KEY=votre_cle_api_henrik
TRACKER_CHANNEL_ID=123456789012345678 # (Optionnel, l'ID du salon où le bot doit annoncer les changements de RR)
```
3. Installez les dépendances nécessaires : 
   `pip install discord.py python-dotenv aiohttp`
4. Lancez le bot via le fichier exécutable `neckhurts.exe` (ou recompilez-le avec `pyinstaller neckhurts.spec`).

## Fichiers de données
Le bot stocke les joueurs enregistrés dans un fichier JSON nommé `tracker_data.json` à la racine du projet. Ce fichier est généré automatiquement lors de la première exécution de la commande `/link`.

## Dépannage (Erreurs courantes)

- **L'éditeur de code (ex: VSCode) souligne `discord` ou `dotenv` en rouge ("Cannot find module")** :
  C'est un problème d'environnement virtuel. Votre éditeur pointe probablement vers une installation Python différente de celle où vous avez installé les bibliothèques. Vous pouvez soit ignorer cette erreur visuelle, soit changer l'interpréteur Python dans votre éditeur (en bas à droite sur VSCode) pour pointer vers l'installation où `discord.py` est installé (ex: Python 3.14).
- **L'exécutable se ferme instantanément** :
  Assurez-vous que le fichier `.env` est bien présent dans le même dossier que l'exécutable et qu'il contient bien votre token. Si vous recompilez, assurez-vous d'avoir installé les modules via `pip` dans l'environnement que PyInstaller utilise.
