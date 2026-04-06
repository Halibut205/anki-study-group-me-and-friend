#!/bin/bash

# Setup script for Anki Study Tracker
# Usage: bash setup.sh

echo "🚀 Anki Study Tracker - Quick Setup"
echo "===================================="
echo ""

# Check if config.json already exists
if [ -f "config.json" ]; then
    echo "⚠️  config.json already exists!"
    echo "If you want to reconfigure, edit it directly or delete and re-run this script."
    exit 0
fi

# Check if config.example.json exists
if [ ! -f "config.example.json" ]; then
    echo "❌ config.example.json not found!"
    echo "Make sure you're in the correct directory."
    exit 1
fi

echo "📋 Creating config.json from template..."
cp config.example.json config.json
echo "✓ config.json created!"
echo ""

# Prompt for user info
echo "📝 Setup Your Profile"
echo "---"

read -p "Your name (default: Ban): " user_name
user_name=${user_name:-Ban}

read -p "Your color (hex code, default: #378ADD): " user_color
user_color=${user_color:-#378ADD}

read -p "Repo path (full path to this directory): " repo_path
if [ -z "$repo_path" ]; then
    repo_path=$(pwd)
fi

# Update config.json
python3 << EOF
import json

config = {
    "my_name": "$user_name",
    "my_color": "$user_color",
    "repo_path": "$repo_path",
    "goals": {
        "daily": 10,
        "weekly": 50
    }
}

with open("config.json", "w") as f:
    json.dump(config, f, indent=2)

print("")
print("✅ Setup complete!")
print("")
print("📊 Your config:")
print(f"  • Name: {config['my_name']}")
print(f"  • Color: {config['my_color']}")
print(f"  • Repo Path: {config['repo_path']}")
print(f"  • Daily Goal: {config['goals']['daily']} cards")
print(f"  • Weekly Goal: {config['goals']['weekly']} cards")
print("")
print("Next step:")
print("1. Open Anki")
print("2. Go to Tools → Study Tracker 📅")
print("3. Click ⚙️ Settings to verify your config")
print("4. Enjoy! 🎓")
EOF
