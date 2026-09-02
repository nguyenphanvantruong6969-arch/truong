# Phần mềm này chạy cơ chế gì

> **Đây là bản mô tả PHẦN MỀM, không phải phần cơ sở lý thuyết của bài nghiên
> cứu.** Tệp này ghi *phần mềm làm gì* và *chỗ nào trong mã kiểm chứng được*.
> Phần diễn giải ý nghĩa khoa học, phần Kết luận, phần Tính mới — học sinh tự
> viết (Phụ lục 1).

Số dòng đối chiếu với `rbda_priority_pipeline.py` tại commit hiện tại. Kiểm lại
bằng:

```bash
grep -n "^def " rbda_priority_pipeline.py
```

---

## ⚠️ Báo cáo và phần mềm đang lệch

Quét cả hai bản báo cáo `.docx`:

| Từ khoá | Số lần xuất hiện trong báo cáo |
|---|---|
| "dự trữ" | **0** |
| "bốc thăm" / "ngẫu nhiên" | **0** |
| "Reserve" / "RB-DA" | **0** |

Báo cáo mô tả **Gale–Shapley nhiều-một thuần tuý**: mỗi CLB có *"một danh sách
ưu tiên học sinh (Q_j)"* và một sức chứa. Phần mềm làm nhiều hơn thế — ba lớp
dưới đây không có mặt trong báo cáo.

**Hệ quả hai chiều:** không viết ra thì không được điểm cho phần khó nhất của
phần mềm, mà vẫn mang rủi ro nếu giám khảo mở mã nguồn ra.

---

## Năm lớp cơ chế

| # | Lớp | Hàm · dòng |
|---|---|---|
| 1 | Deferred Acceptance, học sinh đề xuất | `run_rbda` · **207** |
| 2 | Dự trữ mềm + thứ tự xét | `club_choice_function` · **136** |
| 3 | Single Tie-Breaking (STB) | `generate_stb_lottery` · **441** |
| 4 | Ưu tiên hai tầng thi / không thi | `compute_club_priority` · **48** |
| 5 | Kiểm chứng ổn định bằng chính hàm lựa chọn | `verify_stability` · **322** |

Lớp 1 là phần báo cáo đã mô tả. Lớp 2, 3, 4 là phần chưa có. Lớp 5 là hệ quả
kỹ thuật bắt buộc của lớp 2.

---

### Lớp 1 — Deferred Acceptance, học sinh đề xuất

`run_rbda` · dòng **207**

Học sinh lần lượt đề xuất vào CLB theo thứ tự nguyện vọng. CLB **giữ tạm** những
em tốt nhất trong số đang có mặt và từ chối phần còn lại. Em bị từ chối đề xuất
tiếp nguyện vọng sau. Hết đề xuất thì dừng.

Chữ *"trì hoãn"* nằm ở chỗ **giữ tạm**: CLB không chốt ai cho tới vòng cuối, nên
một em giỏi xuất hiện muộn vẫn đẩy được em kém hơn ra.

**Vì sao dự án cần:** đây là lớp thay thế cách xét theo thứ tự đăng ký.

---

### Lớp 2 — Dự trữ mềm, xét hai lượt

`club_choice_function` · dòng **136**

Mỗi CLB có thể để riêng một số suất (`reserve_capacity`) cho một nhóm học sinh
(`reserve_group`). Khi xét, CLB chạy **hai lượt**:

1. **Lượt dự trữ** — chỉ xét em thuộc diện, lấy tối đa bằng số suất dự trữ.
2. **Lượt chung** — xét toàn bộ số còn lại (kể cả em thuộc diện chưa được suất
   dự trữ), lấp nốt sức chứa.

**"Mềm" nghĩa là gì:** suất dự trữ **không khoá cứng**. Không đủ em thuộc diện
thì phần thừa **tự chuyển sang lượt chung** — CLB vẫn tuyển đủ. Có test canh
điều này (`test_suat_du_tru_thua_tu_chuyen_sang_luot_chung`).

**Một chi tiết quan trọng trong mã** (ghi chú dòng **120–134**): việc phân nhóm
dự trữ/chung phải **tính lại ở mỗi vòng**, theo đúng tập em đang có mặt lúc đó.
Bản đầu tiên gộp thành một thứ tự tổng thể tính một lần — **sai**, và đã sửa sau
khi đối chiếu với bản tham chiếu.

**Vì sao dự án cần:** để CLB giữ được chỗ cho nhóm mình hướng tới, mà không phải
loại bỏ cơ chế xét chung.

---

### Lớp 3 — Single Tie-Breaking (STB)

`generate_stb_lottery` · dòng **441**

Mỗi học sinh nhận **một** số bốc thăm, **dùng chung cho mọi CLB**. Đó là nghĩa
của *"single"* — trái với việc mỗi CLB bốc một bộ số riêng.

**Ba tính chất đã đo, không phải khẳng định suông:**

- Cùng dữ liệu, cùng seed → cùng kết quả, **kể cả khi đổi thứ tự nhập liệu**
  (`sorted()` trước khi xáo — dòng 460).
- Mã học sinh **không** kéo thứ hạng: tương quan giữa mã và số bốc thăm **đổi
  dấu** qua 8 khối seed → là nhiễu. Xem `GIAI_DAP_BOC_THAM`.
- Đổi seed thì **1,1%** số em đổi kết cục có suất / không suất, và **0 cặp phá
  vỡ ở mọi seed** trong 600 lần chạy.

> **KHÔNG viết:** *"số bốc thăm dựa trên mã học sinh"* — sai, và nghe như em tên
> A có lợi hơn em tên Z. Viết đúng: *"bốc thăm không phụ thuộc thứ tự nhập liệu"*.

**Vì sao dự án cần:** ở tầng không thi tuyển, nhiều em ngang nhau hoàn toàn. Phải
có cách phá hoà, và cách đó phải tái lập được để kiểm toán.

---

### Lớp 4 — Ưu tiên hai tầng: đã thi / không thi

`compute_club_priority` · dòng **48**

| Tầng | Gồm ai | Xếp theo |
|---|---|---|
| **Tầng 1** | Em **đã được chấm điểm** cho CLB đó | Điểm giảm dần; **hoà điểm mới tới** số bốc thăm |
| **Tầng 2** | Em có đăng ký nhưng **không thi** CLB đó | **Thuần** số bốc thăm |

**Tầng 1 luôn đứng trọn trước Tầng 2** — không xen kẽ.

**Một ràng buộc cứng ghi ngay trong mã** (dòng 63–72): hàm này **không được**
nhận bất kỳ tham số nào liên quan tới **thứ hạng nguyện vọng** của học sinh. Nếu
CLB biết em xếp mình là nguyện vọng mấy rồi ưu tiên theo đó, tính *khai thật có
lợi nhất* của thuật toán bị phá.

**Vì sao dự án cần — đây là lớp sinh ra từ hoàn cảnh trường:** có CLB tổ chức
thi tuyển, có CLB không. Một bài toán ghép cặp chuẩn không có chỗ cho tình huống
hai loại CLB cùng tồn tại trong một đợt phân bổ.

---

### Lớp 5 — Kiểm chứng ổn định bằng chính hàm lựa chọn

`verify_stability` · dòng **322**

Cách thường: so kết quả với một bảng ưu tiên tĩnh. **Không dùng được ở đây** —
xem phần dưới.

Cách phần mềm làm: với mỗi cặp (học sinh `s`, câu lạc bộ `c`) mà `s` thích `c`
hơn chỗ hiện tại — **thêm `s` vào tập `c` đang giữ, rồi chạy lại hàm lựa chọn
của `c`**. Nếu `s` nằm trong tập được chọn thì đó là một **cặp phá vỡ**.

**Vì sao dự án cần:** đây là định nghĩa tổng quát, đúng cả khi hàm lựa chọn
không phải một thứ tự tuyến tính. Cách cũ dùng bảng tĩnh **đã bị phát hiện sai**
khi đối chiếu với bản tham chiếu.

---

## Chỗ mô hình trong báo cáo không mô tả được phần mềm

Báo cáo viết mỗi CLB có **một danh sách ưu tiên `Q_j`**. Hàm lựa chọn thật
**không phải** một thứ tự tuyến tính. Chạy lại để tự xem:

```bash
python du_lieu_test/do_hai_canh_du_tru.py
```

> CLB sức chứa **3**, trong đó **1 suất dự trữ**.
> Ưu tiên: **A > B > C > D**. D thuộc diện dự trữ.
> Ưu tiên **giữ nguyên** ở cả hai cảnh; chỉ đổi *ai đang có mặt*.

| | Mô hình *một danh sách Q_j* | `club_choice_function` thật | |
|---|---|---|---|
| **Cảnh 1** — D có mặt | A, B, C | **D, A, B** | **LỆCH** |
| **Cảnh 2** — D vắng mặt | A, B, C | A, B, C | khớp |

**Đọc ra hai điều:**

1. Cảnh 1: **C xếp trên D, CLB lấy 3 em — mà D đỗ còn C trượt.** Theo mô hình
   một danh sách thì chuyện đó không xảy ra được.
2. So hai cảnh: **cùng em C, cùng thứ hạng, cùng CLB, cùng sức chứa** — lúc có
   suất lúc không. Cái đổi duy nhất là D có mặt hay không.

Nghĩa là: kết cục của C **không chỉ** phụ thuộc thứ hạng của C, mà còn phụ thuộc
**ai khác đang nộp cùng lúc**. Không viết ra được một `Q_j` cố định rồi đọc ra
kết quả.

**Đây không phải lỗi.** Đó là điều suất dự trữ sinh ra, và là lý do Lớp 5 phải
kiểm cặp phá vỡ bằng chính hàm lựa chọn.

Bảng này có test canh: `tests/test_hai_canh_du_tru.py` (11 test). Gỡ cơ chế dự
trữ ra thì **5 test đỏ** — đã thử.

---

## Bảng đối chiếu báo cáo ↔ phần mềm

| Phần mềm chạy | Báo cáo đã mô tả? |
|---|---|
| Deferred Acceptance học sinh đề xuất | ✅ có |
| Ghép cặp nhiều-một, có sức chứa | ✅ có |
| Kiểm tra cặp phá vỡ | ✅ có (nhưng theo định nghĩa bảng tĩnh) |
| **Dự trữ mềm, xét hai lượt** | ❌ **chưa có** |
| **Bốc thăm STB dùng chung mọi CLB** | ❌ **chưa có** |
| **Ưu tiên hai tầng thi / không thi** | ❌ **chưa có** |
| **Hàm lựa chọn không phải thứ tự tuyến tính** | ❌ **mâu thuẫn** — báo cáo viết `Q_j` là một danh sách |

---

## Một lưu ý về trích dẫn

Cả dự án chỉ có **đúng một** tên tài liệu được nêu: **Kominers & Sonmez 2016**,
ở `rbda_priority_pipeline.py` dòng 6 và 145 — cho phần dự trữ mềm.

Dòng đó **do chính học sinh viết**, có trong commit đầu tiên `57f2e82` (26/08),
trước khi AI chỉnh sửa tệp.

AI **không** tìm thêm trích dẫn, **không** lập danh mục tài liệu tham khảo và
**không** đánh giá tính mới — Phụ lục 1 cấm. Việc khảo sát tài liệu là của học
sinh.

---

*Tệp này do AI viết, mô tả phần mềm do AI tham gia lập trình. Nó không chứa
nhận định về ý nghĩa khoa học của kết quả — phần đó học sinh tự viết.*
