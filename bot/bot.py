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
from scipy.stats import linregress
from io import BytesIO
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

MONITOR_NAME = "discord-latex-bot"
cronitor.api_key = CRONITOR_API_KEY
monitor = cronitor.Monitor(MONITOR_NAME)

MY_GUILD = discord.Object(id=GUILD_ID)  # Replace with your guild ID

# AI Config
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.0-pro")
prompt = "Provide just the LaTeX function for the following equation/expression, even if it is incorrect, follow strict LaTeX formatting however do not surround the raw equation/expression with anything "

class MetaCalculatorButton(discord.ui.View):
    def __init__(self, expression):
        super().__init__()
        # Create the URL link for Meta Calculator
        url = self.create_meta_calculator_url(expression)
        # Add a button to the view
        self.add_item(discord.ui.Button(label="View in Meta Calculator", url=url, style=discord.ButtonStyle.url))

    @staticmethod
    def create_meta_calculator_url(expression):
        from urllib.parse import quote
        # Properly URL encode the expression
        encoded_expression = quote(expression)
        # Return the full URL for Meta Calculator with the encoded expression
        return f"https://www.meta-calculator.com/?panel-101-equations&data-bounds-xMin=-8&data-bounds-xMax=8&data-bounds-yMin=-11&data-bounds-yMax=11&data-equations-0=%22{encoded_expression}%22&data-rand=undefined&data-hideGrid=false"


class InputModal(discord.ui.Modal):
    def __init__(self, button, view):
        super().__init__(title="Enter Value")
        self.button = button
        self.view = view
        # Add a text input field to the modal
        self.value_input = discord.ui.TextInput(label="Enter a number", style=discord.TextStyle.short)
        self.add_item(self.value_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Update the button label with the entered value
        self.button.label = self.value_input.value
        self.button.disabled = True  # Optionally disable the button after input
        # Update the message with the new view state
        await interaction.response.edit_message(view=self.view)

class TableButton(discord.ui.Button):
    def __init__(self, row, col, label):
        # Initialize with dynamic labels indicating their purpose
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.row = row
        self.col = col

    async def callback(self, interaction: discord.Interaction):
        # The modal can capture the input value
        modal = InputModal(button=self, view=self.view)
        await interaction.response.send_modal(modal)


class TableInputView(discord.ui.View):
    def __init__(self, rows):
        super().__init__()
        # Initialize buttons in a grid format based on the number of rows
        for i in range(rows):
            # Add a button for X value in column 0
            self.add_item(TableButton(row=i, col=0, label=f"Input {i}, X"))
            # Add a button for Y value in column 1
            self.add_item(TableButton(row=i, col=1, label=f"Input {i}, Y"))
        # Add a submit button at the end
        self.add_item(SubmitButton(data=rows))

class ScatterPlotButton(discord.ui.Button):
    def __init__(self, data):
        super().__init__(label="Show Scatter Plot with Best Fit", style=discord.ButtonStyle.secondary)
        self.data = data  # Pass the x_values and y_values

    async def callback(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer()
        x_values, y_values = self.data
        # Calculate the line of best fit
        slope, intercept, r_value, _, _ = linregress(x_values, y_values)
        line = slope * np.array(x_values) + intercept

        # Generate the plot
        plt.figure(figsize=(8, 6))
        plt.scatter(x_values, y_values, color='blue', label='Data Points')
        plt.plot(x_values, line, color='red', label=f'Best Fit Line: y={slope:.2f}x+{intercept:.2f}')
        plt.title(f"Scatter Plot with Line of Best Fit\nCorrelation Coefficient: {r_value:.2f}")
        plt.xlabel('X Values')
        plt.ylabel('Y Values')
        plt.legend()
        plt.grid(True)

        # Save and send the updated plot
        filename = 'scatter_plot.png'
        plt.savefig(filename)
        plt.close()

        # Use followup to send the file after initial interaction has been deferred
        file = discord.File(filename, filename='scatter_plot.png')
        await interaction.followup.send(content="Updated to Scatter Plot with Best Fit", file=file)
        os.remove(filename)

class SubmitButton(discord.ui.Button):
    def __init__(self, data):
        super().__init__(label="Submit Table", style=discord.ButtonStyle.success, row=data)
        self.data = data

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        plot_path = self.create_plot(view)
        x_values, y_values = self.extract_data(view)
        file = discord.File(plot_path, filename="plot.png")
        
        # Add the ScatterPlotButton with the data
        button_view = discord.ui.View()
        button_view.add_item(ScatterPlotButton((x_values, y_values)))
        
        await interaction.response.send_message(file=file, view=button_view)
        os.remove(plot_path)

    def extract_data(self, view):
        x_values = [float(view.children[i * 2].label.split()[-1]) for i in range(self.data)]
        y_values = [float(view.children[i * 2 + 1].label.split()[-1]) for i in range(self.data)]
        return x_values, y_values

    def create_plot(self, view):
        x_values = []
        y_values = []
        # Loop through each row and gather x and y values
        for i in range(self.data):  # 'data' contains the number of rows
            x_values.append(float(view.children[i * 2].label.split()[-1]))  # x values are in even index positions
            y_values.append(float(view.children[i * 2 + 1].label.split()[-1]))  # y values are in odd index positions

        plt.figure(figsize=(8, 6))
        plt.plot(x_values, y_values, 'bo-')  # Plot with blue circle markers connected by lines
        plt.title("Plot of Data Points")
        plt.xlabel('X Values')
        plt.ylabel('Y Values')
        plt.grid(True)
        filename = 'plot.png'
        plt.savefig(filename)
        plt.close()
        return filename

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

@tasks.loop(minutes=5)
async def send_periodic_request():
    guild_count = len(client.guilds)
    ping = round(client.latency * 1000)
    monitor.ping(metrics={'guilds': guild_count, 'ping': ping})

@send_periodic_request.before_loop
async def before_send_request():
    await client.wait_until_ready()
    print("Starting periodic check-ins.")

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

    try:
        response.replace("\(", "")
        response.replace("\)", "")
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

# Function to plot a triangle
def plot_triangle(a, b, c):
    # Calculate the coordinates based on the triangle inequality and angles
    coords = [(0, 0), (a, 0)]  # Start with two points
    # Use law of cosines to find the angle between the sides
    angle = np.arccos((a**2 + b**2 - c**2) / (2 * a * b))
    # Third vertex coordinates
    x = b * np.cos(angle)
    y = b * np.sin(angle)
    coords.append((x, y))
    coords.append((0, 0))  # Close the triangle
    x, y = zip(*coords)
    plt.figure()
    plt.plot(x, y, marker='o')
    plt.fill(x, y, 'b', alpha=0.3)  # Fill with light blue
    plt.gca().set_aspect('equal', adjustable='box')
    plt.axis('off')

# Function to plot a circle
def plot_circle(radius):
    circle = plt.Circle((0, 0), radius, color='r', fill=False)
    fig, ax = plt.subplots()
    ax.add_artist(circle)
    ax.set_xlim(-radius-1, radius+1)
    ax.set_ylim(-radius-1, radius+1)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

# Function to plot a rectangle
def plot_rectangle(width, height):
    rectangle = plt.Rectangle((-width/2, -height/2), width, height, fill=None, color='g')
    fig, ax = plt.subplots()
    ax.add_artist(rectangle)
    ax.set_xlim(-width, width)
    ax.set_ylim(-height, height)
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')

# Function to plot a square
def plot_square(side):
    plot_rectangle(side, side)

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
        # Create the button view with the expression
        view = MetaCalculatorButton(expression)
        with open(image_path, 'rb') as image_file:
            # Send the image along with the button view
            await interaction.followup.send(file=discord.File(image_file, os.path.basename(image_path)), view=view)
        os.remove(image_path)


@client.tree.command()
async def latex_help(interaction: discord.Interaction):
    """Help for formatting and using the LaTeX system"""
    await interaction.response.send_message(HELP_TEXT, ephemeral=True)

@client.tree.command()
@app_commands.describe(rows="Number of rows for the table.")
async def input_table(interaction: discord.Interaction, rows: int):
    """Create a table of input buttons and submit to plot."""
    await interaction.response.send_message(view=TableInputView(rows), ephemeral=True)

@client.tree.command()
@app_commands.describe(shape="The shape to draw", dimensions="The dimensions of the shape")
async def draw(interaction: discord.Interaction, shape: str, dimensions: str):
    """Draws a specified shape with given dimensions."""
    await interaction.response.defer(ephemeral=False)
    dimensions = list(map(float, dimensions.split()))
    
    if shape == "triangle" and len(dimensions) == 3:
        plot_triangle(*dimensions)
    elif shape == "circle" and len(dimensions) == 1:
        plot_circle(*dimensions)
    elif shape == "rectangle" and len(dimensions) == 2:
        plot_rectangle(*dimensions)
    elif shape == "square" and len(dimensions) == 1:
        plot_square(*dimensions)
    else:
        await interaction.followup.send("Invalid shape or dimensions. Please check your input and try again.")
        return
    
    # Save plot to a BytesIO buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Send the image in Discord
    file = discord.File(buffer, filename='shape.png')
    await interaction.followup.send(file=file)

# Run the client with the bot token
client.run(TOKEN)
