import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
with open("models_list_final.txt", "w", encoding="utf-8") as f:
    try:
        f.write("Available Models:\n")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                line = f"- {m.name}\n"
                print(line.strip())
                f.write(line)
    except Exception as e:
        error_msg = f"Error listing models: {e}"
        print(error_msg)
        f.write(error_msg + "\n")
