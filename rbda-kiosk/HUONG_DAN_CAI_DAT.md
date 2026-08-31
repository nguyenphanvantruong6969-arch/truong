# Hướng dẫn cài đặt trên máy Windows

## Vì sao Windows báo "không có chữ ký số hợp lệ"?

Khi chạy `PhanBoCauLacBo.exe` lần đầu, Windows hiện một trong hai màn hình:

> **Windows protected your PC**
> Microsoft Defender SmartScreen prevented an unrecognised app from starting.

hoặc

> **Nhà phát hành không xác định** — bạn có muốn chạy tệp này không?

**Đây không phải lỗi phần mềm, và không phải virus.** Windows cảnh báo như vậy với
**mọi** ứng dụng không mua chữ ký số thương mại — kể cả phần mềm hoàn toàn lành.

Muốn hết cảnh báo trên **mọi máy**, phải mua chứng chỉ ký mã từ một tổ chức cấp
chứng chỉ. Giá khoảng **200–1000 USD mỗi năm**, cần giấy tờ pháp nhân và mất
1–14 ngày xác minh. Với một đề tài nghiên cứu của học sinh thì điều đó nằm ngoài
tầm — nên tài liệu này chỉ ra hai đường đi được.

---

## Cách 1 — Bấm qua cảnh báo (30 giây, không cần quyền gì)

**Đây là cách mặc định, luôn dùng được, và không thiếu tính năng nào.**

1. Chạy `PhanBoCauLacBo.exe`
2. Màn hình xanh hiện ra → bấm **More info** (tiếng Việt: *Thông tin thêm*)
3. Nút **Run anyway** (*Vẫn chạy*) hiện ra ở góc dưới → bấm vào

Xong. **Windows nhớ lựa chọn này** — những lần sau chạy thẳng, không hỏi lại.

> Nếu không thấy nút *Run anyway*: bấm chuột phải vào file `.exe` → **Properties**
> → ở cuối tab *General*, nếu có ô **Unblock** thì tích vào → **OK**. Rồi chạy lại.

---

## Nếu app mở ra trong cửa sổ Edge thay vì cửa sổ riêng

Nhìn **góc dưới bên trái** app: nếu dòng cuối ghi **“Chế độ dự phòng (trình duyệt)”**
màu vàng, nghĩa là cửa sổ gốc không mở được và app đang mượn Edge để vẽ.

Nguyên nhân nhiều khả năng nhất: Windows gắn dấu **“tải từ Internet”** vào mọi tệp
giải nén từ tệp `.zip` tải về, và .NET Framework từ chối nạp thư viện mang dấu đó.

**Cách xử lý — 20 giây, không cần quyền gì:**

1. Chuột phải vào tệp **`.zip`** *(làm trước khi giải nén)* → **Properties**
2. Cuối tab *General*, nếu có ô **Unblock** thì tích vào → **OK**
3. Giải nén lại vào một thư mục **mới**, rồi chạy

Đã lỡ giải nén rồi thì mở PowerShell tại thư mục đó và gõ:

```powershell
Get-ChildItem -Recurse | Unblock-File
```

Bản mới cũng **tự gỡ dấu** lúc khởi động và kèm sẵn tệp cấu hình bảo .NET bỏ qua
dấu đó, nên phần lớn trường hợp không phải làm gì. Ba bước trên là để dành cho khi
hai lớp đó không ăn.

**Nếu vẫn ở chế độ dự phòng:** mở tệp **`loi_khoi_dong.txt`** nằm cạnh
`PhanBoCauLacBo.exe` — trong đó có nguyên văn lý do. Gửi lại nội dung tệp đó.

> Chạy ở chế độ dự phòng **không thiếu tính năng nào** — mọi thứ hoạt động y hệt.
> Khác biệt duy nhất là máy phải có sẵn Edge hoặc Chrome.

---

## Cách 2 — Ký bằng chứng chỉ tự tạo (cần quyền Administrator)

Cách này làm cảnh báo **biến mất hoàn toàn** trên máy đã làm. Phù hợp khi máy kiosk
đặt cố định ở trường và bạn muốn giáo viên khác dùng mà không thấy cảnh báo nào.

**Cần:** quyền Administrator trên máy đó, và bộ Windows SDK (script sẽ báo nếu thiếu).

1. Chép `ky_va_tin_cay.ps1` vào **cùng thư mục** với `PhanBoCauLacBo.exe`
2. Bấm chuột phải nút **Start** → **Windows PowerShell (Admin)** hoặc **Terminal (Admin)**
3. Gõ lần lượt:

```powershell
cd "C:\đường\dẫn\tới\thư\mục\vừa\giải\nén"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\ky_va_tin_cay.ps1
```

Script chạy 7 bước, mỗi bước in ra `OK` hoặc `LOI` kèm cách xử lý. Nó tạo chứng chỉ
tự ký, cài vào kho tin cậy của máy, rồi ký file `.exe`.

**Chạy lại nhiều lần không sao** — script tìm chứng chỉ cũ trước, chỉ tạo mới khi
chưa có. Các bản build sau cũng dùng lại đúng chứng chỉ đó, không phải cài lại.

### Giới hạn phải biết

Chứng chỉ tự ký **chỉ được tin trên máy đã cài nó**. Mang file `.exe` sang máy khác
thì máy đó vẫn cảnh báo như thường — đó là bản chất của chứng chỉ tự ký, không phải
lỗi. Trên máy mới: chạy lại script, hoặc dùng Cách 1.

---

## Nên chọn cách nào?

| Tình huống | Cách nên dùng |
|---|---|
| Thử nhanh trên máy cá nhân | **Cách 1** — 30 giây là xong |
| Demo trước giám khảo | **Cách 1** — bấm qua từ trước, lúc demo app mở thẳng |
| Máy kiosk đặt cố định ở trường, nhiều người dùng | **Cách 2** — làm một lần, không ai còn thấy cảnh báo |
| Không có quyền Administrator | **Cách 1** — Cách 2 không chạy được |

---

## Nếu app vẫn không mở được sau khi bấm qua cảnh báo

Cảnh báo chữ ký và lỗi khởi động là **hai chuyện khác nhau**. Nếu bấm *Run anyway*
rồi mà app vẫn không lên, hãy chụp **nguyên văn** thông báo lỗi — đừng gõ lại theo
trí nhớ, vì từng chữ trong đó đều có ích cho việc chẩn đoán.

Ứng dụng có sẵn một đường dự phòng: nếu cửa sổ gốc không mở được, nó tự chuyển sang
mở bằng trình duyệt nhân Chromium (Edge có sẵn trên mọi máy Windows 10/11) ở chế độ
cửa sổ riêng — không thanh địa chỉ, không thanh tab. Toàn bộ tính năng giữ nguyên.

---

## Ghi chú cho phần trình bày đề tài

Nếu cần nhắc tới điều này trong báo cáo, các dữ kiện là:

- Chữ ký số **không** liên quan tới tính đúng đắn của thuật toán phân bổ. Nó chỉ là
  cơ chế để Windows xác minh **ai** phát hành phần mềm, không phải phần mềm **làm gì**.
- Chứng chỉ ký mã loại OV giá khoảng 200–400 USD/năm; ngay cả khi mua, Microsoft
  SmartScreen **vẫn cảnh báo** cho tới khi phần mềm tích luỹ đủ lượt tải. Chỉ chứng
  chỉ loại EV (400–1000 USD/năm, kèm thiết bị USB) mới bỏ qua cảnh báo ngay lập tức.
- Vì vậy với phần mềm nội bộ dùng trong một trường, cách xử lý thông thường trong
  ngành đúng là hai cách nêu trên, chứ không phải mua chứng chỉ.

*Phần nhận xét và đánh giá ý nghĩa của lựa chọn này, học sinh tự viết.*
