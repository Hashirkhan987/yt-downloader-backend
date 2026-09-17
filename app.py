from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import yt_dlp
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/info')
def info():
    url = request.args.get('url')
    ydl_opts = {'quiet': True, 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android']}}}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        data = ydl.extract_info(url, download=False)
        return jsonify(data)

@app.route('/api/download')
def download():
    url = request.args.get('url')
    quality = request.args.get('quality', 'best')
    # Step 1: yt-dlp se asal googlevideo link nikalo
    ydl_opts = {'quiet': True, 'format': f'best[height<={quality}]/best', 'nocheckcertificate': True, 'extractor_args': {'youtube': {'player_client': ['android']}}}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        direct_url = info.get('url') or info['formats'][-1]['url']
        title = info.get('title', 'video')

    # Step 2: Us link ko proxy karke user ko bhejo - taake .txt na aaye
    r = requests.get(direct_url, stream=True)
    return Response(r.iter_content(chunk_size=1024*1024), 
                    content_type='video/mp4',
                    headers={'Content-Disposition': f'attachment; filename="{title}.mp4"'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
