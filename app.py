from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
app = Flask(__name__)
CORS(app)
@app.route('/')
def home():
    return "V7 FIXED LIVE"
@app.route('/api/info', methods=['POST','OPTIONS'])
def info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    url = request.get_json().get('url','')
    r = requests.post("https://api.cobalt.tools/api/json", json={"url": url}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
    j = r.json()
    return jsonify({"title":"Video","thumbnail":"","formats":[{"itag":"720","ext":"mp4","quality":"720p"}],"download_url": j.get('url')})
