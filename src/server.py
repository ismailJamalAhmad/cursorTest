"""Simple HTTP server for uploading GLTF/GLB files and forwarding them to Google Veo.

This server is dependency free and built with the Python standard library.  It exposes
an `/api/generate` endpoint that accepts a multipart form upload containing a `model`
file and optional form fields that describe the advertising prompt.  The file is stored
in a temporary directory before being passed to the (mocked) Google Veo integration.
"""
from __future__ import annotations

import cgi
import json
import os
import posixpath
import shutil
import tempfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Tuple

PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def generate_video_using_veo(file_path: Path, prompt: str | None = None) -> dict:
    """Placeholder Veo client call.

    In a production system this function would call Google Veo 2/3 using the
    developer's API key.  The implementation below simply returns a mocked payload
    that mirrors the shape you might expect from a real integration.
    """

    # NOTE: The real API call is omitted because Google Veo credentials are not
    # available inside this execution environment.  Instead we generate a fake
    # response that demonstrates the shape of the data the front-end expects.
    return {
        "videoUrl": "https://example.com/generated-veo-ad.mp4",
        "jobId": "demo-job-1234",
        "status": "queued",
        "usedPrompt": prompt or "(default prompt)",
        "sourceModel": file_path.name,
    }


class VeoRequestHandler(BaseHTTPRequestHandler):
    server_version = "VeoUploadServer/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        """Support CORS preflight requests for development convenience."""
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # The method names have to remain camelCase to satisfy BaseHTTPRequestHandler's API.
    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        """Serve static files from the `public` directory."""
        if self.path == "/" or self.path == "":
            path = PUBLIC_DIR / "index.html"
        else:
            # Remove query parameters and normalise the path to prevent directory traversal.
            path = PUBLIC_DIR / self._translate_path(self.path)

        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        self.send_response(HTTPStatus.OK)
        self._send_common_headers()
        self.send_header("Content-Type", self._guess_type(path))
        self.end_headers()
        with path.open("rb") as file_obj:
            shutil.copyfileobj(file_obj, self.wfile)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/api/generate":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
        if ctype != "multipart/form-data":
            self.send_error(HTTPStatus.BAD_REQUEST, "Expected multipart/form-data")
            return

        # Limit uploads to 100 MB to prevent accidental large files.
        if int(self.headers.get("Content-Length", 0)) > 100 * 1024 * 1024:
            self.send_error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "File too large")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers.get("Content-Type"),
            },
        )

        upload_field = form["model"] if "model" in form else None
        if upload_field is None or not getattr(upload_field, "filename", ""):
            self.send_error(HTTPStatus.BAD_REQUEST, "Missing model file upload")
            return

        file_suffix = Path(upload_field.filename).suffix.lower()
        if file_suffix not in {".gltf", ".glb"}:
            self.send_error(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, "Only GLTF/GLB files are supported")
            return

        prompt_field = form.getfirst("prompt") if "prompt" in form else None

        temp_fd, temp_path = tempfile.mkstemp(suffix=file_suffix, dir=UPLOAD_DIR)
        with os.fdopen(temp_fd, "wb") as dest:
            shutil.copyfileobj(upload_field.file, dest)

        # Call the mocked Veo integration.
        try:
            response_payload = generate_video_using_veo(Path(temp_path), prompt_field)
        finally:
            # Clean up the temporary file to avoid unbounded storage growth.
            Path(temp_path).unlink(missing_ok=True)

        response_bytes = json.dumps(response_payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self._send_common_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def log_message(self, format: str, *args) -> None:  # noqa: A003 - matches BaseHTTPRequestHandler signature
        """Log to stdout instead of stderr to make container logs easier to read."""
        message = "%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args)
        print(message, end="")

    def _send_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")

    def _translate_path(self, url_path: str) -> Path:
        path = posixpath.normpath(url_path.split("?", 1)[0].lstrip("/"))
        return Path(path)

    def _guess_type(self, path: Path) -> str:
        if path.suffix == ".css":
            return "text/css"
        if path.suffix == ".js":
            return "application/javascript"
        if path.suffix in {".html", ".htm"}:
            return "text/html"
        if path.suffix == ".json":
            return "application/json"
        if path.suffix == ".png":
            return "image/png"
        if path.suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if path.suffix == ".svg":
            return "image/svg+xml"
        return "application/octet-stream"


def run_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    server_address: Tuple[str, int] = (host, port)
    httpd = ThreadingHTTPServer(server_address, VeoRequestHandler)
    print(f"Serving on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
