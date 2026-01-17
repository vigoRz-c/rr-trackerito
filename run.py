#!/usr/bin/env python3
"""
Script de lancement pour le bot Discord neckhurts
Permet l'exécution avec des imports relatifs
"""

import sys
import os

# Ajouter le répertoire du projet au Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Importer et exécuter le module neckhurts
if __name__ == "__main__":
    # Changer le répertoire de travail vers neckhurts
    os.chdir(os.path.join(project_dir, 'neckhurts'))
    
    # Exécuter le fichier neckhurts.py en tant que module
    import runpy
    runpy.run_path('neckhurts.py', run_name='__main__')