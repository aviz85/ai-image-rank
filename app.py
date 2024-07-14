from flask import Flask, render_template, request, jsonify
from groq import Groq
from dotenv import load_dotenv
import os, json
import replicate

load_dotenv()

# Initialize the Groq and Replicate clients
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

if GROQ_API_KEY is None:
    raise ValueError("GROQ_API_KEY not found in environment variables.")
if REPLICATE_API_TOKEN is None:
    raise ValueError("REPLICATE_API_TOKEN not found in environment variables.")

groq_client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)

def generate_image_descriptions(dream):
    # Construct the prompt to get descriptions in a JSON format with a few-shot example
    example_json = {
        "descriptions": [
            "A vivid scene of swimming with dolphins in a clear blue ocean.",
            "A close-up of a dolphin smiling while jumping out of the water.",
            "A serene underwater view with dolphins swimming gracefully.",
            "A person riding on a dolphin's back in the open sea.",
            "A playful group of dolphins splashing around in the ocean.",
            "A sunset view with dolphins silhouetted against the sky.",
            "A diver and dolphins interacting underwater.",
            "A panoramic view of dolphins leaping in unison.",
            "A tranquil beach scene with dolphins in the distance.",
            "An artistic rendering of dolphins in a fantasy ocean."
        ]
    }
    
    prompt = f"""
    Generate 10 different image descriptions for the dream "{dream}" in JSON format.
    Example format:
    {json.dumps(example_json, indent=4)}
    """
    
    response = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=1,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Extract and clean the response
    raw_output = response.choices[0].message.content.strip()

    # Assume the response is a JSON-like string and clean it
    cleaned_output = raw_output[raw_output.find("{"):raw_output.rfind("}")+1]
    
    try:
        descriptions_dict = json.loads(cleaned_output)
        descriptions = descriptions_dict.get("descriptions", [])
    except json.JSONDecodeError:
        descriptions = []

    return descriptions

def create_image(prompt):
    input = {"prompt": prompt}
    output = replicate.run(
        "playgroundai/playground-v2.5-1024px-aesthetic:a45f82a1382bed5c7aeb861dac7c7d191b0fdf74d8d57c4a0e6ed7d4d0bf7d24",
        input=input
    )
    return output[0]

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        dream = request.form.get("dream")
        descriptions = generate_image_descriptions(dream)
        return render_template("index.html", dream=dream, descriptions=descriptions)
    return render_template("index.html")

@app.route("/create_image", methods=["POST"])
def create_image_route():
    description = request.form.get("description")
    image_url = create_image(description)
    return jsonify({"image_url": image_url})

if __name__ == "__main__":
    app.run(debug=True)