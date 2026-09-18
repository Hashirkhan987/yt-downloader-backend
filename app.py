from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Backend Live - Final No Bot"

@app.route('/api/info', methods=['POST', 'OPTIONS'])
def get_info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        url = request.get_json().get('url')

        # 1. Pehle YouTube ke liye Cobalt API try karo (No Bot Error)
        if "youtube.com" in url or "youtu.be" in url:
            try:
                r = requests.post("https://api.cobalt.tools/api/json",
                    json={"url": url, "vCodec": "h264", "vQuality": "720", "aFormat": "mp3"},
                    headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
                data = r.json()
                if data.get("url"):
                    # Cobalt direct link de deta hai
                    return jsonify({
                        "title": "YouTube Video (Cobalt Bypass)",
                        "thumbnail": f"https://img.youtube.com/vi/{url.split('/')[-1].split('?')[0]}/hqdefault.jpg",
                        "formats": [{"itag": "720p", "ext": "mp4", "quality": "720p (No Bot)"}]
                    })
            except Exception as e:
                print(f"Cobalt failed, trying yt-dlp: {e}")

        # 2. Agar Youtube nahi ya Cobalt fail, to baqi TikTok, FB, Insta ke liye yt-dlp
        ydl_opts = {
            'quiet': True,
            'extractor_args': {'youtube': {'player_client': ['android_music', 'android']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": [{"itag": f['format_id'], "ext": f['ext']} for f in info['formats'] if f.get('url')][:8]
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
