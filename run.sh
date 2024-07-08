#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install or upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Run image generation script
python generate_images.py

# Run Flask application
export FLASK_APP=app.py
export FLASK_ENV=development
flask run