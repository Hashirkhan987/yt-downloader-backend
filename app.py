from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Backend is running - new version!"

@app.route('/api/info')
def info():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL"}), 400
    try:
        ydl_opts = {'quiet': True, 'noplaylist': True, 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android', 'web']}}}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(url, download=False)
            return jsonify({"title": data.get("title"), "thumbnail": data.get("thumbnail"), "duration": data.get("duration"), "url": data.get("webpage_url")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/download')
def download():
    url = request.args.get('url')
    if not url:
        return "No URL", 400
    try:
        ydl_opts = {'quiet': True, 'format': 'best[ext=mp4]/best', 'noplaylist': True, 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android']}}}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get('url') or info['formats'][-1]['url']
            title = info.get('title', 'video').replace('"','')
        r = requests.get(direct_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        return Response(stream_with_context(r.iter_content(chunk_size=1024*1024)), headers={'Content-Disposition': f'attachment; filename="{title}.mp4"', 'Content-Type': 'video/mp4'})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
