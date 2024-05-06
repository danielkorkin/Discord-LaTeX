# LaTeX Discord Bot Setup Guide

This guide will help you set up a Discord bot that renders mathematical equations into images using LaTeX. The bot listens for equations entered via Discord commands, processes them with a LaTeX compiler, and sends back the rendered images.

## Prerequisites
Before setting up the bot, ensure you have the following software installed:

1. **Python 3.x** (with pip)
   - Download from [python.org](https://www.python.org) and install the latest version.
   - Ensure `pip` (Python's package manager) is also installed.

2. **Discord Bot Token**
   - Create a Discord bot through the [Discord Developer Portal](https://discord.com/developers/applications).
   - Add the bot to a server with the necessary permissions.
   - Copy the bot token and save it for later.

3. **LaTeX Distribution** (for compiling LaTeX documents)
   - **TeX Live** (recommended):
     - Download from [tug.org/texlive](https://www.tug.org/texlive/).
     - Install using the appropriate installer for your operating system.

   - **MiKTeX** (alternative for Windows users):
     - Download from [miktex.org/download](https://miktex.org/download).
     - Install using the provided installer.

4. **Poppler** (for converting PDFs to images)
   - **Linux**:
     - Install via your package manager: `sudo apt-get install poppler-utils`.

   - **macOS**:
     - Install via Homebrew: `brew install poppler`.

   - **Windows**:
     - Download [Poppler for Windows](http://blog.alivate.com.au/poppler-windows/).
     - Add the `bin` folder to your system's `PATH`.

## Project Setup

1. **Clone or Download the Project Code**
   - Place the bot code in a new directory on your computer.

2. **Create a Virtual Environment (optional but recommended)**
   - Navigate to the project directory and run:
     ```bash
     python -m venv venv
     ```
   - Activate the environment:
     - **Windows**: `venv\Scripts\activate`
     - **Linux/macOS**: `source venv/bin/activate`

3. **Install Required Python Packages**
   - In the virtual environment or directly in your environment, install the required packages:
     ```bash
     pip install discord.py python-dotenv pylatex pdf2image Pillow
     ```

4. **Create and Configure `.env` File**
   - In the project root, create a file named `.env`.
   - Add your Discord bot token and guild ID to the file:
     ```bash
     TOKEN=YOUR_DISCORD_BOT_TOKEN
     GUILD_ID=YOUR_DISCORD_GUILD_ID
     ```

5. **Verify LaTeX Compiler and Poppler Installation**
   - Ensure that the `pdflatex` command is available in your command prompt/terminal.
   - Test that the `pdf2image` library can access `pdftoppm` (part of Poppler).

## Running the Bot

1. **Start the Bot**
   - Run the bot code using Python:
     ```bash
     python bot.py
     ```
   - If the bot starts successfully, you'll see a message like "Logged in as YourBotName#XXXX."

2. **Test the Bot**
   - In your Discord server, use the command you configured (e.g., `/render 1+1`) to render an equation.
   - Verify that the bot responds with a properly formatted image.

## Troubleshooting Tips

- **LaTeX Compilation Issues**:
  - Check that the LaTeX compiler is correctly installed and available in the system's `PATH`.

- **Image Conversion Problems**:
  - Ensure that Poppler is correctly installed and accessible.

- **Discord API Issues**:
  - Verify that the bot token and permissions are set up correctly.

## Conclusion

You have now set up a Discord bot that can render mathematical equations using LaTeX. Customize the bot to your needs or expand its features to handle other types of documents.
