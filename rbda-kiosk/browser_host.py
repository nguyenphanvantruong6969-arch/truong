"""
browser_host.py
===============
Chế độ chạy DỰ PHÒNG: phục vụ chính giao diện trong index.html/recovery.html
qua một máy chủ HTTP cục bộ rồi mở bằng TRÌNH DUYỆT MẶC ĐỊNH của máy, thay
vì cửa sổ pywebview.

VÌ SAO CẦN: trên Windows, backend duy nhất của pywebview (winforms) bắt buộc
đi qua pythonnet -> .NET Framework. Đây là mắt xích hay hỏng nhất khi đóng
gói bằng PyInstaller — đã gặp lỗi thật trên máy người dùng:

    RuntimeError: Failed to resolve Python.Runtime.Loader.Initialize
    from ...\\_internal\\pythonnet\\runtime\\Python.Runtime.dll

(tệp DLL CÓ mặt nhưng .NET từ chối nạp; nguyên nhân nằm ngoài tầm kiểm soát
của mã nguồn). Chế độ này KHÔNG dùng pythonnet/.NET/GUI toolkit nào cả —
chỉ thư viện chuẩn của Python + trình duyệt vốn đã có sẵn trên mọi máy
Windows — nên gần như không thể hỏng vì lý do đóng gói.

CÁCH HOẠT ĐỘNG: giao diện hiện tại gọi backend qua
`window.pywebview.api.<ten_ham>(...)`. Máy chủ này CHÈN một đoạn JS nhỏ vào
mỗi trang HTML nó phục vụ, dựng sẵn `window.pywebview.api` giả lập bằng
Proxy — mỗi lời gọi biến thành một POST tới /__api__/<ten_ham>. Nhờ vậy
app.js và recovery.js GIỮ NGUYÊN, không cần biết mình đang chạy ở chế độ
nào.

AN TOÀN: chỉ lắng nghe trên 127.0.0.1 (không ra ngoài mạng), và mọi lời gọi
API phải kèm token ngẫu nhiên sinh lúc khởi động — để một trang web bất kỳ
đang mở trong cùng trình duyệt không thể tự gọi vào API quản trị này.
"""

import functools
import http.server
import json
import os
import secrets
import threading
import time
import webbrowser

# Không có ping trong ngần này giây -> coi như người dùng đã đóng tab và tự
# tắt tiến trình. Nếu không có cơ chế này, bản đóng gói console=False sẽ
# chạy ngầm mãi sau khi người dùng đóng trình duyệt (không có cửa sổ nào để
# tắt, phải vào Task Manager).
_PING_TIMEOUT_SECONDS = 25
_PING_INTERVAL_MS = 3000

_SHIM_TEMPLATE = """
<script>
/* Cau noi che do trinh duyet — dung san window.pywebview.api gia lap de
   app.js/recovery.js chay y nguyen, khong can sua gi. */
(function () {
  "use strict";
  var TOKEN = "__TOKEN__";

  function call(name, args) {
    return fetch("/__api__/" + encodeURIComponent(name), {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Kiosk-Token": TOKEN },
      body: JSON.stringify({ args: args }),
    }).then(function (r) {
      return r.json();
    });
  }

  window.pywebview = {
    api: new Proxy({}, {
      has: function () { return true; },
      get: function (_target, name) {
        if (typeof name !== "string") return undefined;
        return function () {
          return call(name, Array.prototype.slice.call(arguments));
        };
      },
    }),
  };

  /* Bao cho may chu biet tab van dang mo. */
  function ping() { fetch("/__ping__", { method: "POST" }).catch(function () {}); }
  ping();
  setInterval(ping, __PING_INTERVAL__);
})();
</script>
"""


class _Handler(http.server.SimpleHTTPRequestHandler):
    # gan boi serve(): api object, token, resource dir, va callback ping
    api = None
    token = ""
    on_ping = None

    def log_message(self, *args):
        """Im lang — ban dong goi console=False khong co stderr de ghi."""

    # ---------------------------------------------------------------- #

    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        return secrets.compare_digest(
            self.headers.get("X-Kiosk-Token", ""), self.token
        )

    def do_POST(self):
        if self.path == "/__ping__":
            if callable(self.on_ping):
                self.on_ping()
            self._send_json({"ok": True})
            return

        if not self.path.startswith("/__api__/"):
            self._send_json({"ok": False, "errors": ["unknown endpoint"]}, 404)
            return

        if not self._authorized():
            self._send_json({"ok": False, "errors": ["forbidden"]}, 403)
            return

        from urllib.parse import unquote

        name = unquote(self.path[len("/__api__/"):])
        # Chi cho goi phuong thuc cong khai — khong de lo _backup_db,
        # _move_corrupt_db_aside... ra ngoai qua HTTP.
        if name.startswith("_") or not hasattr(self.api, name):
            self._send_json({"ok": False, "errors": [f"unknown method: {name}"]}, 404)
            return
        method = getattr(self.api, name)
        if not callable(method):
            self._send_json({"ok": False, "errors": [f"not callable: {name}"]}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            args = payload.get("args", [])
            result = method(*args)
        except Exception as e:
            import traceback

            self._send_json({
                "ok": False,
                "data": None,
                "errors": [str(e), traceback.format_exc()],
            })
            return

        self._send_json(result)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", ""):
            path = "/" + self.server.start_page

        if path.endswith(".html"):
            full = os.path.join(self.directory, path.lstrip("/"))
            if not os.path.isfile(full):
                self.send_error(404)
                return
            with open(full, "r", encoding="utf-8") as f:
                html = f.read()
            shim = (
                _SHIM_TEMPLATE
                .replace("__TOKEN__", self.token)
                .replace("__PING_INTERVAL__", str(_PING_INTERVAL_MS))
            )
            # Chen TRUOC </head> de window.pywebview ton tai ngay khi
            # app.js chay -> app.js goi init() thang, dung nhu khi co
            # pywebview that.
            if "</head>" in html:
                html = html.replace("</head>", shim + "</head>", 1)
            else:
                html = shim + html
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.path = path
        super().do_GET()


def serve(api, resource_dir: str, start_page: str = "index.html",
          open_browser: bool = True) -> str:
    """
    Khởi động máy chủ cục bộ và mở trình duyệt. Hàm này CHẶN (blocking)
    cho tới khi người dùng đóng tab (không còn ping) — giống webview.start().
    Trả về URL đã phục vụ (hữu ích khi test, với open_browser=False).
    """
    token = secrets.token_urlsafe(24)
    state = {"last_ping": None}

    def on_ping():
        state["last_ping"] = time.time()

    bound = type("_BoundHandler", (_Handler,), {
        "api": api,
        "token": token,
        "on_ping": staticmethod(on_ping),
    })
    # SimpleHTTPRequestHandler dat self.directory TRONG __init__, nen gan
    # o cap lop se bi ghi de -> phai truyen qua tham so khoi tao.
    handler = functools.partial(bound, directory=resource_dir)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.start_page = start_page

    url = f"http://127.0.0.1:{httpd.server_address[1]}/{start_page}?t={token}"

    def watchdog():
        while True:
            time.sleep(5)
            last = state["last_ping"]
            # Chua co ping nao -> trang chua kip mo, chua tinh gio.
            if last is not None and time.time() - last > _PING_TIMEOUT_SECONDS:
                threading.Thread(target=httpd.shutdown, daemon=True).start()
                return

    threading.Thread(target=watchdog, daemon=True).start()

    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
        httpd.serve_forever()
        httpd.server_close()
    else:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

    return url
