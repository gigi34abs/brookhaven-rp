import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
# On importe les commandes depuis notre autre fichier
from permis import PermisGroup, voir_permis

load_dotenv()
TOKEN = os.getenv('TOKEN')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Ajout du groupe de commandes /permis enregistrer/points/supprimer
        self.tree.add_command(PermisGroup())
        # Ajout de la commande simple /permis
        self.tree.add_command(voir_permis)
        
        await self.tree.sync()
        print("✅ Système de permis chargé et synchronisé.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🚀 Bot connecté : {bot.user.name}")

if __name__ == "__main__":
    bot.run(TOKEN)
