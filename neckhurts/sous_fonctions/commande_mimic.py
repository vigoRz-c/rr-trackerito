import discord
from discord import app_commands
import random
import re
from ..les_textes.remplacements_phonetiques import REMPLACEMENTS_PHONETIQUES

# ID du propriétaire du bot (immunisé)
mon_id = 784106722615754772

def mimic_text(text: str) -> str:
    """Transforme le texte pour imiter quelqu'un avec des fautes phonétiques et alternances majuscules/minuscules."""
    
    # Alternance aléatoire majuscules/minuscules d'abord
    resultat = ""
    for caractere in text:
        if caractere.isalpha():
            resultat += caractere.upper() if random.random() > 0.9 else caractere.lower()
        else:
            resultat += caractere
    
    # Remplacements phonétiques (importés depuis le fichier séparé)
    remplacements_phonetiques = REMPLACEMENTS_PHONETIQUES
    
    # Traitement mot par mot avec limite de 2 remplacements par mot
    mots = resultat.split()
    nouveaux_mots = []
    
    for mot in mots:
        mot_modifie = mot
        remplacements_mot = 0
        max_remplacements_par_mot = 1
        
        for ancien, nouveau in remplacements_phonetiques:
            if remplacements_mot >= max_remplacements_par_mot:
                break
            if ancien in mot_modifie.lower():
                # Chance de 30% de faire le remplacement
                if random.random() < 0.3:
                    # Trouver la première occurrence et remplacer
                    position = mot_modifie.lower().find(ancien.lower())
                    if position != -1:
                        partie_originale = mot_modifie[position:position+len(ancien)]
                        # Appliquer la même casse
                        if partie_originale.isupper():
                            nouvelle_partie = nouveau.upper()
                        elif partie_originale.istitle():
                            nouvelle_partie = nouveau.capitalize()
                        else:
                            nouvelle_partie = nouveau.lower()
                        
                        mot_modifie = mot_modifie[:position] + nouvelle_partie + mot_modifie[position+len(ancien):]
                        remplacements_mot += 1
        
        nouveaux_mots.append(mot_modifie)
    
    return ' '.join(nouveaux_mots)

@app_commands.command(name="mimic", description="Imite le dernier message d'un utilisateur avec du texte déformé")
@app_commands.describe(user="L'utilisateur à imiter")
async def mimic(interaction: discord.Interaction, user: discord.User):
    """Commande slash pour imiter le dernier message d'un utilisateur avec du texte déformé."""
    
    # Vérification de l'immunité : seul le propriétaire peut être ciblé par lui-même
    if user.id == mon_id and interaction.user.id != mon_id:
        await interaction.response.send_message("❌ Vous ne pouvez pas cibler cet utilisateur.", ephemeral=True)
        return
    
    # Vérification : impossible de se mimic soi-même (sauf pour le propriétaire qui peut se tester)
    if user.id == interaction.user.id and interaction.user.id != mon_id:
        await interaction.response.send_message("❌ Vous ne pouvez pas vous imiter vous-même !", ephemeral=True)
        return
    
    # Recherche du dernier message de l'utilisateur dans le canal
    try:
        dernier_message = None
        async for message in interaction.channel.history(limit=100):
            if message.author.id == user.id and not message.author.bot:
                dernier_message = message
                break
        
        if not dernier_message:
            await interaction.response.send_message(f"❌ Aucun message récent trouvé pour {user.display_name} dans ce canal.", ephemeral=True)
            return
        
        if not dernier_message.content.strip():
            await interaction.response.send_message(f"❌ Le dernier message de {user.display_name} est vide ou ne contient que des fichiers.", ephemeral=True)
            return
        
        # Application de la déformation au message
        texte_deforme = mimic_text(dernier_message.content)
        
        await interaction.response.send_message(texte_deforme)
        
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de lire l'historique des messages de ce canal.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur lors de la récupération du message : {str(e)}", ephemeral=True)

# Export de la commande pour l'import dans le bot principal
mimic = mimic
