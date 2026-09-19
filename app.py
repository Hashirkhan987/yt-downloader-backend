from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 3 cobalt servers - jo chale usi se kaam
COBALT_SERVERS = [
    "https://api.cobalt.tools/api/json",
    "https://cobalt-api.kwiatekmiki.com/api/json",
    "https://api.co.wuk.sh/api/json"
]

@app.route('/')
def home():
    return jsonify({"status": "live", "message": "Backend is LIVE"})

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

    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    for server in COBALT_SERVERS:
        try:
            print(f"Trying {server}")
            r = requests.post(server, json=payload, headers=headers, timeout=15)
            if r.status_code!= 200:
                continue

            data = r.json()
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
                continue

            # video id for thumbnail
            vid = url.split('v=')[-1].split('&')[0].split('/')[-1]

            return jsonify({
                "title": "YouTube Video",
                "thumbnail": f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                "duration": 0,
                "uploader": "YouTube",
                "view_count": 0,
                "download_url": download_url,
                "formats": formats if formats else [{"itag": "720", "quality": "720p", "format": "mp4", "filesize": 0, "url": download_url}]
            })
        except Exception as e:
            print(f"Failed {server}: {e}")
            continue

    return jsonify({"error": "Link not found"}), 400

@app.route('/api/download', methods=['GET'])
def download():
    return get_info()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
