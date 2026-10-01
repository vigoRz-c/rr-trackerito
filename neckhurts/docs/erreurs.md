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
