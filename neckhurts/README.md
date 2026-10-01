# Comment activer le bot

Il y a deux façons d'activer le bot selon vos préférences (via l'exécutable ou via le script Python).

## Option 1 : Utiliser l'exécutable (Plus simple)
1. Assurez-vous d'avoir complété les prérequis (notamment la création du fichier `.env` contenant votre Token, voir l'autre fichier).
2. Double-cliquez simplement sur le fichier **`neckhurts.exe`** situé dans ce dossier.
3. Une fenêtre de terminal (invite de commandes) devrait s'ouvrir. Si le lancement est réussi, elle affichera le message : `✅ Connecté en tant que ...`.

## Option 2 : Utiliser le script Python
1. Ouvrez un terminal (PowerShell ou Invite de commandes) dans le dossier du projet.
2. Installez les dépendances nécessaires si ce n'est pas déjà fait :
   ```bash
   pip install discord.py python-dotenv
   ```
3. Lancez le bot avec la commande :
   ```bash
   python neckhurts.py
   ```
4. Le terminal affichera : `✅ Connecté en tant que ...`.
