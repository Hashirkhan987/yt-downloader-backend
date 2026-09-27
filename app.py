from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import tempfile
import os
import re
import uuid
import threading
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Temporary files are deleted automatically after this many seconds.
TEMP_DIR = os.path.join(tempfile.gettempdir(), "video_downloader_backend")
os.makedirs(TEMP_DIR, exist_ok=True)
TEMP_FILE_TTL = 30 * 60


def cleanup_old_files():
    while True:
        try:
            now = time.time()
            for name in os.listdir(TEMP_DIR):
                path = os.path.join(TEMP_DIR, name)
                try:
                    if os.path.isfile(path) and now - os.path.getmtime(path) > TEMP_FILE_TTL:
                        os.remove(path)
                except OSError:
                    pass
        except Exception:
            pass
        time.sleep(300)


threading.Thread(target=cleanup_old_files, daemon=True).start()


def is_http_url(url):
    return bool(re.match(r"^https?://", url or "", re.I))


def base_ydl_opts():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        "extractor_retries": 2,
        "geo_bypass": True,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/140.0.0.0 Safari/537.36"
            )
        },
    }


def clean_format(f):
    if not f:
        return None
    url = f.get("url")
    if not url:
        return None
    return {
        "format_id": f.get("format_id"),
        "quality": f.get("resolution") or f.get("format_note") or "Unknown",
        "ext": f.get("ext", "mp4"),
        "filesize": f.get("filesize") or f.get("filesize_approx") or 0,
        "url": url,
        "has_audio": f.get("acodec") not in (None, "none"),
        "has_video": f.get("vcodec") not in (None, "none"),
        "fps": f.get("fps"),
    }


def extract_info(url):
    opts = base_ydl_opts()
    # Ask yt-dlp for information only. No media is downloaded here.
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    formats = []
    for f in info.get("formats") or []:
        item = clean_format(f)
        if item and (item["has_video"] or item["has_audio"]):
            formats.append(item)

    # Prefer progressive MP4 formats because browsers can play them directly.
    progressive_mp4 = [
        f for f in formats
        if f["ext"] == "mp4" and f["has_video"] and f["has_audio"]
    ]
    progressive_mp4.sort(key=lambda x: (x.get("fps") or 0, x.get("filesize") or 0))

    # Direct media URL for the UI. Prefer a browser-friendly MP4.
    direct = progressive_mp4[-1]["url"] if progressive_mp4 else None

    # If no progressive MP4 exists, choose yt-dlp's best single-file media URL.
    if not direct:
        candidates = [f for f in formats if f["has_video"]]
        candidates.sort(key=lambda x: (x.get("filesize") or 0))
        if candidates:
            direct = candidates[-1]["url"]

    return info, formats, direct


def platform_name(info, url):
    extractor = (info.get("extractor_key") or info.get("extractor") or "").lower()
    host = re.sub(r"^www\.", "", (re.findall(r"https?://([^/]+)", url or "") or [""])[0].lower())
    if "youtube" in extractor or "youtu" in host:
        return "YouTube"
    if "tiktok" in extractor or "tiktok.com" in host:
        return "TikTok"
    if "instagram" in extractor or "instagram.com" in host:
        return "Instagram"
    if "facebook" in extractor or "facebook.com" in host or "fb.watch" in host:
        return "Facebook"
    if "twitter" in extractor or "x.com" in host or "twitter.com" in host:
        return "X"
    if "reddit" in extractor or "reddit.com" in host:
        return "Reddit"
    return info.get("extractor_key") or "Video platform"


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "live",
        "service": "Multi-platform video downloader backend",
        "engine": "yt-dlp"
    })


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/info", methods=["POST", "GET"])
def get_info():
    data = request.get_json(silent=True) or {}
    url = data.get("url") if request.method == "POST" else request.args.get("url")

    if not url or not is_http_url(url):
        return jsonify({"error": "A valid http/https video URL is required."}), 400

    try:
        info, formats, direct = extract_info(url)

        # Return only useful, browser/download-friendly formats to the frontend.
        useful = [
            f for f in formats
            if f["ext"] in ("mp4", "webm", "m4v", "mov") and f["has_video"]
        ]
        useful.sort(key=lambda x: (x.get("filesize") or 0), reverse=True)
        useful = useful[:30]

        return jsonify({
            "success": True,
            "title": info.get("title") or "Video",
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration") or 0,
            "uploader": info.get("uploader") or info.get("channel") or "",
            "view_count": info.get("view_count") or 0,
            "platform": platform_name(info, url),
            "download_url": direct,
            "formats": useful,
        })

    except yt_dlp.utils.DownloadError as e:
        message = str(e)
        return jsonify({"error": "This video could not be accessed or downloaded.", "details": message[:500]}), 422
    except Exception as e:
        return jsonify({"error": "Server error while reading the video.", "details": str(e)[:500]}), 500


@app.route("/api/download", methods=["GET", "POST"])
def download_video():
    data = request.get_json(silent=True) or {}
    url = data.get("url") if request.method == "POST" else request.args.get("url")
    format_id = data.get("format_id") if request.method == "POST" else request.args.get("format_id")

    if not url or not is_http_url(url):
        return jsonify({"error": "A valid http/https video URL is required."}), 400

    # Download server-side so the browser does not have to fetch a short-lived
    # third-party URL and so CORS/expired CDN URLs do not break the download.
    job_id = uuid.uuid4().hex
    output_template = os.path.join(TEMP_DIR, f"{job_id}.%(ext)s")

    if format_id:
        # Only use an explicit format supplied by yt-dlp's /api/info response.
        format_selector = f"{format_id}+bestaudio[ext=m4a]/best[format_id={format_id}]/best"
    else:
        # Prefer a single-file MP4. If unavailable, use best available media.
        format_selector = "best[ext=mp4]/best"

    opts = base_ydl_opts()
    opts.update({
        "format": format_selector,
        "outtmpl": output_template,
        "overwrites": True,
        "continuedl": True,
    })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = ydl.prepare_filename(info)

        # Some formats can change extension after post-processing.
        if not os.path.exists(filepath):
            base, _ = os.path.splitext(filepath)
            matches = [
                os.path.join(TEMP_DIR, n)
                for n in os.listdir(TEMP_DIR)
                if n.startswith(os.path.basename(base) + ".")
            ]
            if matches:
                filepath = matches[0]

        if not os.path.exists(filepath):
            return jsonify({"error": "Download completed but output file was not found."}), 500

        filename = info.get("title") or "video"
        filename = re.sub(r"[^A-Za-z0-9._ -]+", "_", filename).strip() or "video"
        ext = os.path.splitext(filepath)[1] or ".mp4"
        filename += ext

        def generate():
            try:
                with open(filepath, "rb") as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        yield chunk
            finally:
                try:
                    os.remove(filepath)
                except OSError:
                    pass

        return Response(
            stream_with_context(generate()),
            mimetype="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(os.path.getsize(filepath)),
                "Cache-Control": "no-store",
            },
        )

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": "The video could not be downloaded.", "details": str(e)[:500]}), 422
    except Exception as e:
        return jsonify({"error": "Server error while downloading.", "details": str(e)[:500]}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
