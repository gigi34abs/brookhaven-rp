import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import os
import aiohttp

# --- CONFIGURATION FIXE (Modifie ces valeurs si nécessaire) ---
# Chemin vers ton image de base (template) sur GitHub. Renomme ton image template.jpg.
TEMPLATE_PATH = "Permis_de_conduire.png"
# L'ID du rôle Discord autorisé à utiliser la commande d'enregistrement.
ROLE_ID_AUTORISE = 1221424452428890133
# Le pseudo exact de l'utilisateur autorisé (sans le hashtag ni l'ID).
PSEUDO_AUTORISE = "g1.izzy_"

# --- BASE DE DONNÉES TEMPORAIRE (Se vide si le bot redémarre) ---
# Pour une solution persistante, il faudrait utiliser une vraie base de données (SQL, JSON, etc.).
permis_db = {}

def a_la_permission(interaction: discord.Interaction) -> bool:
    """Vérifie si l'utilisateur a le droit d'utiliser la commande d'enregistrement."""
    # Vérifie si l'utilisateur a le rôle spécifique
    a_role = any(r.id == ROLE_ID_AUTORISE for r in interaction.user.roles)
    # Vérifie si c'est l'utilisateur spécifique par pseudo
    est_utilisateur = interaction.user.name == PSEUDO_AUTORISE
    return a_role or est_utilisateur

def inserer_image_avatar(base_img, avatar_img):
    """Redimensionne et paste l'image de l'avatar dans le rectangle de gauche."""
    # Coordonnées et taille du grand rectangle gris à gauche sur ton image.
    # Ces valeurs sont des approximations basées sur l'image que tu as fournie.
    cadre_photo_coords = (25, 110) # Position du coin haut-gauche
    taille_photo_requise = (265, 355) # Taille que la photo doit faire

    # Redimensionnement de la photo avec un algorithme de haute qualité pour qu'elle s'adapte au cadre.
    avatar_img = avatar_img.resize(taille_photo_requise, Image.Resampling.LANCZOS)
    
    # On colle l'avatar sur l'image de base. Si l'avatar est un PNG transparent, le fond sera conservé.
    # S'il a un décor, le décor sera visible mais redimensionné.
    base_img.paste(avatar_img, cadre_photo_coords, avatar_img if avatar_img.mode == 'RGBA' else None)

def dessiner_champs_texte(draw_ctx, nom, prenom, sexe, nationalite, lieu, points):
    """Dessine tous les champs textuels sur l'image avec les coordonnées ajustées."""
    # On essaie de charger une police d'écriture claire. Si elle n'est pas trouvée, on prend celle par défaut.
    try:
        # Pour utiliser Arial, tu dois uploader arial.ttf dans ton dépôt GitHub.
        font_main = ImageFont.truetype("arial.ttf", 26)
    except:
        font_main = ImageFont.load_default()

    # Couleur du texte (noir légèrement gris pour un rendu naturel).
    couleur_texte = (30, 30, 30)

    # Dessin des textes un par un à des coordonnées spécifiques (à ajuster lors de tes tests).
    # draw_ctx.text((X, Y), "Texte à écrire", fill=couleur_texte, font=font_main)
    draw_ctx.text((375, 422), nom.upper(), fill=couleur_texte, font=font_main) # NOM (en majuscules)
    draw_ctx.text((375, 532), prenom, fill=couleur_texte, font=font_main) # Prénoms
    draw_ctx.text((375, 642), sexe.upper(), fill=couleur_texte, font=font_main) # Sexe
    draw_ctx.text((520, 642), nationalite.upper(), fill=couleur_texte, font=font_main) # Nationalité
    draw_ctx.text((375, 755), lieu, fill=couleur_texte, font=font_main) # Lieu de naissance
    draw_ctx.text((375, 875), f"{points}/12", fill=couleur_texte, font=font_main) # Points

# --- CLASSE DE COMMANDE GROUPÉE ---
# Cela permet d'avoir la structure /permis enregistrer, /permis points, etc.
class PermisGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="permis", description="Bureau de gestion des permis de conduire de Brookhaven")

    # --- COMMANDE /permis enregistrer ---
    @app_commands.command(name="enregistrer", description="Créer et enregistrer un nouveau permis de conduire")
    @app_commands.describe(
        citoyen="Le citoyen à qui attribuer le permis",
        nom="NOM de famille (en majuscules)",
        prenom="Prénoms",
        sexe="Sexe (M pour masculin, F pour féminin)",
        nationalite="Nationalité (ex: FRANÇAISE)",
        lieu="Lieu de naissance",
        points="Nombre de points sur 12",
        photo="Image du personnage Roblox (Sera recadrée pour le permis)"
    )
    async def enregistrer(
        self,
        interaction: discord.Interaction, 
        citoyen: discord.Member, 
        nom: str, 
        prenom: str, 
        sexe: str, 
        nationalite: str, 
        lieu: str, 
        points: int, 
        photo: discord.Attachment
    ):
        # 1. Vérification stricte des permissions.
        if not a_la_permission(interaction):
            return await interaction.response.send_message("❌ Erreur : Vous n'êtes pas autorisé à utiliser cette commande.", ephemeral=True)

        # 2. Vérification que le fichier envoyé est bien une image.
        if not photo.content_type.startswith("image/"):
            return await interaction.response.send_message("❌ Erreur : Le fichier envoyé doit être une image.", ephemeral=True)

        # 3. On "signale" à Discord que la commande est prise en compte mais que le traitement peut être long.
        # Cela évite que la commande n'expire (timeout).
        await interaction.response.defer()

        try:
            # 4. Vérification que le fichier template.jpg existe sur le serveur.
            if not os.path.exists(TEMPLATE_PATH):
                return await interaction.followup.send(f"❌ Erreur critique : Le fichier `{TEMPLATE_PATH}` est introuvable sur GitHub. Assurez-vous qu'il soit bien présent dans le même dossier que ce code.")

            # 5. Chargement de l'image de base (le template) et conversion en RGBA pour gérer la transparence.
            base_image = Image.open(TEMPLATE_PATH).convert("RGBA")
            
            # 6. Téléchargement et ouverture de l'image de l'avatar fournie par l'utilisateur.
            photo_bytes = await photo.read()
            avatar_image = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
            
            # 7. Insertion de l'avatar redimensionné dans le cadre photo.
            inserer_image_avatar(base_image, avatar_image)

            # 8. Initialisation du contexte de dessin pour écrire sur l'image.
            drawing_context = ImageDraw.Draw(base_image)
            
            # 9. Écriture de tous les champs de texte sur l'image.
            dessiner_champs_texte(drawing_context, nom, prenom, sexe, nationalite, lieu, points)

            # 10. Préparation de l'envoi de l'image finale.
            final_buffer = io.BytesIO()
            base_image.save(final_buffer, format="PNG") # On sauvegarde en PNG pour conserver la qualité
            final_buffer.seek(0)
            
            # 11. Sauvegarde en mémoire du permis généré pour les commandes futures (/permis).
            # Note : C'est temporaire. Si le bot redémarre, ces données seront perdues.
            permis_db[citoyen.id] = {
                "nom": nom,
                "points": points,
                "donnees_image": final_buffer.getvalue() # On stocke les bytes de l'image
            }

            # 12. Création de l'objet de fichier Discord et envoi de l'image finale.
            discord_file = discord.File(fp=final_buffer, filename=f"permis_valide_{citoyen.id}.png")
            await interaction.followup.send(content=f"✅ Permis de conduire généré avec succès pour {citoyen.mention} !", file=discord_file)

        except Exception as e:
            # Gestion globale des erreurs pour éviter que le bot ne crash.
            await interaction.followup.send(f"⚠️ Une erreur technique est survenue lors de la génération : {str(e)}")

    # --- COMMANDE /permis points ---
    @app_commands.command(name="points", description="Modifier le solde de points d'un permis existant")
    @app_commands.describe(citoyen="Le membre Discord", nouveaux_points="Nouveau nombre de points (ex: 10)")
    async def modifier_points(self, interaction: discord.Interaction, citoyen: discord.Member, nouveaux_points: int):
        # Seuls les admins (toi et le rôle spécifique) peuvent modifier les points.
        if not a_la_permission(interaction): return

        if citoyen.id in permis_db:
            permis_db[citoyen.id]["points"] = nouveaux_points
            await interaction.response.send_message(f"✅ Points mis à jour pour {citoyen.display_name}. Nouveau solde : {nouveaux_points}/12.")
        else:
            await interaction.response.send_message("❌ Aucun permis n'est enregistré pour ce membre.", ephemeral=True)

    # --- COMMANDE /permis supprimer ---
    @app_commands.command(name="supprimer", description="Supprimer définitivement un permis de la base de données")
    @app_commands.describe(citoyen="Le membre Discord dont le permis doit être supprimé")
    async def supprimer_permis(self, interaction: discord.Interaction, citoyen: discord.Member):
        # Seuls les admins peuvent supprimer un permis.
        if not a_la_permission(interaction): return

        if citoyen.id in permis_db:
            del permis_db[citoyen.id]
            await interaction.response.send_message(f"🗑️ Le permis de conduire de {citoyen.display_name} a été supprimé de la mairie.")
        else:
            await interaction.response.send_message("❌ Aucun permis trouvé pour ce membre.", ephemeral=True)

# --- COMMANDE GLOBALE /permis ---
# Cette commande est publique et permet à un joueur de voir son propre permis.
# Elle est définie en dehors de la classe PermisGroup car c'est la commande principale.
@app_commands.command(name="permis", description="Afficher votre propre permis de conduire Brookhaven s'il est enregistré")
async def voir_permis(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # On vérifie si l'utilisateur a un permis enregistré en mémoire.
    if user_id in permis_db:
        # On récupère les bytes de l'image stockés.
        image_data = io.BytesIO(permis_db[user_id]["donnees_image"])
        
        # On crée le fichier à envoyer à Discord.
        discord_file = discord.File(fp=image_data, filename="mon_permis_de_conduire.png")
        
        # On envoie l'image finale.
        await interaction.response.send_message(f"Voici votre permis {interaction.user.mention} :", file=discord_file)
    else:
        # Si aucun permis n'est trouvé, on envoie un message d'erreur.
        await interaction.response.send_message("❌ Aucun permis de conduire n'est actuellement enregistré à votre nom au bureau de la mairie.", ephemeral=True)
