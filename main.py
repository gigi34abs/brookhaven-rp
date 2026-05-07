import discord
from discord.ext import commands
import os
# Tu n'auras pas besoin de python-dotenv sur Railway, 
# car Railway gère les variables d'environnement directement.
# Mais pour tester chez toi, c'est utile.
from dotenv import load_dotenv

# On importe les groupes de commandes et la commande simple depuis le fichier permis.py
from permis import PermisGroup, voir_permis

# Chargement du Token (si présent localement dans un .env)
load_dotenv()
TOKEN = os.getenv('TOKEN')

# --- CONFIGURATION DU BOT ---
# On définit une classe personnalisée pour le bot pour gérer proprement la synchronisation des commandes slash.
class MyBot(commands.Bot):
    def __init__(self):
        # Définition des "Intents" (permissions) nécessaires.
        # intents.members = True est requis pour interagir avec les membres du serveur (@mentions).
        intents = discord.Intents.default()
        intents.members = True
        
        # On appelle le constructeur de la classe parente.
        super().__init__(command_prefix="!", intents=intents)

    # Cette méthode est appelée une fois que le bot est connecté à Discord.
    async def setup_hook(self):
        # 1. Ajout du groupe de commandes structuré (/permis enregistrer, etc.).
        self.tree.add_command(PermisGroup())
        
        # 2. Ajout de la commande simple publique (/permis).
        self.tree.add_command(voir_permis)
        
        # 3. Synchronisation des commandes slash avec l'API Discord.
        # Cela les rendra visibles et utilisables dans l'interface Discord.
        await self.tree.sync()
        print("✅ Système de permis chargé et synchronisé avec succès.")

# Instanciation du bot personnalisé.
bot = MyBot()

# Événement déclenché lorsque le bot est prêt et en ligne.
@bot.event
async def on_ready():
    print(f"🚀 Bot en ligne en tant que : {bot.user.name} (ID: {bot.user.id})")
    print("------")

# Point d'entrée principal pour lancer le bot.
if __name__ == "__main__":
    if TOKEN:
        # Lancement du bot avec le token récupéré.
        bot.run(TOKEN)
    else:
        # Message d'erreur critique si le token est manquant.
        print("ERREUR CRITIQUE : Le TOKEN n'a pas été trouvé dans les variables d'environnement !")
