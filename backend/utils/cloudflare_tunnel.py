"""
Cloudflare Tunnel manager for public access without a server.

Uses cloudflared (https://github.com/cloudflare/cloudflared) to create
a secure tunnel from localhost to a public *.trycloudflare.com URL.
"""
import subprocess
import threading
import time
import re
import sys


_tunnel_url: str | None = None
_tunnel_process: subprocess.Popen | None = None


def _find_cloudflared() -> str | None:
    """Find cloudflared executable."""
    import shutil
    return shutil.which("cloudflared")


def _stream_reader(stream, prefix: str):
    """Read lines from a stream and print them (runs in thread)."""
    try:
        for line in iter(stream.readline, b""):
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                print(f"[cloudflared] {text}")
    except Exception:
        pass


def start_tunnel(port: int = 8000) -> str | None:
    """
    Start a Cloudflare Tunnel to expose localhost:port.

    Returns the public URL if successful, None otherwise.
    """
    global _tunnel_url, _tunnel_process

    if _tunnel_process is not None:
        return _tunnel_url

    cloudflared = _find_cloudflared()
    if not cloudflared:
        print("[cloudflared] cloudflared not found. Install: https://github.com/cloudflare/cloudflared")
        print("[cloudflared] Or: winget install Cloudflare.cloudflared")
        return None

    try:
        _tunnel_process = subprocess.Popen(
            [cloudflared, "tunnel", "--url", f"http://localhost:{port}", "--no-autoupdate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        # Read output to find the public URL
        start_time = time.time()
        url_pattern = re.compile(r"https://[\w-]+\.trycloudflare\.com")

        for line in iter(_tunnel_process.stdout.readline, b""):
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                print(f"[cloudflared] {text}")
                match = url_pattern.search(text)
                if match:
                    _tunnel_url = match.group(0)
                    print(f"\n{'='*60}")
                    print(f"  Public URL: {_tunnel_url}")
                    print(f"{'='*60}\n")
                    # Continue reading in background
                    threading.Thread(
                        target=_stream_reader,
                        args=(_tunnel_process.stdout, "cloudflared"),
                        daemon=True,
                    ).start()
                    return _tunnel_url

            if time.time() - start_time > 30:
                print("[cloudflared] Timeout waiting for tunnel URL")
                break

    except Exception as e:
        print(f"[cloudflared] Failed to start tunnel: {e}")

    return None


def stop_tunnel():
    """Stop the Cloudflare Tunnel."""
    global _tunnel_process, _tunnel_url
    if _tunnel_process:
        _tunnel_process.terminate()
        _tunnel_process = None
        _tunnel_url = None
        print("[cloudflared] Tunnel stopped.")


def get_tunnel_url() -> str | None:
    """Get the current tunnel URL."""
    return _tunnel_url
