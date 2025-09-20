import discord

# Variables partagées
ORTHOGRAPHE_NEZ = ["nay", "nez", "nai", "naï", "n'est", "nait", "né", "née"]

# Méthodes pour la classe du bot
async def on_message(self, message):
    if message.author.bot:
        return

    content = message.content.lower().strip()

    if content.endswith("quoi"):
        await self.repondre(message, "feur")

    if content.endswith(tuple(ORTHOGRAPHE_NEZ)):
        await self.repondre(message, "gros")

async def repondre(self, message, texte):
    try:
        await message.channel.send(
            content=texte,
            reference=message,
            mention_author=True
        )
        print(f"Répondu '{texte}' au message de {message.author}")
    except Exception as e:
        print("Erreur lors de l'envoi :", e)