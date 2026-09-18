from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Backend Live - Latest yt-dlp"

@app.route('/api/info', methods=['POST', 'OPTIONS'])
def get_info():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    try:
        data = request.get_json()
        url = data.get('url')
        
        # Final bypass for Render IP block
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_music', 'android', 'ios'],
                    'player_skip': ['webpage']
                }
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            for f in info.get('formats', []):
                if f.get('url') and f.get('ext'):
                    formats.append({'itag': f.get('format_id'), 'ext': f.get('ext'), 'quality': f.get('format_note')})
            
            return jsonify({
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'formats': formats[:10]
            })
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
