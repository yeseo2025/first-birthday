#!/usr/bin/env python3
"""돌잔치 초대장 미리보기용 정적 서버 (저장 시 자동 새로고침).

index.html을 서빙할 때 라이브 리로드 스크립트를 주입한다.
파일이 바뀌면 브라우저가 1초 안에 자동으로 새로고침된다.
"""
import http.server
import os
import socketserver

PORT = int(os.environ.get("PORT", "5050"))
ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(ROOT, "index.html")

LIVERELOAD = b"""
<script>
(function(){
  let last = null;
  async function tick(){
    try{
      const r = await fetch('/__livereload', {cache:'no-store'});
      const t = await r.text();
      if(last !== null && t !== last){ location.reload(); }
      last = t;
    }catch(e){}
  }
  setInterval(tick, 1000); tick();
})();
</script>
"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def log_message(self, fmt, *args):
        pass  # 조용히

    def do_GET(self):
        if self.path == "/__livereload":
            try:
                mtime = str(os.path.getmtime(INDEX)).encode()
            except OSError:
                mtime = b"0"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(mtime)
            return

        if self.path in ("/", "/index.html"):
            with open(INDEX, "rb") as f:
                body = f.read()
            if b"</body>" in body:
                body = body.replace(b"</body>", LIVERELOAD + b"</body>", 1)
            else:
                body += LIVERELOAD
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        super().do_GET()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Preview running at http://127.0.0.1:{PORT}")
        httpd.serve_forever()
