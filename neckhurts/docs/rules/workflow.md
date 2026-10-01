---
name: workflow_obligatoire
description: Règles de workflow à exécuter après chaque modification de code
---

# Workflow Obligatoire

À chaque fois que le bot ou ses commandes sont modifiés, il est IMPÉRATIF de suivre ces 3 étapes avant de terminer l'interaction avec l'utilisateur :

1. **Rebuild l'exécutable (.exe)**
   - Utilise la commande de compilation appropriée avec le fichier spec (ex: `pyinstaller neckhurts.spec --clean --noconfirm`) pour mettre à jour l'exécutable.

2. **Mettre à jour la documentation (`docs/documentation.md`)**
   - Si de nouvelles commandes, fonctionnalités ou variables d'environnement (`.env`) ont été ajoutées/modifiées, documente-les.
   - Mets à jour les comportements décrits si ceux-ci ont changé (ex: affichage JSON dans le terminal, messages en DM, etc.).

3. **Mettre à jour les erreurs (`docs/erreurs.md`)**
   - Documente toute nouvelle erreur rencontrée au cours du prompt et la solution apportée.
   - Ajoute des conseils de débogage si nécessaire.

4. commit et push dans la branche feature/valorant-rr-trackeret dans le main en fin de session

