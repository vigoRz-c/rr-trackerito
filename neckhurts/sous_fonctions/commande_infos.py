import discord
from discord import app_commands
import random
import datetime
import os
import sys

mon_id = 784106722615754772  # À synchroniser avec le fichier principal si besoin

def get_resource_path():
    """Retourne le chemin vers les ressources, compatible avec PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # Nous sommes dans un exécutable PyInstaller
        return sys._MEIPASS
    else:
        # Nous sommes en mode développement
        return os.path.dirname(os.path.dirname(__file__))

def lire_liste_csv(fichier):
    """Lit un fichier texte (1 valeur par ligne) et retourne la liste des valeurs non vides."""
    valeurs = []
    try:
        with open(fichier, encoding="utf-8") as f:
            for ligne in f:
                valeur = ligne.strip()
                if valeur:
                    valeurs.append(valeur)
    except FileNotFoundError:
        print(f"❌ Fichier '{fichier}' introuvable !")
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier '{fichier}': {e}")
    return valeurs

BASE_PATH = get_resource_path()
NOMS_POKEMON = lire_liste_csv(os.path.join(BASE_PATH, "les_textes", "pokemon_g1-6.csv"))
FETICHES = lire_liste_csv(os.path.join(BASE_PATH, "les_textes", "fetiches.csv"))
PLATS = lire_liste_csv(os.path.join(BASE_PATH, "les_textes", "plats.csv"))
VIRGIN = lire_liste_csv(os.path.join(BASE_PATH, "les_textes", "virgin.csv"))

if not NOMS_POKEMON:
    print("❌ Aucun Pokémon chargé ! Vérifie le fichier 'pokemon_g1-6.csv'.")
if not FETICHES:
    print("❌ Aucun fétiche chargé ! Vérifie le fichier 'fetiches.csv'.")
if not PLATS:
    print("❌ Aucun plat chargé ! Vérifie le fichier 'plats.csv'.")
if not VIRGIN:
    print("❌ Aucun virgin chargé ! Vérifie le fichier 'virgin.csv'.")

@app_commands.command(name="infos", description="Balance des infos (100% vraies) sur un utilisateur")
@app_commands.describe(user="La victime (optionnel)")
async def infos(interaction: discord.Interaction, user: discord.User = None):
    target = user or interaction.user
    today = datetime.date.today().strftime("%Y-%m-%d")
    seed = str(target.id) + today
    local_random = random.Random(seed)

    if target.id == mon_id:
        virgin_list = []
        puceau_chance = 0
    else:
        virgin_list = VIRGIN
        puceau_chance = local_random.randint(0, 100)

    teub_size = local_random.randint(1, 35)
    last_fap_days = local_random.randint(0, 15)
    qi = local_random.randint(45, 180)
    porn_time = local_random.randint(0, 40)
    virginité = local_random.choice(virgin_list) if virgin_list else "gros baiseur"

    fetish = local_random.choice(FETICHES) if FETICHES else "aucun"
    pokemon_pref = local_random.choice(NOMS_POKEMON) if NOMS_POKEMON else "Aucun (liste vide)"
    plat_deteste = local_random.choice(PLATS) if PLATS else "aucun"

    msg = (
        f"📊 **Dossier secret sur {target.mention}** 📊\n"
        f"- Taille de teub : **{teub_size} cm** 🍆\n"
        f"- Dernière branlette : **il y a {last_fap_days} heures** ✋💦\n"
        f"- Plus grand fétiche : **{fetish}** 🔥\n"
        f"- QI estimé : **{qi}** 🧠\n"
        f"- Heures passées sur Pornhub cette semaine : **{porn_time}h** 🍑\n"
        f"- Pokémon préféré : **{pokemon_pref}** 🎮\n"
        f"- Plat le plus détesté : **{plat_deteste}** 🍽️\n"
        f"- Niveau de virginité : **{virginité}** 🕊️\n"
        f"- Chance d’être encore puceau : **{puceau_chance}%** 📉"
    )

    await interaction.response.send_message(msg)

# Export de la commande pour l'import dans le bot principal
infos = infos