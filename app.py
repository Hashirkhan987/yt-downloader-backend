import os
import yt_dlp
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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
        return jsonify({"error": "YouTube URL is required"}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': 'best',
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Link not found"}), 400

            direct_url = info.get('url')
            formats = []

            for f in info.get('formats', []):
                f_url = f.get('url')
                if not f_url or f_url == 'None':
                    continue

                vcodec = f.get('vcodec', 'none')
                acodec = f.get('acodec', 'none')
                has_video = vcodec and vcodec!= 'none'
                has_audio = acodec and acodec!= 'none'

                if (has_video and has_audio) or (not has_video and has_audio):
                    formats.append({
                        "itag": str(f.get('format_id', '')),
                        "quality": f"{f.get('height', 'Audio')}p" if has_video else "Audio MP3",
                        "format": f.get('ext', 'mp4'),
                        "filesize": f.get('filesize') or f.get('filesize_approx') or 0,
                        "url": f_url
                    })

            if (not direct_url or direct_url == 'None') and formats:
                direct_url = formats[0]['url']

            if not direct_url or direct_url == 'None':
                return jsonify({"error": "Link not found"}), 400

            return jsonify({
                "title": info.get('title', 'YouTube Video'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "uploader": info.get('uploader'),
                "view_count": info.get('view_count'),
                "download_url": direct_url,
                "formats": formats
            }), 200

    except Exception as e:
        print("yt-dlp extraction error:", e)
        return jsonify({"error": "Link not found"}), 400

@app.route('/api/download', methods=['GET'])
def download():
    url = request.args.get('url')
    itag = request.args.get('itag')

    if not url:
        return jsonify({"error": "YouTube URL is required"}), 400

    format_spec = itag if (itag and itag!= 'None') else 'best'
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'format': format_spec,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            stream_url = info.get('url')

            if not stream_url or stream_url == 'None':
                for f in info.get('formats', []):
                    if f.get('url') and f.get('url')!= 'None':
                        stream_url = f.get('url')
                        break

            if not stream_url or stream_url == 'None':
                return jsonify({"error": "Link not found"}), 400

            return redirect(stream_url, code=302)
    except Exception as e:
        return jsonify({"error": "Link not found"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
