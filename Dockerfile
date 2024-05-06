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
