# Dockerfile
FROM python:3.11-slim

# Install system dependencies for TeX Live, poppler-utils, CMake, and essential build tools
RUN apt-get update && apt-get install -y \
    texlive-full \
    poppler-utils \
    cmake \
    build-essential \
    autoconf \
    automake \
    libtool \
    ninja-build \
    && apt-get clean

# Check CMake installation
RUN cmake --version

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
