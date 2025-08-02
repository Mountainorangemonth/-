from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict
import json
import requests
import re
from database_manager import DatabaseManager

# --- Models ---
class TranslationRequest(BaseModel):
    texts: List[str]

# --- FastAPI App ---
app = FastAPI()

# Mount the static directory to serve frontend files
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Globals ---
# Load config and database manager at startup
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    DB_MANAGER = DatabaseManager()
    print("Server startup: Config and DatabaseManager loaded successfully.")
except FileNotFoundError as e:
    print(f"FATAL: Could not start server. {e}")
    DB_MANAGER = None
    CONFIG = None

# --- Helper Functions ---
def clean_ai_response(response_text: str) -> Dict:
    """Robustly cleans the raw response from the AI to extract a JSON object."""
    match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = response_text[start:end]
        else:
            return None
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def translate_with_ai(texts_to_translate: List[str]) -> Dict[str, str]:
    """Translates a list of texts using the configured AI provider with improved prompting."""
    if not CONFIG or not texts_to_translate:
        return {}

    provider = CONFIG.get('ai_provider', 'ollama')
    input_json = {text: text for text in texts_to_translate}
    prompt = f"""
    You are a high-quality automated translation service for Minecraft.
    Your task is to translate the values in the following JSON object from English to Simplified Chinese.
    
    CRITICAL RULES:
    1. Translate ALL text, including short phrases, single words, and symbols.
    2. Convert English punctuation to corresponding full-width Chinese punctuation (e.g., `!` -> `！`, `...` -> `…`).
    3. If a value cannot be meaningfully translated, return an EMPTY a string `""` for that value.
    4. You MUST return ONLY a valid JSON object with the original keys and translated values.
    
    Input:
    {json.dumps(input_json, indent=2, ensure_ascii=False)}
    
    Output:
    """

    try:
        if provider == 'ollama':
            settings = CONFIG['ollama_settings']
            data = {"model": settings['model'], "prompt": prompt, "stream": False, "options": {"temperature": 0.0}}
            response = requests.post(settings['api_url'], json=data, timeout=180)
        elif provider == 'api':
            settings = CONFIG['api_settings']
            auth_header_name = settings.get('auth_header', 'Authorization')
            auth_header_value = f"Bearer {settings['api_key']}" if auth_header_name == 'Authorization' else settings['api_key']
            headers = {auth_header_name: auth_header_value, "Content-Type": "application/json"}
            data = {"model": settings['model'], "messages": [{"role": "user", "content": prompt}], "temperature": 0.0}
            response = requests.post(settings['url'], json=data, headers=headers, timeout=180)
        else:
            return {text: text for text in texts_to_translate}

        response.raise_for_status()
        raw_response = response.json().get('response', '{}') if provider == 'ollama' else response.json()['choices'][0]['message']['content']
        
        parsed_response = clean_ai_response(raw_response)
        if parsed_response:
            return {text: parsed_response.get(text, text) for text in texts_to_translate}
        else:
            print(f"Error: Failed to parse AI response. Raw response: {raw_response}")
            return {text: text for text in texts_to_translate}

    except requests.exceptions.RequestException as e:
        print(f"Error during AI call: {e}")
        return {text: text for text in texts_to_translate}

def batch_translate_with_ai(texts_to_translate: List[str]) -> Dict[str, str]:
    """Translates a large list of texts by splitting it into smaller, configurable batches."""
    # Read batch size from config, with a safe default
    batch_size = CONFIG.get('persistent_server_settings', {}).get('batch_size', 50)
    
    all_translations = {}
    for i in range(0, len(texts_to_translate), batch_size):
        batch = texts_to_translate[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(texts_to_translate) + batch_size - 1)//batch_size} (size: {len(batch)})...")
        batch_translations = translate_with_ai(batch)
        all_translations.update(batch_translations)
    return all_translations

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/translate", response_model=Dict[str, str])
async def translate_texts(request: TranslationRequest):
    if not DB_MANAGER or not CONFIG:
        raise HTTPException(status_code=500, detail="Server is not properly configured.")

    unique_texts = list(set(request.texts))
    
    # 1. Database Lookup
    translations = DB_MANAGER.get_translations(unique_texts)
    
    # 2. AI Fallback
    texts_for_ai = [text for text in unique_texts if text not in translations]
    if texts_for_ai:
        print(f"Found {len(texts_for_ai)} items not in DB. Calling AI in batches...")
        # Use the new batching function
        ai_translations = batch_translate_with_ai(texts_for_ai)
        
        # 3. Permanent Memory: Save new translations to DB
        for source_text, translated_text in ai_translations.items():
            if translated_text:
                DB_MANAGER.add_translation(source_text, translated_text)
                if source_text != translated_text:
                    print(f"Learned new translation: '{source_text}' -> '{translated_text}'")
                else:
                    print(f"Confirmed translation (same as source): '{source_text}'")
        translations.update(ai_translations)

    # Ensure all original texts are in the final dictionary
    final_results = {text: translations.get(text, text) for text in request.texts}
    return final_results
