#!/usr/bin/env python3
import argparse
import os
import socket
import urllib.parse
import datetime

CRLF = b"\r\n"

MIME_MAP = {
    ".html": "text/html; charset=utf-8",
    ".png":  "image/png",
    ".pdf":  "application/pdf",
}

def http_date_now():
    return datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

def build_response(status_code, reason, headers=None, body=b""):
    lines = [f"HTTP/1.1 {status_code} {reason}"]
    base_headers = {
        "Server": "MinimalPySocketServer/1.0",
        "Date": http_date_now(),
        "Connection": "close",
        "Content-Length": str(len(body)),
    }
    if headers:
        base_headers.update(headers)
    for k, v in base_headers.items():
        lines.append(f"{k}: {v}")
    head = (("\r\n").join(lines) + "\r\n\r\n").encode("utf-8")
    return head + body

def safe_join(root, url_path):
    decoded = urllib.parse.unquote(url_path)
    if decoded == "/":
        decoded = "/"
    fs_path = os.path.realpath(os.path.join(root, decoded.lstrip("/")))
    root_real = os.path.realpath(root)
    if not fs_path.startswith(root_real):
        return None
    return fs_path

def guess_mime(path):
    _, ext = os.path.splitext(path.lower())
    return MIME_MAP.get(ext)

def make_dir_listing_html(url_path, abs_dir_path):
    # Breadcrumbs
    parts = url_path.rstrip('/').split('/')
    breadcrumbs = []
    for i in range(len(parts)):
        if not parts[i]:
            href = '/'
            name = 'root'
        else:
            href = '/' + '/'.join(parts[1:i+1])
            name = parts[i]
        breadcrumbs.append(f'<a href="{href}">{name}</a>')
    breadcrumb_html = ' / '.join(breadcrumbs)

    rows = []
    if url_path != "/":
        parent = os.path.dirname(url_path.rstrip("/"))
        if not parent:
            parent = "/"
        rows.append(f'<tr><td>📁</td><td colspan="3"><a href="{parent or "/"}">.. (parent dir)</a></td></tr>')

    for name in sorted(os.listdir(abs_dir_path)):
        full = os.path.join(abs_dir_path, name)
        is_dir = os.path.isdir(full)
        display = name + ("/" if is_dir else "")
        href = urllib.parse.urljoin(url_path.rstrip("/") + "/", name)
        size = "-" if is_dir else f"{os.path.getsize(full)/1024:.1f} KB"
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(full)).strftime('%Y-%m-%d %H:%M')
        icon = "📁" if is_dir else "📄"
        rows.append(f'<tr><td>{icon}</td><td><a href="{href}">{display}</a></td><td>{size}</td><td>{mtime}</td></tr>')

    body = f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Index of {url_path}</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; background: #f3f6fa; color: #222; margin: 0; }}
    .listing-container {{ max-width: 750px; background: white; border-radius: 18px; margin: 40px auto; padding: 32px 40px; box-shadow: 0 9px 32px rgba(80, 118, 181, 0.10); }}
    .breadcrumb {{ font-size: 1em; margin-bottom: 25px; color: #999; }}
    .breadcrumb a {{ color: #4578e1; text-decoration: none; margin-right: 4px; }}
    .breadcrumb a:hover {{ text-decoration: underline; }}
    h1 {{ font-size: 1.45em; margin-bottom: 22px; color: #2c3e50; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 12px; text-align: left; }}
    th {{ background: #f8fafd; border-bottom: 2px solid #e9edf3; color: #4d6488; font-size: 1em; font-weight: 600; }}
    td {{ border-bottom: 1px solid #ecf0f3; font-size: 1em; }}
    tr:last-child td {{ border-bottom: none; }}
    a {{ color: #397bd6; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    tr:hover td {{ background: #f3f6fb; }}
    @media (max-width: 600px) {{ .listing-container {{ padding: 7vw 3vw; }} th, td {{ font-size: 0.97em; padding: 7px 6px; }} }}
  </style>
</head>
<body>
  <div class="listing-container">
    <div class="breadcrumb">{breadcrumb_html}</div>
    <h1>Index of {url_path}</h1>
    <table>
      <tr><th style="width:30px"></th><th>Name</th><th style="width:100px">Size</th><th style="width:160px">Last modified</th></tr>
      {''.join(rows)}
    </table>
  </div>
</body>
</html>'''
    return body.encode("utf-8")

def custom_404_html(path):
    html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>404 Not Found</title>
<style>
  body {{ font-family: Segoe UI, sans-serif; background: #f3f6fa; color: #222; margin:0; }}
  .container {{ max-width:450px; margin:60px auto; background:white; border-radius:18px; box-shadow:0 5px 24px #b1b8cd22; padding:36px 35px 32px 35px; text-align:center; }}
  h1 {{ font-size:2.9em; margin-bottom:12px; color: #db3a34; }}
  p {{ font-size:1.16em; color:#526485; margin-bottom:22px; }}
  .big-icon {{ font-size:3em; margin-bottom:10px; }}
  a.btn {{ display:inline-block; background:#397bd6; color:white; padding:11px 28px; border-radius:8px; text-decoration:none; font-weight:600; margin-top:10px; font-size:1.06em; }}
  a.btn:hover {{ background: #2b5fa5; }}
</style>
</head>
<body>
  <div class="container">
    <div class="big-icon">🔍</div>
    <h1>404 Not Found</h1>
    <p>No file or directory found at<br><code>{path}</code></p>
    <a class="btn" href="/">Go to Home</a>
  </div>
</body>
</html>'''
    return html.encode("utf-8")

def handle_client(conn, addr, root):
    data = b""
    conn.settimeout(2.0)
    try:
        while b"\r\n\r\n" not in data and len(data) < 65536:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
    except socket.timeout:
        pass

    if not data:
        conn.sendall(build_response(400, "Bad Request", body=b""))
        return

    try:
        header_text = data.split(b"\r\n\r\n", 1)[0].decode("iso-8859-1")
        request_line = header_text.split("\r\n", 1)[0]
        method, path, _ = request_line.split(" ")
    except Exception:
        conn.sendall(build_response(400, "Bad Request", body=b""))
        return

    if method.upper() != "GET":
        conn.sendall(build_response(405, "Method Not Allowed",
                   headers={"Allow": "GET"},
                   body=b""))
        return

    fs_path = safe_join(root, path)
    if fs_path is None:
        conn.sendall(build_response(403, "Forbidden", body=b""))
        return

    if os.path.isdir(fs_path):
        body = make_dir_listing_html(path, fs_path)
        resp = build_response(200, "OK",
                              headers={"Content-Type": "text/html; charset=utf-8"},
                              body=body)
        conn.sendall(resp)
        return

    if os.path.isfile(fs_path):
        mime = guess_mime(fs_path)
        if not mime:
            conn.sendall(build_response(404, "Not Found", body=custom_404_html(path)))
            return
        try:
            with open(fs_path, "rb") as f:
                body = f.read()
            resp = build_response(200, "OK",
                                  headers={"Content-Type": mime},
                                  body=body)
            conn.sendall(resp)
            return
        except OSError:
            conn.sendall(build_response(500, "Internal Server Error", body=b""))
            return

    conn.sendall(build_response(404, "Not Found", body=custom_404_html(path)))

def run_server(root_dir, host, port):
    print(f"[INFO] Serving '{root_dir}' at http://{host}:{port} (one request at a time)")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            with conn:
                handle_client(conn, addr, root_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Minimal HTTP file server (single-connection).")
    parser.add_argument("root", help="Directory to serve")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    if not os.path.isdir(args.root):
        raise SystemExit(f"Error: directory not found: {args.root}")

    run_server(args.root, args.host, args.port)
