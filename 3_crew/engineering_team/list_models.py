
import google.generativeai as genai
import os
import sys

# Try to match the user's environment variable naming
api_key = os.environ.get("GOOGLE_API_KEY") 
if not api_key:
    print("GOOGLE_API_KEY not found.")
    # Attempt to load from potential .env if python-dotenv is there? 
    # For now just exit
    sys.exit(1)

try:
    genai.configure(api_key=api_key)
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
