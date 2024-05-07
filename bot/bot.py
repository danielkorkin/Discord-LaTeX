import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv
import os
import time
import subprocess
from pylatex import Document, Math, NoEscape
from pdf2image import convert_from_path
import sympy as sp
import matplotlib.pyplot as plt
import numpy as np
# AI
import google.generativeai as genai

# Status
import cronitor

# Text stuff
from text import HELP_TEXT

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
GOOGLE_API_KEY=os.getenv('GOOGLE_API_KEY')
CRONITOR_API_KEY = os.getenv("CRONITOR_API_KEY")

cronitor.api_key = CRONITOR_API_KEY

MY_GUILD = discord.Object(id=GUILD_ID)  # Replace with your guild ID

# AI Config
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.0-pro")
prompt = "Provide just the LaTeX function for the following equation/expression, even if it is incorrect, follow strict LaTeX formatting however do not surround the raw equation/expression with anything "
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
    """Generate a PDF from the given LaTeX equation and convert it to PNG, ensuring visibility with padding."""
    wrapped_equation = NoEscape(f"\\[{equation}\\]")

    # Generate file paths
    current_timestamp = int(time.mktime(time.strptime("2024-01-01", "%Y-%m-%d")))
    epoch_time = str(int(time.time() - current_timestamp))
    output_dir = 'bot/tmp'
    os.makedirs(output_dir, exist_ok=True)
    base_filename = os.path.join(output_dir, f'{epoch_time}')
    pdf_filename = f'{base_filename}.pdf'
    png_filename = f'{base_filename}.png'

    # Create LaTeX document with a standalone class and geometry for padding
    doc = Document(documentclass='standalone', document_options=['12pt'])
    doc.packages.append(NoEscape(r'\usepackage[top=1in, bottom=1in, left=1in, right=1in]{geometry}'))  # Larger margins
    doc.packages.append(NoEscape(r'\usepackage{amsmath}'))
    with doc.create(Math(data=wrapped_equation)):
        pass

    # Compile LaTeX to PDF
    try:
        doc.generate_pdf(base_filename, clean_tex=True, compiler='pdflatex')
    except subprocess.CalledProcessError as e:
        print(f"LaTeX warnings: {e}")
    except Exception as e:
        raise RuntimeError(f"LaTeX Error: {e}")

    # Convert generated PDF to PNG
    try:
        pages = convert_from_path(pdf_filename)
        first_page = pages[0]
        first_page.save(png_filename, 'PNG')
    except Exception as e:
        raise RuntimeError(f"Error converting PDF to PNG: {e}")

    # Clean up auxiliary files
    for ext in ['.aux', '.log', '.tex', '.pdf']:
        file_path = f"{base_filename}{ext}"
        if os.path.exists(file_path):
            os.remove(file_path)

    return png_filename

def preprocess_expression(expression: str) -> str:
    expression = get_AI_prompt(expression)
    print(expression)

    # Further processing rules can be added here
    return expression


def plot_function(expression: str):

    # Strip 'y=' or 'f(x)=' if it exists to get just the RHS
    if '=' in expression:
        expression = expression.split('=')[1]

    # Preprocess the expression to correct common syntax issues
    expression = preprocess_expression(expression)

    # Create a range of x values
    x = np.linspace(-10, 10, 400)
    
    try:
        # Convert the string expression to a sympy expression and then to a numpy function
        expr = sp.sympify(expression)
        f = sp.lambdify(sp.Symbol('x'), expr, 'numpy')
        
        # Calculate y values based on the expression
        y = f(x)
        
        # Create the plot
        plt.figure(figsize=(8, 6))
        plt.plot(x, y, label=f"y = {expression}")
        plt.title(f"Plot of y = {expression}")
        plt.xlabel('x')
        plt.ylabel('y')
        plt.grid(True)
        plt.legend()

        # Save the plot to a file
        filename = 'plot.png'
        plt.savefig(filename)
        plt.close()

        return filename, None  # Return the filename and no error
    except Exception as e:
        return None, str(e)  # Return no filename and the error message

 
def get_AI_prompt(equation:str):
    response = model.generate_content(f"{prompt} {equation}")
    response = format_to_latex(response.text)

    try:
        response.replace("$", "")
    except Exception:
        pass

    return response

def format_to_latex(expression):
    # Replace implicit multiplication (e.g., '4x') with explicit (e.g., '4*x')
    terms = list(expression)  # Convert expression into a list of characters
    formatted_expression = []

    # Iterate over the characters to identify and format multiplication
    for i, char in enumerate(terms):
        # Check if a multiplication should be inserted
        if char.isdigit() and i+1 < len(terms) and terms[i+1].isalpha():
            formatted_expression.append(char + '*')
        else:
            formatted_expression.append(char)

    # Join all parts into a single string
    return ''.join(formatted_expression)

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

@client.tree.command()
@app_commands.describe(equation="Enter the equation in LaTeX format.")
async def render_ai(interaction: discord.Interaction, equation: str):
    """Render a expression and converts it to LaTeX with AI and then returns it as an image."""
    await interaction.response.defer(ephemeral=False, thinking=True)
    try:
        response = get_AI_prompt(equation)
        image_path = visualize_equation(response.text)
        with open(image_path, 'rb') as image_file:
            await interaction.followup.send(file=discord.File(image_file, os.path.basename(image_path)))
        os.remove(image_path)
    except RuntimeError as e:
        await interaction.followup.send(f"Error rendering the equation: {e}")
    except Exception as e:
        await interaction.followup.send("An unexpected error occurred while rendering the equation.")

@client.tree.context_menu(name="Render with AI")
async def render_ai(interaction: discord.Interaction, message: discord.Message):
    """Render a expression and converts it to LaTeX with AI and then returns it as an image."""
    await interaction.response.defer(ephemeral=False, thinking=True)
    try:
        response = get_AI_prompt(message.content.strip())
        image_path = visualize_equation(response.text)
        with open(image_path, 'rb') as image_file:
            await interaction.followup.send(file=discord.File(image_file, os.path.basename(image_path)))
        os.remove(image_path)
    except RuntimeError as e:
        await interaction.followup.send(f"Error rendering the equation: {e}")
    except Exception as e:
        await interaction.followup.send("An unexpected error occurred while rendering the equation.")

@client.tree.command()
@app_commands.describe(equation="Enter the equation in LaTeX format.")
@app_commands.choices(operation=[
    app_commands.Choice(name="Simplify", value="simplify"),
    app_commands.Choice(name="Factor", value="factor"),
    app_commands.Choice(name="Solve", value="solve"),
])
async def math_operation(interaction: discord.Interaction, equation: str, operation: str):
    """Perform a mathematical operation on a given equation."""
    await interaction.response.defer(ephemeral=False, thinking=True)

    equation = get_AI_prompt(equation)
    # Parse the equation string into a Sympy expression
    try:
        expr = sp.sympify(equation, evaluate=False)
    except sp.SympifyError as e:
        await interaction.followup.send(f"Error parsing the equation: {e}")
        return

    try:
        if operation == 'simplify':
            result = sp.simplify(expr)
        elif operation == 'factor':
            result = sp.factor(expr)
        elif operation == 'solve':
            # Assuming it's an equation and solving for x
            result = sp.solve(expr, sp.Symbol('x'))
        else:
            await interaction.followup.send("Unsupported operation. Please use 'simplify', 'factor', or 'solve'.")
            return

        # Render the result as LaTeX and create an image
        latex_result = sp.latex(result)
        image_path = visualize_equation(latex_result)
        with open(image_path, 'rb') as image_file:
            await interaction.followup.send(file=discord.File(image_file, os.path.basename(image_path)))
        os.remove(image_path)
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred while performing the operation: {e}")

@client.tree.command()
@app_commands.describe(expression="Enter the function expression, like 'x^2 - 3*x + 5'.")
async def plot(interaction: discord.Interaction, expression: str):
    """Plot a mathematical function based on the given expression."""
    await interaction.response.defer(ephemeral=False, thinking=True)
    
    image_path, error = plot_function(expression)
    if error:
        await interaction.followup.send(f"An error occurred while plotting the function: {error}")
    else:
        with open(image_path, 'rb') as image_file:
            await interaction.followup.send(file=discord.File(image_file, os.path.basename(image_path)))
        os.remove(image_path)

@client.tree.command()
async def latex_help(interaction: discord.Interaction):
    """Help for formatting and using the LaTeX system"""
    await interaction.response.send_message(HELP_TEXT, ephemeral=True)


# Run the client with the bot token
client.run(TOKEN)
