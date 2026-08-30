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
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser

# LÀM SAO BIẾT CỬA SỔ CÒN MỞ
#
# Bản đóng gói chạy `console=False`: đóng cửa sổ mà tiến trình không tự
# tắt thì nó chạy ngầm mãi, phải vào Task Manager mới diệt được.
#
# Cách cũ là đếm ping do `setInterval` gửi, không có ping quá 120 giây thì
# tự tắt. CÁCH ĐÓ SAI, và đã hỏng thật trên máy học sinh ngày 30/08:
# trình duyệt hiện ĐÓNG BĂNG hẳn bộ đếm giờ của trang đang bị che
# (Chromium gọi là intensive throttling; Edge trên Windows còn bật thêm
# "Efficiency mode" — nhìn thấy rõ trong ảnh Task Manager của học sinh).
# Trang bị đóng băng thì ping ngừng hẳn, không phải thưa đi. Máy chủ tự
# tắt trong khi cửa sổ VẪN ĐANG MỞ. Người dùng quay lại thấy giao diện
# còn nguyên (trình duyệt giữ lại hình đã vẽ) nhưng mọi thao tác đều báo
# "TypeError: Failed to fetch" — không một dấu hiệu nào cho biết vì sao.
#
# Cách mới: trang mở một KẾT NỐI SỰ KIỆN (EventSource) và giữ nguyên đó.
# Trình duyệt KHÔNG đóng băng socket đang mở — nó chỉ đóng băng bộ đếm
# giờ. Cửa sổ còn mở thì socket còn đó, dù trang bị đóng băng bao lâu.
# Đóng cửa sổ thì socket đứt ngay, máy chủ biết tức khắc.
#
# Ping cũ vẫn giữ, nhưng chỉ còn là lưới đỡ cho trường hợp EventSource
# không kết nối được lần nào. Khi đã có ít nhất một kết nối sống thì
# ngưỡng chờ rút xuống _GRACE_SECONDS, vì lúc đó socket đứt là tín hiệu
# chắc chắn, không cần chờ lâu.
_PING_TIMEOUT_SECONDS = 120     # chỉ dùng khi EventSource chưa từng kết nối
_GRACE_SECONDS = 20             # chờ sau khi kết nối cuối cùng đứt
_ALIVE_BEAT_SECONDS = 10        # nhịp ghi vào socket để phát hiện đứt
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

  /* Bao cho may chu biet cua so van dang mo.

     Ket noi EventSource nay la tin hieu CHINH. No la mot socket mo, ma
     trinh duyet khong dong bang socket — chi dong bang bo dem gio. Nen
     cua so con mo thi may chu con biet, du trang bi che bao lau.
     EventSource tu ket noi lai neu duong truyen dut quang. */
  try {
    var song = new EventSource("/__alive__?t=" + encodeURIComponent(TOKEN));
    song.onerror = function () { /* tu ket noi lai, khong lam gi */ };
  } catch (e) { /* trinh duyet qua cu -> con ping o duoi do */ }

  /* Ping cu: luoi do khi EventSource khong dung duoc. */
  function ping() { fetch("/__ping__", { method: "POST" }).catch(function () {}); }
  ping();
  setInterval(ping, __PING_INTERVAL__);

  /* Dong cua so -> bao NGAY, khong de tien trinh chay ngam.
     Dung `pagehide` (khong phai `unload`) vi day la su kien duy nhat
     trinh duyet bao dam ban ra khi trang bi dong, va sendBeacon van gui
     duoc trong luc trang dang bi huy. */
  window.addEventListener("pagehide", function () {
    try {
      navigator.sendBeacon("/__closed__?t=" + encodeURIComponent(TOKEN));
    } catch (e) { /* dong duoc la tot, khong dong duoc thi da co nguong cho */ }
  });
})();
</script>
"""


class _Handler(http.server.SimpleHTTPRequestHandler):
    # gan boi serve(): api object, token, resource dir, va callback ping
    api = None
    token = ""
    on_ping = None
    on_closed = None
    on_alive_open = None
    on_alive_close = None

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

    def _giu_ket_noi_song(self):
        """Giữ một kết nối mở suốt thời gian cửa sổ còn sống.

        Ghi một dòng chú thích SSE mỗi _ALIVE_BEAT_SECONDS giây. Cửa sổ
        đóng thì lần ghi kế tiếp hỏng — đó là lúc biết chắc, không phải
        đoán qua nhịp ping có thể bị đóng băng.
        """
        from urllib.parse import parse_qs, urlparse

        sent = parse_qs(urlparse(self.path).query).get("t", [""])[0]
        if not secrets.compare_digest(sent, self.token):
            self.send_error(403)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        if callable(self.on_alive_open):
            self.on_alive_open()
        try:
            while True:
                self.wfile.write(b": con-song\n\n")
                self.wfile.flush()
                time.sleep(_ALIVE_BEAT_SECONDS)
        except Exception:
            pass
        finally:
            if callable(self.on_alive_close):
                self.on_alive_close()

    def do_POST(self):
        if self.path == "/__ping__":
            if callable(self.on_ping):
                self.on_ping()
            self._send_json({"ok": True})
            return

        if self.path.split("?", 1)[0] == "/__closed__":
            # Cua so da dong -> tat may chu ngay, khong cho het nguong.
            # Bat buoc co token: khong de mot trang web khac dang mo trong
            # cung may do trung cong roi tat app dang chay do.
            from urllib.parse import parse_qs, urlparse

            sent = parse_qs(urlparse(self.path).query).get("t", [""])[0]
            if not secrets.compare_digest(sent, self.token):
                self._send_json({"ok": False, "errors": ["forbidden"]}, 403)
                return
            self._send_json({"ok": True})
            if callable(self.on_closed):
                self.on_closed()
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

        if path == "/__alive__":
            self._giu_ket_noi_song()
            return

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


# ------------------------------------------------------------------ #
# MỞ GIAO DIỆN NHƯ MỘT ỨNG DỤNG RIÊNG (KHÔNG PHẢI TAB TRÌNH DUYỆT)
#
# Mọi trình duyệt nhân Chromium (Edge, Chrome, Brave, Chromium) đều hiểu
# cờ `--app=<url>`: mở MỘT CỬA SỔ RIÊNG — không thanh địa chỉ, không
# thanh tab, không nút Back/Refresh — và có mục riêng trên thanh tác vụ.
# Nhìn và dùng y như một ứng dụng desktop.
#
# VÌ SAO QUAN TRỌNG VỚI KIOSK: máy đặt ở trường, học sinh tự thao tác.
# Có thanh địa chỉ nghĩa là gõ được sang trang khác, đóng nhầm tab của
# app, hoặc thấy cả token trong URL. Chế độ --app bỏ hết những thứ đó.
#
# VÌ SAO KHÔNG DÙNG FIREFOX: Firefox không có cờ tương đương. `-kiosk`
# của nó chiếm trọn màn hình và không có nút đóng — quá tay cho phòng
# máy dùng chung. Nên chỉ tìm nhóm Chromium; nếu máy không có con nào,
# mới quay về mở tab thường (vẫn dùng được, chỉ kém đẹp).
#
# Windows 10/11 LUÔN có sẵn Microsoft Edge, nên trên máy trường gần như
# chắc chắn tìm được. Đường dẫn Edge cũng được thử TRƯỚC Chrome.
# ------------------------------------------------------------------ #

# CREATE_NO_WINDOW — không để nháy cửa sổ console đen khi khởi chạy
# trình duyệt từ bản đóng gói console=False.
_CREATE_NO_WINDOW = 0x08000000

_APP_WINDOW_EXE_NAMES = (
    "msedge", "chrome", "google-chrome", "chromium", "chromium-browser",
    "brave", "brave-browser",
)

_APP_WINDOW_RELATIVE_PATHS_WINDOWS = (
    r"Microsoft\Edge\Application\msedge.exe",
    r"Google\Chrome\Application\chrome.exe",
    r"BraveSoftware\Brave-Browser\Application\brave.exe",
)


def _windows_candidates():
    """Đường dẫn cài đặt tiêu chuẩn trên Windows, Edge trước tiên."""
    roots = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    return [
        os.path.join(root, rel)
        for rel in _APP_WINDOW_RELATIVE_PATHS_WINDOWS
        for root in roots
        if root
    ]


def find_app_window_browser():
    """Tìm một trình duyệt nhân Chromium để mở cửa sổ riêng.

    Trả về đường dẫn, hoặc None nếu máy không có con nào (lúc đó
    open_ui sẽ quay về mở tab trình duyệt mặc định).

    Biến môi trường RBDA_BROWSER cho phép người vận hành chỉ định thẳng
    trình duyệt khi máy trường cài ở đường dẫn không tiêu chuẩn. Nếu
    giá trị đó sai/không tồn tại thì BỎ QUA và tìm tiếp như bình thường
    — không được để một biến gõ nhầm làm app không mở lên được.
    """
    override = os.environ.get("RBDA_BROWSER", "").strip()
    if override:
        if os.path.isfile(override):
            return override
        found = shutil.which(override)
        if found:
            return found

    if sys.platform.startswith("win"):
        for path in _windows_candidates():
            if os.path.isfile(path):
                return path

    for name in _APP_WINDOW_EXE_NAMES:
        found = shutil.which(name)
        if found:
            return found

    return None


def app_window_profile_dir():
    """Hồ sơ trình duyệt RIÊNG của app.

    Không dùng chung hồ sơ của người dùng: tránh extension, lịch sử,
    hộp thoại "khôi phục tab" và mọi thứ có thể chen vào giao diện
    kiosk. Đặt trong thư mục tạm của hệ điều hành — mất cũng không sao,
    dữ liệu thật nằm hết trong app.db.
    """
    return os.path.join(tempfile.gettempdir(), "rbda-kiosk-ui-profile")


def build_app_window_command(browser, url, profile_dir, width, height):
    return [
        browser,
        f"--app={url}",
        f"--user-data-dir={profile_dir}",
        f"--window-size={width},{height}",
        # Bỏ mấy hộp thoại chào mừng/hỏi han của lần chạy đầu — kiosk
        # phải vào thẳng giao diện.
        "--no-first-run",
        "--no-default-browser-check",
        # Trang tiếng Việt hay bị Chrome/Edge mời "Dịch trang này?".
        "--disable-features=Translate,TranslateUI",
    ]


def open_ui(url, width, height):
    """Mở giao diện: ưu tiên CỬA SỔ RIÊNG, cùng lắm mới mở tab thường."""
    browser = find_app_window_browser()
    if browser:
        kwargs = {}
        if sys.platform.startswith("win"):
            kwargs["creationflags"] = _CREATE_NO_WINDOW
        try:
            subprocess.Popen(
                build_app_window_command(
                    browser, url, app_window_profile_dir(), width, height
                ),
                **kwargs,
            )
            return
        except OSError:
            # Trình duyệt tìm thấy nhưng không chạy được (thiếu quyền,
            # file hỏng). Vẫn còn đường mở tab thường.
            pass

    webbrowser.open(url)


def serve(api, resource_dir: str, start_page: str = "index.html",
          open_browser: bool = True, width: int = 1280,
          height: int = 800) -> str:
    """
    Khởi động máy chủ cục bộ và mở trình duyệt. Hàm này CHẶN (blocking)
    cho tới khi người dùng đóng tab (không còn ping) — giống webview.start().
    Trả về URL đã phục vụ (hữu ích khi test, với open_browser=False).
    """
    token = secrets.token_urlsafe(24)
    state = {"last_ping": None, "n_song": 0, "tung_song": False,
             "het_song_luc": None}
    khoa = threading.Lock()

    def on_ping():
        state["last_ping"] = time.time()

    def on_alive_open():
        with khoa:
            state["n_song"] += 1
            state["tung_song"] = True
            state["het_song_luc"] = None

    def on_alive_close():
        with khoa:
            state["n_song"] = max(0, state["n_song"] - 1)
            if state["n_song"] == 0:
                state["het_song_luc"] = time.time()

    def on_closed():
        # shutdown() phai chay o thread KHAC, khong the goi tu trong
        # chinh handler dang phuc vu request nay (se treo).
        threading.Thread(target=lambda: httpd.shutdown(), daemon=True).start()

    bound = type("_BoundHandler", (_Handler,), {
        "api": api,
        "token": token,
        "on_ping": staticmethod(on_ping),
        "on_closed": staticmethod(on_closed),
        "on_alive_open": staticmethod(on_alive_open),
        "on_alive_close": staticmethod(on_alive_close),
    })
    # SimpleHTTPRequestHandler dat self.directory TRONG __init__, nen gan
    # o cap lop se bi ghi de -> phai truyen qua tham so khoi tao.
    handler = functools.partial(bound, directory=resource_dir)

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.start_page = start_page

    url = f"http://127.0.0.1:{httpd.server_address[1]}/{start_page}?t={token}"

    def nen_tat(gio) -> bool:
        """Cửa sổ đã đóng thật chưa?

        Hai chế độ, tuỳ EventSource có dùng được hay không:

        - ĐÃ từng có kết nối sống: socket đứt là tín hiệu CHẮC CHẮN.
          Chỉ cần không còn kết nối nào VÀ ping cũng tắt trong
          _GRACE_SECONDS là đóng thật. Ngắn, vì không phải đoán.
        - CHƯA từng có kết nối nào (trình duyệt quá cũ, hoặc kết nối bị
          chặn): quay về cách cũ — chờ đủ _PING_TIMEOUT_SECONDS không
          ping. Dài, vì lúc này chỉ còn cách đoán.
        """
        last = state["last_ping"]
        if last is None:
            return False            # trang chưa kịp mở
        if state["tung_song"]:
            if state["n_song"] > 0:
                return False        # còn cửa sổ mở
            het = state["het_song_luc"]
            return (het is not None
                    and gio - het > _GRACE_SECONDS
                    and gio - last > _GRACE_SECONDS)
        return gio - last > _PING_TIMEOUT_SECONDS

    def watchdog():
        while True:
            time.sleep(5)
            with khoa:
                tat = nen_tat(time.time())
            if tat:
                threading.Thread(target=httpd.shutdown, daemon=True).start()
                return

    threading.Thread(target=watchdog, daemon=True).start()

    if open_browser:
        threading.Timer(0.3, lambda: open_ui(url, width, height)).start()
        httpd.serve_forever()
        httpd.server_close()
    else:
        # Phai dong luon socket lang nghe sau khi dung, khong thi cong van
        # con mo: ket noi moi van bat tay duoc nhung khong ai tra loi, ben
        # goi treo vo han thay vi nhan mot loi ro rang.
        def chay():
            httpd.serve_forever()
            httpd.server_close()

        threading.Thread(target=chay, daemon=True).start()

    return url
