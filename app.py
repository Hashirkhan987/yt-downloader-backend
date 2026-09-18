from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp, requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home(): return "Backend LIVE Final Fix"

@app.route('/api/info', methods=['POST'])
def get_info():
    try:
        url = request.get_json().get('url')
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('url'):
                    formats.append({'itag': f['format_id'], 'quality': f.get('height'), 'ext': f['ext']})
            return jsonify({'title': info.get('title'), 'thumbnail': info.get('thumbnail'), 'formats': formats[:10]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download():
    try:
        url = request.args.get('url')
        itag = request.args.get('itag')
        ydl_opts = {'format': itag, 'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}}}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            for f in info['formats']:
                if f['format_id'] == itag:
                    r = requests.get(f['url'], stream=True)
                    return Response(r.iter_content(1024*1024), headers={'Content-Disposition': f'attachment; filename="video.{f["ext"]}"'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
