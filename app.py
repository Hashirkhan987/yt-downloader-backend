from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Backend is running!"

@app.route('/api/info')
def info():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL"}), 400
    ydl_opts = {
        'quiet': True, 
        'noplaylist': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)
        return jsonify(data)

@app.route('/api/download')
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', '720')
    if not url:
        return "No URL", 400
    
    ydl_opts = {
        'quiet': True,
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            direct_url = info.get('url')
            if not direct_url:
                # fallback to best mp4 format
                formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                direct_url = formats[-1]['url'] if formats else info['formats'][-1]['url']
            title = info.get('title', 'video').replace('"', '')

        # Proxy download - is se .txt ka masla khatam hoga
        req = requests.get(direct_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        headers = {
            'Content-Disposition': f'attachment; filename="{title}.mp4"',
            'Content-Type': 'video/mp4'
        }
        return Response(stream_with_context(req.iter_content(chunk_size=1024*1024)), headers=headers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
