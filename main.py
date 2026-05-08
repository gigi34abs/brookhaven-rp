import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# ON IMPORTE LES NOUVEAUX NOMS DE LA VERSION VRAI VIE
from permis import service_pref_instance, citoyen_cmd_instance

load_dotenv()
TOKEN = os.getenv('TOKEN')

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # 1. On ajoute les services de la préfecture (/permis delivrer, etc.)
        self.tree.add_command(service_pref_instance)
        
        # 2. On ajoute la commande portefeuille (/portefeuille)
        self.tree.add_command(citoyen_cmd_instance)
        
        await self.tree.sync()
        print("✅ Système administratif de la Préfecture synchronisé !")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🚀 Préfecture de Brookhaven en ligne : {bot.user.name}")

if __name__ == "__main__":
    bot.run(TOKEN)
