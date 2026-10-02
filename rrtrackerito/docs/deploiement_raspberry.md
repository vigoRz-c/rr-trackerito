# Guide de Déploiement sur Raspberry Pi (Linux)

Ce guide détaille les étapes pour transférer et exécuter le bot **RR Trackerito** de façon permanente sur un Raspberry Pi (ou n'importe quel serveur Linux).

## Étape 1 : Préparer le Raspberry Pi

Assurez-vous que Python 3 et `pip` sont installés sur votre Raspberry Pi :
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git
```

## Étape 2 : Transférer les fichiers sur le Raspberry Pi

Via GitHub (méthode la plus propre car elle permet de mettre à jour le bot facilement.)

1. **Sur votre PC** : Assurez-vous que votre code est poussé (Push) sur GitHub.
2. **Sur le Raspberry Pi** : Cloner le dépôt.
   ```bash
   cd /home/pi
   git clone https://github.com/VOTRE_NOM/rrtrackerito.git
   cd rrtrackerito
   ```


## Étape 3 : Installer les dépendances

Une fois les fichiers transférés, connectez-vous au Raspberry Pi via SSH (ou ouvrez un terminal dessus) et naviguez dans le dossier du bot :

```bash
cd /home/pi/rrtrackerito
```

Il est fortement recommandé de créer un environnement virtuel (venv) pour ne pas polluer le système du Raspberry :
```bash
python3 -m venv venv
source venv/bin/activate
```

Installez ensuite les librairies requises :
```bash
pip install -r requirements.txt
```
*(Assurez-vous d'avoir un fichier `requirements.txt` généré via `pip freeze > requirements.txt` sur votre PC Windows)*.

## Étape 4 : Configurer le service Systemd (24/7)

Pour que le bot tourne en arrière-plan et redémarre automatiquement en cas de plantage ou de coupure de courant, on utilise le fichier `rrtrackerito.service`.

1. **Vérifier le chemin** : Le fichier `scripts/linux/rrtrackerito.service` pointe par défaut vers `/home/pi/rrtrackerito`. Si vous avez utilisé un environnement virtuel (recommandé), modifiez la ligne `ExecStart` du service pour utiliser l'exécutable Python du venv :
   ```ini
   ExecStart=/home/pi/rrtrackerito/venv/bin/python3 /home/pi/rrtrackerito/rrtrackerito.py
   ```
2. **Copier le service** :
   ```bash
   sudo cp scripts/linux/rrtrackerito.service /etc/systemd/system/
   ```
3. **Recharger systemd** :
   ```bash
   sudo systemctl daemon-reload
   ```
4. **Activer au démarrage** :
   ```bash
   sudo systemctl enable rrtrackerito.service
   ```
5. **Démarrer le bot** :
   ```bash
   sudo systemctl start rrtrackerito.service
   ```

## Étape 5 : Gérer le Bot au quotidien

- **Vérifier le statut / voir si le bot est connecté :**
  ```bash
  sudo systemctl status rrtrackerito.service
  ```
- **Voir les logs complets (pour débugger en direct) :**
  ```bash
  sudo journalctl -u rrtrackerito.service -f
  ```
- **Redémarrer après avoir fait une mise à jour du code (git pull) :**
  ```bash
  sudo systemctl restart rrtrackerito.service
  ```
- **Couper le bot (mise hors ligne) :**
  ```bash
  sudo systemctl stop rrtrackerito.service
  ```
