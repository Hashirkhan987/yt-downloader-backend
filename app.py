from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, yt_dlp

app = Flask(__name__)
CORS(app)

def get_youtube_via_cobalt(url):
    try:
        r = requests.post("https://api.cobalt.tools/api/json",
            json={"url": url, "vCodec": "h264", "vQuality": "720"},
            headers={"Accept":"application/json","Content-Type":"application/json"},
            timeout=30)
        j = r.json()
        if j.get("url"):
            return j
    except:
        pass
    return None

@app.route('/')
def home():
    return "Server Running V6 - YouTube Fixed"

@app.route('/api/info', methods=['POST','OPTIONS'])
def info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    data = request.get_json()
    url = data.get('url','')
    
    # 1. If YouTube, use Cobalt first (No bot error)
    if "youtube.com" in url or "youtu.be" in url:
        cobalt = get_youtube_via_cobalt(url)
        if cobalt and cobalt.get("url"):
            return jsonify({
                "title": "YouTube Video",
                "thumbnail": "",
                "formats": [{"itag":"cobalt","ext":"mp4","quality":"720p - MP4"}],
                "download_url": cobalt.get("url")
            })
    
    # 2. For TikTok, Insta, FB - use yt-dlp
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True, 'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats',[]):
                if f.get('vcodec') != 'none':
                    formats.append({"itag": f.get('format_id'), "ext": f.get('ext'), "quality": f.get('height')})
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats[-5:],
                "download_url": info.get('url')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
