import os, socket, threading, mimetypes, urllib.parse, time

HOST, PORT = "0.0.0.0", 8080
DOCROOT = os.path.join(os.path.dirname(__file__), "content")
REQUEST_COUNTERS = {}
LOCK = threading.Lock()

def guess_type(path):
    typ, _ = mimetypes.guess_type(path)
    return typ or "application/octet-stream"

def http_response(status, headers, body=b""):
    reasons = {200:"OK", 400:"Bad Request", 404:"Not Found", 405:"Method Not Allowed", 500:"Internal Server Error"}
    reason = reasons.get(status, "OK")
    head_lines = [f"HTTP/1.1 {status} {reason}"]
    for k, v in headers.items():
        head_lines.append(f"{k}: {v}")
    head_lines.append("Connection: close")
    return ("\r\n".join(head_lines) + "\r\n\r\n").encode("utf-8") + body

def list_files_with_counters():
    rows = []
    for dirpath, _, filenames in os.walk(DOCROOT):
        for fn in sorted(filenames):
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, DOCROOT).replace(os.sep, "/")
            count = REQUEST_COUNTERS.get("/" + rel, 0)
            rows.append(f"<tr><td><a href='/{rel}'>/{rel}</a></td><td style='text-align:right'>{count}</td></tr>")
    table = "\n".join(rows) if rows else "<tr><td colspan='2'>(empty)</td></tr>"
    variant_label = os.environ.get("VARIANT", os.path.basename(__file__))
    html = f"""<!doctype html><html><head><meta charset='utf-8'><title>Lab 2 — Directory</title>
<style>
:root {{ --cream: #fbf6f0; --peach: #fde3c9; --black: #221d10; --indigo: #550c72; }}
body{{font-family:Inter,system-ui,Arial;background:linear-gradient(135deg,var(--cream),var(--peach));color:var(--black);margin:0}}
header{{padding:24px 20px;border-bottom:2px solid rgba(34,29,16,.08);text-align:center}}
h1{{margin:0;font-size:26px;color:var(--indigo)}}
.wrap{{max-width:960px;margin:0 auto;padding:20px}}
.card{{background:#ffffffcc;border:1px solid rgba(34,29,16,.12);border-radius:20px;padding:18px;box-shadow:0 10px 25px rgba(34,29,16,.08)}}
table{{width:100%;border-collapse:collapse;margin-top:10px}}
td,th{{border-bottom:1px solid rgba(34,29,16,.12);padding:10px}}
th{{text-align:left;color:#5b4e3a;font-weight:600}}
.badge{{display:inline-block;background:var(--peach);border:1px solid rgba(34,29,16,.18);border-radius:999px;padding:6px 10px;color:var(--black)}}
a{{color:var(--indigo)}}
</style></head>
<body>
<header>
  <h1>Lab 2 — Concurrent HTTP Server</h1>
  <div class="badge">Open multiple tabs or use client.py to generate load</div>
</header>
<div class="wrap">
  <div class="card">
    <h2 style="margin:0 0 10px 0">Directory listing with per-file request counters</h2>
    <table>
      <tr><th>Path</th><th style='text-align:right'>Requests Served</th></tr>
      {table}
    </table>
    <p style="margin-top:12px">Variant: <strong>{variant_label}</strong></p>
  </div>
</div>
</body></html>"""
    return html

def safe_path(url_path):
    if url_path == "/":
        body = list_files_with_counters().encode("utf-8")
        return None, http_response(200, {"Content-Type":"text/html; charset=utf-8","Content-Length":str(len(body))}, body)
    rel = os.path.normpath(urllib.parse.unquote(url_path).lstrip("/"))
    full = os.path.join(DOCROOT, rel)
    return full, None

def inc_counter(path, use_lock=False):
    if use_lock:
        with LOCK:
            REQUEST_COUNTERS[path] = REQUEST_COUNTERS.get(path, 0) + 1
    else:
        old = REQUEST_COUNTERS.get(path, 0)
        time.sleep(0.0005)  # widen race window
        REQUEST_COUNTERS[path] = old + 1

def handle_client(conn, addr, use_lock=False):
    try:
        try:
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 65536:
                chunk = conn.recv(4096)
                if not chunk: break
                data += chunk
            if not data:
                conn.sendall(http_response(400, {"Content-Length":"0"})); return

            line = data.split(b"\r\n", 1)[0].decode("utf-8", "ignore")
            parts = line.split()
            if len(parts) < 3:
                conn.sendall(http_response(400, {"Content-Length":"0"})); return
            method, path, _ = parts

            if method != "GET":
                conn.sendall(http_response(405, {"Allow":"GET","Content-Length":"0"})); return

            fs_path, direct = safe_path(path)
            if direct is not None:
                conn.sendall(direct); return

            if not os.path.isfile(fs_path):
                conn.sendall(http_response(404, {"Content-Length":"0"})); return

            inc_counter(path, use_lock=use_lock)

            with open(fs_path, "rb") as f:
                body = f.read()
            headers = {"Content-Type": guess_type(fs_path), "Content-Length": str(len(body))}
            conn.sendall(http_response(200, headers, body))
        except Exception as e:
            msg = f"Internal error: {e}\n".encode("utf-8", "ignore")
            conn.sendall(http_response(500, {"Content-Type":"text/plain; charset=utf-8","Content-Length":str(len(msg))}, msg))
    finally:
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        conn.close()

def server_loop(use_lock=False):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(256)
        mode = "LOCK" if use_lock else "RACE"
        print(f"[lab2 {mode}] http://{HOST}:{PORT} serving from {DOCROOT}")
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr, use_lock), daemon=True)
            t.start()

if __name__ == '__main__':
    server_loop(use_lock=False)
