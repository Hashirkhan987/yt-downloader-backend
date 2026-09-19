from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

COBALT_API = "https://api.cobalt.tools/api/json"
# backup api if first fails
COBALT_BACKUP = "https://co.wuk.sh/api/json"

@app.route('/')
def home():
    return jsonify({"status": "live", "message": "Backend is LIVE with Cobalt"})

@app.route('/api/info', methods=['POST', 'GET'])
def get_info():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        url = data.get('url')
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL required"}), 400

    payload = {
        "url": url,
        "videoQuality": "720",
        "audioFormat": "mp3"
    }

    try:
        # try main cobalt
        r = requests.post(COBALT_API, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=20)
        if r.status_code!= 200:
            r = requests.post(COBALT_BACKUP, json=payload, headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=20)

        data = r.json()

        # cobalt returns url or picker
        download_url = data.get('url')
        picker = data.get('picker', [])

        formats = []
        if picker:
            for p in picker:
                formats.append({
                    "itag": p.get('type', 'video'),
                    "quality": p.get('type', '720p'),
                    "format": "mp4",
                    "filesize": 0,
                    "url": p.get('url')
                })
            if not download_url and formats:
                download_url = formats[0]['url']

        if not download_url:
            return jsonify({"error": "Link not found"}), 400

        return jsonify({
            "title": "YouTube Video",
            "thumbnail": f"https://img.youtube.com/vi/{url.split('v=')[-1].split('&')[0]}/hqdefault.jpg",
            "duration": 0,
            "uploader": "YouTube",
            "view_count": 0,
            "download_url": download_url,
            "formats": formats if formats else [{"itag": "720", "quality": "720p", "format": "mp4", "filesize": 0, "url": download_url}]
        })

    except Exception as e:
        print("Cobalt error:", e)
        return jsonify({"error": "Link not found"}), 400

@app.route('/api/download', methods=['GET'])
def download():
    # for compatibility with your frontend
    url = request.args.get('url')
    return get_info()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
