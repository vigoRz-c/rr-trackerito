# Documentation de RR Trackerito (RR Tracker Valorant)

## Introduction
Le bot RR Trackerito est un bot Discord 100% dedie au suivi des statistiques et des parties classees (Ranked Rating) sur le jeu Valorant.

## Fonctionnalites Valorant

### 1. Commande /rr (Details du dernier match)
Permet de consulter ponctuellement les statistiques d un joueur. Elle affiche le Rang, les RR actuels, mais aussi les details de la derniere game (KDA, Agent, Map, Resultat).
- Parametres : nom (avec autocompletion), tag (optionnel si le joueur est enregistre), region (par defaut eu).
- Utilisation : /rr nom:TenZ tag:000 region:na ou juste /rr nom:PerrierGingembre grace a l autocompletion.

### 2. Tracker Automatique et Commande /link
Permet d associer un compte Discord a un compte Riot Valorant et de suivre son evolution en arriere-plan.
- /link nom tag region : Lier son compte Riot.
- /unlink : Supprimer l association.
- Tache de fond (Tracker) : Toutes les 2 minutes, le bot verifie si une nouvelle partie classee s est terminee pour chaque compte enregistre. La detection est basee sur le matchid de la derniere partie : si le dernier matchid differe du last_match_id sauvegarde en local, le bot declenche la notification. Le last_match_id est sauvegarde immediatement apres detection pour eviter les doublons. Les parties non classees (spike rush, deathmatch, etc.) mettent a jour le last_match_id sans envoyer de notification.
  - Detectection de groupe (Duo/Trio...) : Si plusieurs joueurs du serveur participent a la meme partie (meme matchid), le bot regroupe les resultats et genere une image leaderboard style Valorant via generate_group_image().
  - Un bouton interactif 5 dernieres games est attache a chaque message.

### 3. Commande /classement (Leaderboard)
Affiche le classement en temps reel de tous les membres enregistres via /link.
- Le bot interroge l API HenrikDev pour chaque joueur et trie par ELO decroissant.
- Rendu visuel premium via utils/image_reports_generator.py (Pillow) :
  - En-tete sombre avec accent rouge Valorant et badge du nombre de joueurs.
  - Colonnes POS / JOUEUR / RANG / RR avec icones de rang officielles.
  - Podium (top 3) mis en valeur avec couleurs or/argent/bronze.
  - Avatar Discord : Si le membre est present sur le serveur (guild.get_member()), sa photo de profil Discord est telechargee, decoupee en cercle parfait et affichee. Sinon, fallback sur l initiale coloree selon son rang.
- Fallback : Si la generation d image echoue, un embed texte pagine (15 joueurs/page) est envoye.

### 4. Recapitulatif Quotidien (9h00)
- Tache de fond (Daily Recap) : Tous les jours a 9h00, le bot analyse l historique complet de la veille pour chaque joueur enregistre.
- Le panneau (resolution 1600px de large, haute qualite) contient une carte par joueur avec :
  - Avatar Discord en cercle (84px) si disponible, sinon initiale coloree.
  - Pseudo#Tag en grand.
  - Bilan RR en grand (police 52pt) avec fleche haut/bas et code couleur (vert/rouge).
  - Stats : Victoires / Defaites / Win Rate %.
  - Progression de rang visuelle : icone rang depart -> icone rang fin + barre de progression RR (0-100, 400px).
- Les joueurs sont tries par gain de RR decroissant (meilleur joueur en haut, pire en bas).
- Rattrapage (Catch-up) : Si le bot est eteint a 9h00, il envoie le recapitulatif manquant au redemarrage.
- Fallback : Si la generation d image echoue, un embed texte classique est envoye.

### 5. Commande /test_affichage (Admin)
Genere et envoie dans le salon courant un exemple de chaque type d affichage avec des donnees aleatoires a chaque appel :
1. Recap solo (map, agent, KDA, score, RR aleatoires)
2. Recap duo (joueurs et resultat aleatoires)
3. Recap trio
4. Recap 5-stack
5. Recapitulatif journalier (stats aleatoires pour chaque joueur)
6. Classement (rangs aleatoires, ordre recalcule)

## Architecture and Fichiers cles

| Fichier | Role |
|---|---|
| cogs/tracker.py | Tracker automatique, /link, /unlink, Daily Recap |
| cogs/classement.py | Commande /classement |
| utils/image_generator.py | Generation d image fin de partie + leaderboard groupe |
| utils/image_reports_generator.py | Generation d image classement et recap quotidien (Pillow, 1600px) |
| data/tracker_data.json | Donnees persistantes des joueurs + metadonnees |

## Installation / Configuration

1. Obtenez une cle API depuis HenrikDev (https://dev.henrikdev.xyz/).
2. Creez un fichier .env a la racine :
   DISCORD_TOKEN=votre_token_discord
   HENRIK_API_KEY=votre_cle_api_henrik
   TRACKER_CHANNEL_ID=123456789012345678
3. Installez les dependances : pip install -r requirements.txt
4. Lancez neckhurts.exe ou recompilez-le avec pyinstaller neckhurts.spec.

## Permissions Discord requises

### Privileged Gateway Intents (portail developpeur -> Bot)
| Intent | Requis |
|---|---|
| Server Members Intent | OUI (avatars Discord dans les images) |
| Message Content Intent | OUI |
| Presence Intent | Non necessaire |

### Permissions du bot (OAuth2)
| Permission | Pourquoi |
|---|---|
| Voir les salons | Acceder au channel |
| Envoyer des messages | Envoyer les recaps |
| Integrer des liens | Embeds (recap solo) |
| Joindre des fichiers | Images PNG generees |
| Utiliser les commandes slash | Toutes les commandes / |

Scopes OAuth2 : bot + applications.commands

## Depannage (Erreurs courantes)
- L executable se ferme instantanement : Assurez-vous que le fichier .env est present avec votre token.
- PyInstaller and Fuseaux Horaires : Le code utilise un decalage horaire en dur (UTC+2) pour eviter les problemes zoneinfo.
- Avatars Discord absents dans les images : Verifiez que le Server Members Intent est active dans le portail developpeur Discord ET dans le code (intents.members = True). Sans ca, guild.get_member() retourne None et le bot revient sur les initiales colorees.
- Icones de rang manquantes : En cas d echec reseau, le texte du rang est affiche a la place de l icone.
- Pas de salon configure (TRACKER_CHANNEL_ID) : Le bot envoie les notifications en DM aux utilisateurs concernes.
