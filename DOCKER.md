
# Docker Setup Guide

This guide outlines the steps to set up and run the LaTeX bot inside a Docker container on various platforms.

## 1. Create a Dockerfile

Create a `Dockerfile` with the following contents:

```Dockerfile
# Dockerfile
# Base image with Python
FROM python:3.11-slim

# Install system dependencies for TeX Live and poppler-utils
RUN apt-get update && apt-get install -y \
    texlive-full \
    poppler-utils \
    && apt-get clean

# Create a working directory
WORKDIR /usr/src/app

# Copy the Python dependencies file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire bot project to the working directory
COPY bot/ ./bot/

# Set environment variables for the bot
ENV PYTHONUNBUFFERED 1

# Run the bot using the main Python script
CMD ["python", "bot/bot.py"]
```

## 2. Create a Docker Compose File (Optional)

This file simplifies running the bot's Docker container with required configurations:

```yaml
# docker-compose.yml
version: '3.8'
services:
  latex-bot:
    build:
      context: .
      dockerfile: Dockerfile
    env_file: .env
    volumes:
      - ./bot/tmp:/usr/src/app/bot/tmp
    restart: always
```

## 3. Prepare the Environment Configuration

Ensure the `.env` file is created in the same directory with secrets like the Discord bot token, guild ID, and Google API key.

```plaintext
# .env
TOKEN=<your_discord_bot_token>
GUILD_ID=<your_discord_guild_id>
GOOGLE_API_KEY=<your_google_api_key>
```

## 4. Build and Run the Docker Container

### Using Docker Compose

To build and start the container using Docker Compose, run:

```bash
docker-compose up --build
```

### Using the Dockerfile

To build and run directly from the Dockerfile:

```bash
docker build -t discord-latex-bot .
docker run --env-file .env discord-latex-bot
```

## Platform-Specific Notes

### Windows

- Ensure Docker Desktop is installed and running.
- Use WSL2 or Hyper-V mode for a better experience.

### macOS

- Install Docker Desktop for Mac.
- Use the default settings unless modifications are necessary.

### Linux

- Install Docker CE and Docker Compose using the official instructions from [Docker Documentation](https://docs.docker.com/get-docker/).

### Raspberry Pi

- Use the `arm32v7/python` or `arm64v8/python` base image instead of `python:3.11-slim`.

```Dockerfile
# Replace this base image with the appropriate ARM-based one
FROM arm32v7/python:3.11-slim

# The rest of the Dockerfile remains the same
```

- Make sure your Pi has enough resources and is properly cooled.
