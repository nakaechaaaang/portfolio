"""ブラウザ校閲UI 用のローカルサーバ（標準ライブラリのみ）。

- GET  /                … review/index.html を返す
- GET  /api/data        … 現在の校閲JSONを返す
- POST /api/save        … 受け取った items で上書き保存（reviewed のまま）
- POST /api/done        … reviewed=true で保存し、校閲完了を通知してサーバ停止
- GET  /media/audio.wav … プレビュー再生用の音声

校閲は JSON に対して行う＝JSONが真実。SRTはここから後段で生成する。
"""
from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import build

UI_HTML = Path(__file__).resolve().parent.parent / "review" / "index.html"


def run_review(doc_path: str | Path, *, port: int = 8765, open_browser: bool = True) -> dict:
    """校閲サーバを起動し、ユーザーが「校閲完了」を押すまでブロックする。

    完了後の（reviewed=true の）ドキュメントを返す。
    """
    doc_path = Path(doc_path)
    done = threading.Event()
    state = {"doc": build.load_doc(doc_path)}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # 黙らせる
            pass

        def _send(self, code, body=b"", ctype="application/json; charset=utf-8"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, UI_HTML.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/api/data":
                body = json.dumps(state["doc"], ensure_ascii=False).encode("utf-8")
                self._send(200, body)
            elif self.path.startswith("/media/audio"):
                audio = Path(state["doc"].get("audio_path", ""))
                if audio.exists():
                    self._send(200, audio.read_bytes(), "audio/wav")
                else:
                    self._send(404)
            else:
                self._send(404)

        def _read_json(self):
            length = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(length) or b"{}")

        def do_POST(self):
            if self.path in ("/api/save", "/api/done"):
                payload = self._read_json()
                doc = state["doc"]
                if "items" in payload:
                    doc["items"] = payload["items"]
                for key in ("offset_sec", "max_close_gap_sec"):
                    if key in payload:
                        doc[key] = payload[key]
                if self.path == "/api/done":
                    doc["reviewed"] = True
                build.save_doc(doc_path, doc)
                self._send(200, b'{"ok":true}')
                if self.path == "/api/done":
                    done.set()
            else:
                self._send(404)

    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    url = f"http://127.0.0.1:{port}/"
    print(f"\n🖊  校閲UIを開きました: {url}")
    print("   テキスト修正・不要字幕の削除・フィラー確認を行い、")
    print("   最後に「校閲完了」を押してください（このまま待機します）。\n")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        done.wait()
    except KeyboardInterrupt:
        print("\n中断しました。校閲JSONは保存済みです。")
    finally:
        httpd.shutdown()

    return build.load_doc(doc_path)
