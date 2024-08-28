from flask import Flask, render_template, request, jsonify
import os
import google.generativeai as genai
import requests
from geopy.distance import geodesic

app = Flask(__name__)

# Set your API keys
api_keys = [
    'AIzaSyCnHl00zFLlQHXtYR4Q0sAqaj2Vstz0a08',  # Original key
    'AIzaSyA59iFa2YEp9-4pqdM1pGOJwfOenil9fCI',  # api_key1
    'AIzaSyDxFSs2n8X1fDNeS5o3HirUi1Y8_ZgixeQ',  # api_key2
    'AIzaSyAeCq43oM55R9sKp3ceDLCw3ITjTvgua-0',  # api_key3
    'AIzaSyDcT8abHhg94xH8twWSdzXC_EqLPuuE6W4',  
    'AIzaSyBER-AtJ5rRIiiOezfqWpbwdDk4GezyZbY'    # api_key4
]

# Rotate API keys to avoid quota exhaustion
current_key_index = 0

def get_next_api_key():
    global current_key_index
    api_key = api_keys[current_key_index]
    current_key_index = (current_key_index + 1) % len(api_keys)
    return api_key

def configure_gemini():
    genai.configure(api_key=get_next_api_key())

# Configure Google Gemini with the first API key
configure_gemini()

# Get user location
def get_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        location = f"{data['city']}, {data['region']}, {data['country']}"
        return location, (data['loc'].split(","))
    except Exception as e:
        print(f"Error getting location: {e}")
        return None, None

# Fetch images from Pexels API
def fetch_images(query):
    headers = {
        'Authorization': 'q3BGqmiLthLOkBMlXFXlGqGHtmVSrpBTJNQ9tGyHDtx56ymVpex6wpGi',
    }
    params = {
        'query': query,
        'per_page': 5,
    }
    try:
        response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params)
        photos = response.json().get('photos', [])
        return [photo['src']['medium'] for photo in photos]
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []


def start_chat_session(location):
    try:
        configure_gemini()  # Configure with the next API key before starting a session
        
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config=generation_config,
        )

        chat_session = model.start_chat(
            history=[]
        )

        query = f"Tell me about tribal artifacts or tribal culture near {location}. " \
                f"In the first line, provide the name and 3 to 4 words about it. " \
                f"In the second line, give a 40-word description. " \
                f"In the third line, give a genuine review of the artifact."
        
        response = chat_session.send_message(query)
        
        # Print the raw response for debugging
        #print("Raw Response:\n", response.text)
        
        # Split the response into lines, filtering out empty lines
        response_lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        
        # Handle the lines properly
        artifact_name = response_lines[0] if len(response_lines) > 0 else "No name found"
        description = response_lines[1] if len(response_lines) > 1 else "No description found"
        review = response_lines[2] if len(response_lines) > 2 else "No review found"

        return artifact_name, description, review
    except Exception as e:
        print(f"Error during chat session: {e}")
        return None, None, None



# Calculate the distance between two locations
def calculate_distance(user_location, target_location):
    return geodesic(user_location, target_location).kilometers

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore', methods=['POST'])
def explore():
    location = request.form.get('location') or get_location()[0]
    user_coordinates = get_location()[1]
    
    if not location:
        return jsonify({
            "error": "Could not retrieve location."
        }), 400
    
    artifact_name, description, review = start_chat_session(location)
    images = fetch_images(artifact_name)
    
    # For demonstration, we'll assume the artifact is in the same city; real implementation would need precise coordinates
    distance = calculate_distance(user_coordinates, user_coordinates)  # Replace with real coordinates if available
    
    return jsonify({
        "artifact_name": artifact_name,
        "description": description,
        "review": review,
        "images": images,
        "distance": distance
    })

if __name__ == '__main__':
    app.run(debug=True)
