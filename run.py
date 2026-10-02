#!/usr/bin/env python3
"""
Script de lancement pour le bot Discord rrtrackerito
Permet l'exécution avec des imports relatifs
"""

import sys
import os

# Ajouter le répertoire du projet au Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importer et exécuter le module rrtrackerito
if __name__ == "__main__":
    # Changer le répertoire de travail vers rrtrackerito
    os.chdir(os.path.join(project_dir, 'rrtrackerito'))
    
    # Exécuter le fichier rrtrackerito.py en tant que module
    import runpy
    runpy.run_path('rrtrackerito.py', run_name='__main__')