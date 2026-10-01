# Documentation de RR Trackerito (RR Tracker Valorant)

## Introduction
Le bot RR Trackerito est un bot Discord 100% dédié au suivi des statistiques et des parties classées (Ranked Rating) sur le jeu Valorant.

## Fonctionnalités Valorant

### 1. Commande `/rr` (Détails du dernier match)
Permet de consulter ponctuellement les statistiques d'un joueur. Elle affiche le Rang, les RR actuels, mais aussi les **détails de la dernière game** (KDA, Agent, Map, Résultat).
- **Paramètres** : `nom` (avec autocomplétion), `tag` (optionnel si le joueur est enregistré), `region` (par défaut 'eu').
- **Utilisation** : `/rr nom:TenZ tag:000 region:na` ou juste `/rr nom:PerrierGingembre` grâce à l'autocomplétion.

### 2. Tracker Automatique et Commande `/link`
Permet d'associer un compte Discord à un compte Riot Valorant et de suivre son évolution en arrière-plan.
- **`/link <nom> <tag> <region>`** : Lier son compte Riot.
- **`/unlink`** : Supprimer l'association.
- **Tâche de fond (Tracker)** : Toutes les 2 minutes, le bot vérifie si une **nouvelle partie classée** s'est terminée pour chaque compte enregistré. La détection est basée sur le **`matchid`** de la dernière partie (et non plus sur le seul changement d'ELO) : si le dernier `matchid` retourné par l'API diffère du `last_match_id` sauvegardé en local, le bot déclenche la notification. Cela garantit une détection fiable même si l'API HenrikDev tarde à mettre à jour le MMR. Le `last_match_id` est sauvegardé dans `tracker_data.json` pour éviter les doublons. Les parties non classées (spike rush, deathmatch, etc.) mettent à jour le `last_match_id` sans envoyer de notification. S'il y a une nouvelle partie détectée, le bot envoie automatiquement un **Embed Premium** de fin de partie dans le salon configuré.
  - L'embed contient désormais une **image générée dynamiquement** en Python via `Pillow`, affichant le fond de la carte jouée, l'agent, le KDA et l'évolution du RR (en vert ou rouge) façon Tracker.gg, pour un rendu beaucoup plus premium. Les assets graphiques (splash arts et icones) sont téléchargés de manière asynchrone en temps réel via l'API publique `valorant-api.com`.
  - **Détection de groupe (Duo/Trio...)** : Si plusieurs joueurs du serveur participent à la même partie (même `matchid`), le bot regroupe intelligemment les résultats dans un seul et même message global pour éviter le spam du salon.
  - Un **bouton interactif** « 🕹️ 5 dernières games » est attaché à chaque message : en cliquant dessus, le joueur reçoit un récapitulatif éphémère de ses 5 dernières parties (agent, KDA, ACS, HS%, score).

### 3. Commande `/classement` (Leaderboard)
Affiche le classement en temps réel de tous les membres enregistrés via `/link`.
- **Pagination interactive** : Les résultats sont affichés par page de 15 joueurs avec des boutons interactifs pour naviguer (◀️ / ▶️) afin de ne pas saturer l'espace du salon. Seul l'auteur de la commande peut naviguer.
- Le bot interroge l'API HenrikDev pour chaque joueur et trie par ELO décroissant.
- L'embed affiche : position (🥇🥈🥉 pour le podium), pseudo#tag, rang actuel et RR.
- Les joueurs dont l'API est indisponible apparaissent en bas du classement avec `—`.

### 4. Récapitulatif Quotidien (9h00)
- **Tâche de fond (Daily Recap)** : Tous les jours à 9h00, le bot analyse l'historique complet de la veille pour chaque joueur enregistré. Il génère un rapport montrant le nombre de victoires/défaites (avec emojis ✅/❌), le winrate, l'évolution globale des RR et la progression de rang (avant → après). 
- **Rattrapage (Catch-up)** : Si le bot est éteint à 9h00, il mémorise son retard et enverra le récapitulatif manquant instantanément dès qu'il sera rallumé.

### 4. Commandes de Test (Admins)
- **`/test_game`** : Simule artificiellement un changement d'ELO pour tester l'annonce automatique du tracker.
- **`/test_recap`** : Force la génération et l'envoi immédiat du récapitulatif quotidien de la veille.

## Installation / Configuration

1. Obtenez une clé API depuis [HenrikDev](https://dev.henrikdev.xyz/).
2. Créez un fichier `.env` à la racine :
```env
DISCORD_TOKEN=votre_token_discord
HENRIK_API_KEY=votre_cle_api_henrik
TRACKER_CHANNEL_ID=123456789012345678 # ID du salon où le bot doit annoncer les changements de RR
```
3. Installez les dépendances : 
   `pip install -r requirements.txt`
4. Lancez `neckhurts.exe` ou recompilez-le avec `pyinstaller neckhurts.spec`.

## Fichiers de données et Architecture
Le projet respecte les conventions `discord.py` avec le code des commandes rangé dans le dossier `cogs/`.
Les joueurs et la mémoire interne (comme la date du dernier récapitulatif) sont stockés dans le fichier protégé `data/tracker_data.json`.

## Dépannage (Erreurs courantes)
- **L'exécutable se ferme instantanément** : Assurez-vous que le fichier `.env` est présent avec votre token et que le dossier `data/` a bien les droits d'écriture. 
- **PyInstaller & Fuseaux Horaires** : L'utilisation du module `zoneinfo` peut faire crasher PyInstaller sur Windows s'il n'arrive pas à compiler la base `tzdata`. Le code utilise un décalage horaire en dur (UTC+2) pour éviter ce problème.
- **Débogage des messages Discord** : Le bot imprime en direct dans le terminal les objets JSON complets des embeds qu'il envoie sur Discord (tracker, récapitulatif, `/rr`). Cela permet de vérifier la validité des données avant leur affichage.
- **Pas de salon configuré (`TRACKER_CHANNEL_ID`)** : Si aucun salon n'est défini, le bot essaiera d'envoyer les notifications de match et le récapitulatif quotidien directement en Message Privé (DM) aux utilisateurs concernés.
