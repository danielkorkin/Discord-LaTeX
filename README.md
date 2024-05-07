
# LaTeX Equation Discord Bot

A Discord bot that generates LaTeX equations from text inputs and converts them into PNG images for easy sharing. Powered by Google Generative AI Gemini Model.

## Prerequisites

- [Python 3.10+](https://www.python.org/downloads/)
- [Discord Developer Account](https://discord.com/developers/applications)
- [Google API Key](https://console.cloud.google.com/)

## Setting up the Bot

### 1. Create a Discord Bot

1. **Create a New Application:**
   - Visit the [Discord Developer Portal](https://discord.com/developers/applications).
   - Click `New Application` and provide a name.
2. **Create a Bot:**
   - Under `Bot`, click `Add Bot`.
   - Save your token and add it to the `.env` file.
  
### 2. Setting Up Your Environment

- Create a `.env` file with the following variables:
  ```bash
  TOKEN=your-discord-bot-token
  GUILD_ID=your-guild-id
  GOOGLE_API_KEY=your-google-api-key
  ```

### 3. Install Required Software

#### Mac

1. **Install MacTeX**: [Download and install MacTeX](https://tug.org/mactex/)
2. **Install Python Requirements**: Run the following command:
   ```bash
   pip install -r requirements.txt
   ```

#### Windows

1. **Install MiKTeX**: [Download and install MiKTeX](https://miktex.org/download)
2. **Install Python Requirements**: Run:
   ```bash
   pip install -r requirements.txt
   ```

#### Linux

1. **Install TeX Live**:
   - Debian/Ubuntu: `sudo apt install texlive`
   - Fedora/Red Hat: `sudo dnf install texlive`
2. **Install Python Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

#### Raspberry Pi (Linux)

1. **Install TeX Live**: Same as Linux instructions above.
2. **Install Python Requirements**: Follow Linux instructions.

### 4. Get Google Gemini API Key

- Sign up at [Google Generative AI API](https://developers.generativeai.google/)
- Create a project and an API key.
- Enable the Generative Language API and add the key to your `.env` file.

### 5. Running the Bot

- Start the bot by running the Python script:
  ```bash
  python bot.py
  ```

## Docker Instructions
For details on docker instructions look at the docker.md file

## Troubleshooting

- Ensure your `.env` file has correct values.
- Check if all software dependencies are correctly installed.

## Contributing

Contributions are welcome! Please submit issues or pull requests to improve this bot.
