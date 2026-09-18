from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "V7 FIXED"

@app.route('/api/info', methods=['POST','OPTIONS'])
def info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    url = request.get_json().get('url','')
    # YouTube ke liye yt-dlp bilkul use nahi karenge
    r = requests.post("https://api.cobalt.tools/api/json",
        json={"url": url}, 
        headers={"Accept":"application/json","Content-Type":"application/json"},
        timeout=30)
    data = r.json()
    return jsonify({
        "title": "YouTube Video",
        "thumbnail": "",
        "formats": [{"itag":"720","ext":"mp4","quality":"720p"}],
        "download_url": data.get('url')
    })
