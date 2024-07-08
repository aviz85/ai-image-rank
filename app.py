from flask import Flask, render_template, request, jsonify, send_from_directory
import json
import os

app = Flask(__name__)

# Configure the upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Path to the metadata JSON file
METADATA_FILE = 'metadata.json'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        
        with open('models.json', 'r') as f:
            models_data = json.load(f)
        
        models = [model['name'] for model in models_data['models']]
        dreams = list(set(item['dream'] for item in metadata))
        prompt_types = ['POV', 'Theme']
        
        return jsonify({
            'metadata': metadata,
            'models': models,
            'dreams': dreams,
            'prompt_types': prompt_types
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    filename = data['filename']
    rating = data['rating']
    
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        
        for item in metadata:
            if item['filename'] == filename:
                item['rating'] = rating
                break
        
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/top_models')
def top_models():
    try:
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
        
        model_ratings = {}
        for item in metadata:
            if item['rating'] > 0:
                if item['model'] not in model_ratings:
                    model_ratings[item['model']] = []
                model_ratings[item['model']].append(item['rating'])
        
        avg_ratings = {model: sum(ratings) / len(ratings) for model, ratings in model_ratings.items()}
        sorted_models = sorted(avg_ratings.items(), key=lambda x: x[1], reverse=True)
        
        return jsonify(sorted_models)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)