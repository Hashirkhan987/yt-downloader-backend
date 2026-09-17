@app.route('/api/download')
def download_video():
    url = request.args.get('url')
    quality = request.args.get('quality', '720') # 1080, 720 etc
    
    ydl_opts = {
        'quiet': True,
        'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'noplaylist': True,
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        # googlevideo.com wala asal link nikalo
        if 'url' in info:
            direct_url = info['url']
        else:
            # sab se achi mp4 format dhoondo
            formats = [f for f in info['formats'] if f.get('ext') == 'mp4' and f.get('vcodec') != 'none']
            direct_url = formats[-1]['url'] if formats else info['formats'][-1]['url']
        
        # Redirect mat karo, link JSON me bhejo taake frontend download kara sake
        return jsonify({"download_url": direct_url, "title": info['title']})
