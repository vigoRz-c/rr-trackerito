# Erreurs et Obstacles rencontrés pendant le développement

Voici l'historique des erreurs potentielles anticipées ou survenues lors de la transformation du bot.

1. **Absence de Clé API par défaut** : 
L'API de HenrikDev requiert désormais une autorisation (Clé API) pour fonctionner correctement ou limiter les erreurs 429 (Rate Limit). Il a fallu l'ajouter dans la documentation pour que l'utilisateur soit averti qu'il doit configurer une clé dans son fichier `.env`.

2. **Gestion asynchrone des requêtes HTTP** :
L'utilisation de la librairie standard `requests` est bloquante et figerait le bot Discord entier lors d'un appel à l'API Valorant. Pour contourner ce problème, il a été décidé d'utiliser `aiohttp`, qui permet des requêtes asynchrones, préservant la réactivité de `discord.py`. L'installation de cette dépendance a été ajoutée à la documentation.

3. **Mise à jour du statut des joueurs (Background Task)** :
Créer une boucle infinie avec un `while True` et `asyncio.sleep` est une mauvaise pratique avec `discord.py`. La solution a été d'utiliser l'extension intégrée `discord.ext.tasks` qui permet de créer des boucles robustes (`@tasks.loop`).

4. **Persistance des données** :
Il a fallu choisir un moyen simple et efficace de stocker les profils liés (Discord -> Valorant). L'utilisation d'une base SQL lourde aurait rendu le bot complexe à déployer. Nous avons donc opté pour un fichier JSON (`tracker_data.json`) qui est écrit et lu de manière sûre, en le créant s'il n'existe pas.

5. **Gestion du setup_hook()** :
Dans le fichier principal `neckhurts.py`, le bot utilise une classe héritant de `discord.Client` (avec le `CommandTree` instancié manuellement). Les tâches d'arrière-plan (`tasks.loop`) doivent être lancées au bon moment, idéalement dans `setup_hook` ou `on_ready`. La tâche de fond a été correctement importée et lancée dans `setup_hook`.

6. **Détection de changement de partie** :
Comment savoir si un joueur a fait une partie ? On stocke son ELO absolu (`elo` dans l'API HenrikDev) à chaque vérification. Si l'ELO change, c'est qu'une partie s'est terminée.

7. **Problème de compilation PyInstaller avec les fuseaux horaires** :
Lors de l'ajout du récapitulatif quotidien à 9h, l'utilisation de `zoneinfo` (et de `tzdata` sous Windows) faisait crasher l'exécutable (`ModuleNotFoundError` et `ZoneInfoNotFoundError`). La solution la plus robuste pour une distribution via PyInstaller a été d'utiliser un décalage horaire en Python pur (`datetime.timezone(datetime.timedelta(hours=2))`) pour s'affranchir complètement des bases de données de l'OS.

8. **Crash API NoneType (Valeurs Nulles)** :
L'API Henrik renvoie parfois certaines clés (comme `assets` ou `stats`) avec la valeur explicite `null` au lieu d'un dictionnaire vide, notamment s'il y a un bug de récupération côté Riot. Le code Python plantait avec `AttributeError: 'NoneType' object has no attribute 'get'`. Il a fallu remplacer les vérifications classiques `get("key", {})` par `get("key") or {}` pour forcer l'usage d'un dictionnaire vide en cas de `None`.

9. **Oubli du récapitulatif si le bot est éteint à 9h** :
L'extension `discord.ext.tasks.loop(time=...)` s'exécute uniquement si le bot est allumé à l'heure H. Si le bot était éteint à 9h00, le récapitulatif de la veille n'était jamais envoyé. Une solution de "catch-up" (rattrapage) a été développée en stockant la date d'envoi (`last_daily_recap`) dans une clé globale `_meta` du fichier JSON. Au démarrage, le bot vérifie s'il a manqué l'envoi d'aujourd'hui et se rattrape instantanément.

10. **Crash KeyError suite à l'ajout de la clé globale _meta** :
En ajoutant la clé globale `"_meta"` dans `tracker_data.json` pour stocker des paramètres, les boucles qui itéraient sur tous les profils (`for discord_id, info in tracker_data.items()`) essayaient de lire le pseudo (`info["nom"]`) sur cet objet de configuration interne, causant des `KeyError`. Il a fallu ajouter des conditions `if user_id == "_meta": continue` partout (tracker, commandes, autocomplétion).

11. **Absence de fallback pour le Daily Recap** :
Si `TRACKER_CHANNEL_ID` n'était pas défini dans le `.env`, la boucle Tracker envoyait les messages de match en message privé (DM) à l'utilisateur, mais le Daily Recap, lui, n'avait pas cette sécurité et ignorait l'envoi. Un fallback a été implémenté pour envoyer le récapitulatif global en DM à tous les utilisateurs enregistrés.

12. **Génération d'objets JSON dans le terminal** :
Pour faciliter le débogage et l'inspection des données, des logs ont été ajoutés pour imprimer dans le terminal le contenu exact des embeds (au format JSON) avant leur envoi sur Discord, remplaçant ainsi le message envahissant de démarrage dans le salon Discord.

13. **Migration vers l'embed premium style RR Tracker** :
L'embed de fin de partie a été entièrement refondu pour afficher : rang avec emoji, bannière du rang (`RANK_BANNER_URLS`), miniature de l'agent, KDA, ACS (score brut / nb_rounds), HS% (headshots / total_shots × 100), Map, nombre de rounds, et le gain/perte de RR en `code block`. Les données de HS%, bodyshots et legshots proviennent de `stats.headshots/bodyshots/legshots` dans la réponse v3/matches. L'ACS est calculé côté bot via `score_raw / rounds_played`. Un bouton interactif `DernieresGamesView` (discord.ui.View, timeout=120s) est attaché à chaque message pour afficher les 5 dernières games en éphémère.

14. **Fausse détection Victoire/Défaite** :
Le titre de l'embed (`VICTOIRE` / `DÉFAITE`) était calculé à partir de `diff = current_elo - last_elo` (l'écart ELO global depuis la dernière vérification). Si le joueur a joué plusieurs parties entre deux cycles de 2 minutes, ce `diff` peut être positif alors que la *dernière game* était une défaite, d'où des VICTOIRE affichées avec -19 RR. **Fix** : utiliser `mmr_change_to_last_game` (retourné directement par l'API HenrikDev) pour déterminer `is_win`/`is_draw`, car il représente précisément le RR changé lors de la dernière partie.
