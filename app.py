from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Backend is LIVE - 500 Fixed"

@app.route('/api/info', methods=['GET', 'POST'])
def get_info():
    try:
        if request.method == 'POST':
            data = request.get_json()
            url = data.get('url') if data else None
        else:
            url = request.args.get('url')
        
        if not url:
            return jsonify({'error': 'URL missing'}), 400

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'extractor_args': {'youtube': {'skip': ['hls', 'dash']}},
            'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats = []
            seen = set()
            for f in info.get('formats', []):
                fid = f.get('format_id')
                if fid in seen: continue
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    seen.add(fid)
                    formats.append({
                        'itag': fid,
                        'quality': f.get('format_note') or (f"{f.get('height')}p" if f.get('height') else f.get('ext')),
                        'ext': f.get('ext'),
                    })
            
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'formats': formats[:15]  # Top 15 only
            })
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({'error': f'Backend Error: {str(e)}'}), 500

@app.route('/api/download')
def download_video():
    try:
        url = request.args.get('url')
        itag = request.args.get('itag')
        ydl_opts = {'format': itag, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            for f in info['formats']:
                if f['format_id'] == itag and 'url' in f:
                    r = requests.get(f['url'], stream=True, headers={'User-Agent': 'Mozilla/5.0'})
                    return Response(r.iter_content(1024*1024), headers={
                        'Content-Disposition': f'attachment; filename="video.{f.get("ext","mp4")}"'
                    })
        return jsonify({'error': 'Format not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
