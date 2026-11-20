import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

client = genai.Client(api_key=api_key)

print("Fetching models available for your API key...\n")
available_models = []

for model in client.models.list():
    supported_actions = getattr(model, "supported_actions", []) or []
    if "generateContent" in supported_actions and "gemini" in model.name.lower():
        clean_name = model.name.replace("models/", "")
        available_models.append(clean_name)

print(f"Total Gemini models supporting generateContent: {len(available_models)}")
for idx, name in enumerate(available_models, start=1):
    print(f" {idx}. {name}")

if not available_models:
    raise RuntimeError("No Gemini models supporting generateContent were found.")

prompt = "Suggest three beautiful tourist attractions in Goa in 3 short bullet points."

# Prioritize models avoiding deprecated 2.5-flash, trying available candidates in order
candidates = [
    m for m in available_models
    if "2.5-flash" not in m and "image" not in m and "tts" not in m and "robotics" not in m
]

print("\nTesting models until a working one responds...\n")

working_model = None

for model_name in candidates:
    print(f"--- Testing model: {model_name} ---")
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            print(f"\nSUCCESS with model '{model_name}'!\n")
            print(response.text)
            working_model = model_name
            break
        except errors.APIError as e:
            print(f"Attempt {attempt + 1} failed for {model_name}: {e.code} {e.message}")
            if e.code == 404:
                # Model not enabled for this key; skip immediately to next model
                break
            if attempt < 1:
                time.sleep(2)

    if working_model:
        break

if working_model:
    print(f"\nVerified working model ID to use in our project: {working_model}")
else:
    print("\nCould not find a responding model right now. Share the full numbered list above.")