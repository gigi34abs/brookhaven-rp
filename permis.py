import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
import io
import os

# --- 1. CONFIGURATION OFFICIELLE ---
# L'image doit être nommée exactement comme ça sur ton GitHub
TEMPLATE_PATH = "Permis_de_conduire.jpg" 

ROLE_ID_AUTORISE = 1221424452428890133
PSEUDO_AUTORISE = "g1.izzy_"

# Base de données (Archives de la Préfecture)
permis_db = {}

# --- 2. VÉRIFICATION DES ACCRÉDITATIONS ---
def est_agent_prefecture(interaction: discord.Interaction) -> bool:
    """Vérifie si l'utilisateur a les droits d'administration."""
    a_role = any(r.id == ROLE_ID_AUTORISE for r in interaction.user.roles)
    est_admin = interaction.user.name == PSEUDO_AUTORISE
    return a_role or est_admin

# --- 3. TRAITEMENT GRAPHIQUE ---
def appliquer_photo_identite(base_img, photo_bytes):
    """Prépare et colle la photo d'identité sur le document."""
    photo = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    # Zone d'affichage officielle (Rectangle gris)
    dimension_photo = (265, 355) 
    position_photo = (25, 110)
    
    photo_redimensionnee = photo.resize(dimension_photo, Image.Resampling.LANCZOS)
    base_img.paste(photo_redimensionnee, position_photo, photo_redimensionnee if photo_redimensionnee.mode == 'RGBA' else None)

def inscrire_donnees_identite(draw, nom, prenom, sexe, nationalite, lieu, points):
    """Inscrit les informations au style 𝚌𝚘𝚖𝚖𝚎 𝚜𝚊 (Courier)."""
    try:
        # Police Monospace pour un effet "Machine à écrire" réaliste
        font = ImageFont.truetype("Courier", 27)
    except:
        font = ImageFont.load_default()

    couleur_encre = (40, 40, 40) # Noir de type administratif

    # Coordonnées basées sur le formulaire officiel
    draw.text((375, 422), f"{nom.upper()}", fill=couleur_encre, font=font)
    draw.text((375, 532), f"{prenom}", fill=couleur_encre, font=font)
    draw.text((375, 642), f"{sexe.upper()}", fill=couleur_encre, font=font)
    draw.text((520, 642), f"{nationalite.upper()}", fill=couleur_encre, font=font)
    draw.text((375, 755), f"{lieu}", fill=couleur_encre, font=font)
    draw.text((375, 875), f"{points}/12", fill=couleur_encre, font=font)

# --- 4. SERVICES PRÉFECTORAUX (/permis ...) ---
class PermisGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="permis", description="Services administratifs de la Préfecture 🏛️")

    @app_commands.command(name="delivrer", description="Délivrer un nouveau permis de conduire")
    async def delivrer(self, interaction: discord.Interaction, citoyen: discord.Member, nom: str, prenom: str, sexe: str, nationalite: str, lieu: str, points: int, photo: discord.Attachment):
        """Procédure de création d'un titre de conduite."""
        if not est_agent_prefecture(interaction):
            return await interaction.response.send_message("⚠️ **Alerte Sécurité** : Vous ne disposez pas des accréditations nécessaires pour délivrer un titre officiel.", ephemeral=True)

        if not photo.content_type.startswith("image/"):
            return await interaction.response.send_message("❌ **Format Invalide** : Veuillez fournir une photo d'identité au format image.", ephemeral=True)

        await interaction.response.defer()

        try:
            # Création du document
            base = Image.open(TEMPLATE_PATH).convert("RGBA")
            photo_data = await photo.read()
            
            appliquer_photo_identite(base, photo_data)
            inscrire_donnees_identite(ImageDraw.Draw(base), nom, prenom, sexe, nationalite, lieu, points)

            # Enregistrement en mémoire
            buffer = io.BytesIO()
            base.save(buffer, format="PNG")
            img_officielle = buffer.getvalue()
            buffer.seek(0)

            permis_db[citoyen.id] = {
                "identite": f"{prenom} {nom.upper()}",
                "points": points,
                "document": img_officielle
            }

            file = discord.File(fp=buffer, filename=f"titre_conduite_{citoyen.id}.png")
            await interaction.followup.send(
                content=f"🏛️ **MINISTÈRE DE L'INTÉRIEUR**\n\nLe titre de conduite de {citoyen.mention} a été validé et enregistré sous le numéro d'archive `BKH-{citoyen.id}`.\n\n✅ **Statut** : En règle\n📍 **Lieu de délivrance** : Mairie de Brookhaven", 
                file=file
            )

        except Exception as e:
            await interaction.followup.send(f"⚠️ **Incident Technique** : Impossible de générer le document. Erreur : `{e}`")

    @app_commands.command(name="retrait_points", description="Sanctionner un conducteur (Retrait de points)")
    async def retrait(self, interaction: discord.Interaction, citoyen: discord.Member, points_en_moins: int):
        """Procédure de sanction routière."""
        if not est_agent_prefecture(interaction): return
        
        if citoyen.id in permis_db:
            nouveaux_points = max(0, permis_db[citoyen.id]["points"] - points_en_moins)
            permis_db[citoyen.id]["points"] = nouveaux_points
            
            await interaction.response.send_message(f"⚖️ **Sanction Routière** : {citoyen.mention} a été sanctionné. Nouveau solde : **{nouveaux_points}/12 points**.")
            if nouveaux_points == 0:
                await interaction.followup.send(f"🚨 **ALERTE** : Le permis de {citoyen.mention} est désormais invalide (Solde nul).")
        else:
            await interaction.response.send_message("🔎 **Erreur** : Ce citoyen ne figure pas dans nos fichiers.", ephemeral=True)

    @app_commands.command(name="revoquer", description="Annuler et supprimer un permis du registre")
    async def revoquer(self, interaction: discord.Interaction, citoyen: discord.Member):
        """Suppression définitive d'un dossier."""
        if not est_agent_prefecture(interaction): return
        
        if permis_db.pop(citoyen.id, None):
            await interaction.response.send_message(f"🗑️ **Archives** : Le dossier de {citoyen.display_name} a été détruit et son titre révoqué.")
        else:
            await interaction.response.send_message("🔎 **Erreur** : Dossier introuvable.", ephemeral=True)

# --- 5. CONSULTATION CITOYENNE ---
@app_commands.command(name="portefeuille", description="Consulter mes documents de conduite")
async def voir_portefeuille(interaction: discord.Interaction):
    """Permet au citoyen de voir sa carte grise / son permis."""
    user_id = interaction.user.id
    if user_id in permis_db:
        data = io.BytesIO(permis_db[user_id]["document"])
        file = discord.File(data, filename="permis_conduire.png")
        await interaction.response.send_message(f"🪪 **Documents Personnels de {interaction.user.mention}** :", file=file)
    else:
        await interaction.response.send_message("⚠️ **Information** : Vous ne possédez aucun titre de conduite enregistré à votre nom.", ephemeral=True)

# --- 6. EXPORT POUR LE MAIN.PY ---
# On prépare les objets pour l'importation propre
service_pref_instance = PermisGroup()
citoyen_cmd_instance = voir_portefeuille
