import os
import json
import time
from datetime import datetime
import requests
import replicate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def generate_image(prompt, model_code, negative_prompt, steps):
    if not REPLICATE_API_TOKEN:
        raise ValueError("Replicate API token not found in environment variables")

    input_data = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": steps
    }

    start_time = time.time()
    
    try:
        output = replicate.run(model_code, input=input_data)
        
        # The output is now a generator, we need to iterate through it
        image_url = None
        for item in output:
            if isinstance(item, str) and item.startswith('http'):
                image_url = item
                break
        
        if not image_url:
            raise ValueError("No image URL found in the output")

        end_time = time.time()
        generation_time = end_time - start_time

        response = requests.get(image_url)
        if response.status_code == 200:
            uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            image_path = os.path.join(uploads_dir, filename)
            
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            return filename, generation_time
        else:
            raise ValueError(f"Failed to download image: {response.status_code}")
    except Exception as e:
        print(f"Error in generate_image: {str(e)}")
        raise

def save_metadata(metadata, filename, dream, model, prompt, negative_prompt, steps, generation_time):
    new_metadata = {
        "filename": filename,
        "dream": dream,
        "model": model,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": steps,
        "generation_time": generation_time,
        "rating": 0
    }
    
    metadata.append(new_metadata)
    save_json(metadata, 'metadata.json')

def get_completed_tasks(metadata):
    completed = set()
    for item in metadata:
        completed.add((item['dream'], item['prompt'], item['model']))
    return completed

def main():
    # Load data
    models_data = load_json('models.json')
    prompts_data = load_json('prompts.json')
    metadata = load_json('metadata.json')

    # Ensure metadata is a list
    if not isinstance(metadata, list):
        metadata = []

    # Get the negative prompt from models_data
    negative_prompt = models_data.get("negative_prompt", "")

    completed_tasks = get_completed_tasks(metadata)

    for dream in prompts_data.get("dreams", []):
        for prompt_type in ["pov_prompt", "theme_prompt"]:
            prompt = dream.get(prompt_type)
            if not prompt:
                continue
            for model in models_data.get("models", []):
                task = (dream['dream'], prompt, model['name'])
                if task in completed_tasks:
                    print(f"Skipping already completed task: {task}")
                    continue
                try:
                    steps = int(model.get("steps_needed", 7))  # Default to 7 if not specified
                    filename, generation_time = generate_image(prompt, model["code"], negative_prompt, steps)
                    save_metadata(metadata, filename, dream["dream"], model["name"], prompt, negative_prompt, steps, generation_time)
                    print(f"Generated image for {dream['dream']} using {model['name']} with {steps} steps")
                except Exception as e:
                    print(f"Error generating image for {dream['dream']} using {model['name']}: {str(e)}")
                time.sleep(1)  # Add a small delay to avoid overwhelming the API

if __name__ == "__main__":
    main()