import discord
from discord import app_commands
from dotenv import load_dotenv
import os
import time
import subprocess
from pylatex import Document, Math, NoEscape
from pdf2image import convert_from_path

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

MY_GUILD = discord.Object(id=GUILD_ID)  # Replace with your guild ID

# Create the bot client
class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

# Initialize intents
intents = discord.Intents.default()
client = MyClient(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('------')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Mathematical Equations 🤓"))

def visualize_equation(equation: str):
    """Generate a PDF from the given LaTeX equation and convert it to PNG."""
    wrapped_equation = NoEscape(f"\\[{equation}\\]")

    # Create filenames based on the current timestamp
    current_timestamp = int(time.mktime(time.strptime("2024-01-01", "%Y-%m-%d")))
    epoch_time = str(int(time.time() - current_timestamp))
    output_dir = 'bot/tmp'
    os.makedirs(output_dir, exist_ok=True)
    base_filename = os.path.join(output_dir, f'{epoch_time}')
    pdf_filename = f'{base_filename}.pdf'
    png_filename = f'{base_filename}.png'

    # Create a LaTeX document with a standalone class
    doc = Document(documentclass='standalone')
    doc.packages.append(NoEscape(r'\usepackage{amsmath}'))
    with doc.create(Math(data=wrapped_equation)):
        pass

    try:
        doc.generate_pdf(base_filename, clean_tex=True, compiler='pdflatex')
    except subprocess.CalledProcessError as e:
        print(f"LaTeX warnings: {e}")
    except Exception as e:
        raise RuntimeError(f"LaTeX Error: {e}")

    try:
        pages = convert_from_path(pdf_filename)
        first_page = pages[0]
        # Crop or adjust the image size as needed
        first_page_cropped = first_page.crop((0, 0, first_page.width, first_page.height // 2))
        first_page_cropped.save(png_filename, 'PNG')
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to PNG: {e}")

    for ext in ['.aux', '.log', '.tex', '.pdf']:
        file_path = f"{base_filename}{ext}"
        if os.path.exists(file_path):
            os.remove(file_path)

    return png_filename

@client.tree.command()
@app_commands.describe(equation="Enter the equation in LaTeX format.")
async def render(interaction: discord.Interaction, equation: str):
    """Render a LaTeX equation and return it as an image."""
    try:
        image_path = visualize_equation(equation)
        with open(image_path, 'rb') as image_file:
            await interaction.response.send_message(file=discord.File(image_file, os.path.basename(image_path)))
        os.remove(image_path)
    except RuntimeError as e:
        await interaction.response.send_message(f"Error rendering the equation: {e}")
    except Exception as e:
        await interaction.response.send_message("An unexpected error occurred while rendering the equation.")

@client.tree.context_menu(name="Render LaTeX")
async def render_latex_menu(interaction: discord.Interaction, message: discord.Message):
    """Render a LaTeX equation from a context menu command."""
    equation = message.content.strip()
    if equation:
        try:
            image_path = visualize_equation(equation)
            with open(image_path, 'rb') as image_file:
                await interaction.response.send_message(file=discord.File(image_file, os.path.basename(image_path)))
            os.remove(image_path)
        except RuntimeError as e:
            await interaction.response.send_message(f"Error rendering the equation: {e}")
        except Exception as e:
            await interaction.response.send_message("An unexpected error occurred while rendering the equation.")
    else:
        await interaction.response.send_message("The message doesn't contain any content.")

# Run the client with the bot token
client.run(TOKEN)
