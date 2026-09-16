#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dựng QUA_TRINH_LAP_TRINH.docx — quá trình lập trình phần mềm RB-DA.

Đọc NHAT_KY_AI.html và liệt kê **từng câu lệnh một** (118 câu), giữ phần kỹ thuật
và bỏ phần ranh giới sử dụng AI. Nhật ký gốc không bị đụng tới.

Chạy lại:  python3 tao_danh_sach_cau_lenh.py [NHAT_KY_AI.html] [QUA_TRINH_LAP_TRINH.docx]
"""

import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

import tao_nhat_ky_word as nk

TONG_CAU_LENH = 118

# Nhãn trường nói về việc DÙNG AI, không nói về phần mềm — tệp này bỏ hết.
KHOA_BO = (
    "ranh giới", "ai từ chối", "học sinh quyết", "phần việc của ai",
    "ghi chú cho báo cáo", "ghi chú bắt buộc", "một trích dẫn duy nhất",
    "một chỗ ai tự cảnh báo", "ai tự sửa một câu mình viết sai",
)


# Đoạn mở đầu bằng những cụm này là nói về ranh giới dùng AI, dù nằm trong
# một trường kỹ thuật — cũng bỏ.
DAU_DOAN_BO = (
    "ranh giới đã giữ", "ai không làm theo nghĩa đen", "ai không thu thập",
    "ai không viết phần kết luận", "ai không đưa tên nào",
)


def bo_truong(nhan):
    x = nhan.lower()
    return any(k in x for k in KHOA_BO)


def bo_doan(the):
    """Đoạn văn nói về ranh giới dùng AI, nhận ra bằng cụm mở đầu."""
    dau = nk.clean(the.get_text(" ", strip=True))[:70].lower()
    return any(dau.startswith(k) or f" {k}" in dau[:40] for k in DAU_DOAN_BO)


# ----------------------------------------------------------- đọc nhật ký
def so_cua_muc(article):
    seq = re.sub(r"\s+", "", article.find("span", class_="seq").get_text(" ", strip=True))
    nums = [int(x) for x in re.findall(r"\d+", seq)]
    return (list(range(nums[0], nums[-1] + 1)) if len(nums) > 1 else nums), seq


def tach_cau_lenh(txt, nums):
    """Tách một khối câu lệnh thành từng câu. Trả về [(số, chữ, ghi_chung)]."""
    n = len(nums)
    if n == 1:
        return [(nums[0], txt.strip("\n").rstrip(), False)]

    # (1) có sẵn dấu #NN — tách chuẩn, không phải đoán
    dau = re.findall(r"^#(\d+)[ \t]*(.*?)(?=^#\d+|\Z)", txt, re.M | re.S)
    if len(dau) == n and [int(a) for a, _ in dau] == nums:
        return [(int(a), b.strip("\n").rstrip(), False) for a, b in dau]

    khoi = [b.strip("\n") for b in re.split(r"\n[ \t]*\n", txt.strip()) if b.strip()]

    # (2) tách theo dòng trống
    if len(khoi) == n:
        return [(s, k.rstrip(), False) for s, k in zip(nums, khoi)]

    # (3) tách khối cuối theo dòng
    if khoi:
        dong = [d for d in khoi[-1].split("\n") if d.strip()]
        if len(khoi) - 1 + len(dong) == n:
            phan = khoi[:-1] + dong
            return [(s, k.rstrip(), False) for s, k in zip(nums, phan)]

    # không cách nào khớp — giữ nguyên khối, nói rõ là ghi chung
    return [(nums, txt.strip("\n").rstrip(), True)]


def doc_muc(article):
    nums, seq = so_cua_muc(article)
    gutter = article.find("div", class_="entry-gutter")
    khi = nk.clean(gutter.get_text(" ", strip=True).replace(
        article.find("span", class_="seq").get_text(" ", strip=True), "", 1)).strip()
    task = nk.clean(article.find("span", class_="task").get_text(" ", strip=True))

    cau_lenh, ky_thuat, thieu_nguyen_van = [], [], None
    for f in article.find_all("div", class_="field"):
        the_nhan = f.find("p", class_="field-label")
        nhan = nk.clean(the_nhan.get_text(strip=True)) if the_nhan else ""
        if nhan.lower().startswith("câu lệnh"):
            pre = f.find("pre")
            if pre is not None:
                cau_lenh = tach_cau_lenh(pre.get_text(), nums)
            else:  # #99 — không còn bản ghi nguyên văn
                p = next((x for x in f.find_all("p") if "field-label" not in (x.get("class") or [])), None)
                thieu_nguyen_van = p
                cau_lenh = [(nums[0] if len(nums) == 1 else nums, None, len(nums) > 1)]
            continue
        if the_nhan is None or bo_truong(nhan):
            continue
        ky_thuat.append((nhan, f))

    return dict(nums=nums, seq=seq, khi=khi, task=task, cau_lenh=cau_lenh,
                ky_thuat=ky_thuat, thieu=thieu_nguyen_van)


def tep_chinh(muc):
    for nhan, f in muc["ky_thuat"]:
        ul = f.find("ul", class_="files")
        if ul is not None:
            li = ul.find("li")
            if li is not None:
                t = nk.clean(li.get_text(" ", strip=True))
                return re.split(r"\s+[·(]| — ", t)[0].strip()
    return "—"


# -------------------------------------------------------------- dựng tệp
def nhan_so(phan):
    so, _, chung = phan
    return f"#{so[0]}–{so[-1]}" if chung else f"#{so}"


def mo_dau(doc, nguon):
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(4)
    nk.style_run(par.add_run("PHỤ LỤC KỸ THUẬT — QUÁ TRÌNH LẬP TRÌNH"),
                 bold=True, mono=True, size=9, color=nk.STAMP)

    h = doc.add_paragraph()
    h.paragraph_format.space_after = Pt(8)
    nk.style_run(h.add_run("Phần mềm RB-DA đã được lập trình ra sao"),
                 bold=True, size=22, color=nk.INK)

    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(6)
    nk.style_run(par.add_run(
        f"Danh sách đầy đủ {TONG_CAU_LENH} câu lệnh đã dùng để lập trình phần mềm, chép "
        "nguyên văn theo đúng thứ tự đã gõ, kèm việc đã làm được sau mỗi câu lệnh: mã "
        "nguồn viết ra, lỗi tìm được, cách kiểm chứng."), size=10.5, color=nk.INK_SOFT)

    t = doc.add_table(rows=2, cols=4)
    t.style = "Table Grid"
    o = [("Đề tài", "Phân bổ Câu lạc bộ (RB-DA)"),
         ("Nguồn", "NHAT_KY_AI.html"),
         ("Thời gian", "26/08 – 16/09/2026"),
         ("Số câu lệnh", f"{TONG_CAU_LENH} câu · 78 lượt làm việc")]
    for i, (dt, dd) in enumerate(o):
        top = t.cell(0, i)
        nk.shade_cell(top, nk.WASH_HEAD)
        p = top.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        nk.style_run(p.add_run(dt.upper()), mono=True, size=7.5, color=nk.INK_FAINT)
        p = t.cell(1, i).paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        nk.style_run(p.add_run(dd), bold=True, size=10)
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    khung = doc.add_table(rows=1, cols=1)
    cell = khung.cell(0, 0)
    nk.shade_cell(cell, nk.WASH_CAUTION)
    nk.cell_borders(cell)
    nk.cell_padding(cell)
    cell.paragraphs[0]._p.getparent().remove(cell.paragraphs[0]._p)
    p = cell.add_paragraph(); p.paragraph_format.space_after = Pt(4)
    nk.style_run(p.add_run("Phạm vi của tệp này"), bold=True, size=11, color=nk.CAUTION)
    p = cell.add_paragraph(); p.paragraph_format.space_after = Pt(4)
    nk.style_run(p.add_run(
        "Tệp này chỉ gồm câu lệnh và phần kỹ thuật. Phần đối chiếu với quy định sử dụng "
        "AI, các mốc AI từ chối, phần diễn giải số đo và danh sách việc học sinh tự thực "
        "hiện nằm ở Mục 1, 2, 4 và 7 của nhật ký gốc "), size=10)
    nk.style_run(p.add_run("NHAT_KY_AI.docx"), mono=True, size=9.5, color=nk.STAMP)
    nk.style_run(p.add_run(" — không chép lại ở đây."), size=10)
    p = cell.add_paragraph(); p.paragraph_format.space_after = Pt(0)
    nk.style_run(p.add_run(
        "Câu lệnh chép nguyên văn, giữ nguyên lỗi chính tả. Chỗ nào nhật ký không tách "
        "riêng được từng câu thì ghi rõ là ghi chung, không suy ra ranh giới."),
        italic=True, size=9.5, color=nk.INK_SOFT)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def bang_tra(doc, mucs):
    nk.add_heading(doc, f"PHẦN B — Danh sách {TONG_CAU_LENH} câu lệnh", 1)
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(8)
    nk.style_run(par.add_run(
        "Mỗi câu lệnh một dòng, đánh số liên tục. Bản đầy đủ của từng câu lệnh và việc đã "
        "làm được nằm ở Phần C, theo đúng số thứ tự này."), size=10, color=nk.INK_SOFT)

    rong = [Cm(1.5), Cm(1.9), Cm(9.3), Cm(4.3)]
    t = doc.add_table(rows=0, cols=4)
    t.style = "Table Grid"
    t.autofit = False
    dau = t.add_row().cells
    for cell, chu, w in zip(dau, ["STT", "NGÀY", "CÂU LỆNH (NGUYÊN VĂN)", "TỆP CHÍNH"], rong):
        cell.width = w
        nk.shade_cell(cell, nk.WASH_HEAD)
        nk.cell_padding(cell)
        p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        nk.style_run(p.add_run(chu), bold=True, mono=True, size=8, color=nk.INK_SOFT)

    da_ra = []
    for m in mucs:
        ngay = m["khi"].split("~")[0].strip()
        tep = tep_chinh(m)
        for phan in m["cau_lenh"]:
            so, chu, chung = phan
            for so_don in (so if chung else [so]):
                cells = t.add_row().cells
                for cell, w in zip(cells, rong):
                    cell.width = w
                    nk.cell_padding(cell, top=40, bottom=40)
                    cell.paragraphs[0].paragraph_format.space_after = Pt(0)
                nk.style_run(cells[0].paragraphs[0].add_run(f"#{so_don}"),
                             bold=True, mono=True, size=8.5, color=nk.STAMP)
                nk.style_run(cells[1].paragraphs[0].add_run(ngay), mono=True, size=8,
                             color=nk.INK_SOFT)

                p = cells[2].paragraphs[0]
                if chu is None:
                    nk.style_run(p.add_run("Không còn bản ghi nguyên văn — xem 7 mã commit ở Phần C"),
                                 italic=True, size=9, color=nk.CAUTION)
                else:
                    gon = nk.clean(chu)
                    if len(gon) > 190:
                        gon = gon[:190].rstrip() + "…"
                    nk.style_run(p.add_run(gon), mono=True, size=8.5)
                    if chung:
                        p2 = cells[2].add_paragraph(); p2.paragraph_format.space_after = Pt(0)
                        nk.style_run(p2.add_run(
                            f"(ghi chung cho {nhan_so(phan)} — nhật ký không tách riêng từng câu)"),
                            italic=True, size=8, color=nk.CAUTION)
                nk.style_run(cells[3].paragraphs[0].add_run(tep), mono=True, size=8,
                             color=nk.INK_SOFT)
                da_ra.append(so_don)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return da_ra


def chi_tiet(doc, mucs):
    doc.add_page_break()
    nk.add_heading(doc, "PHẦN C — Từng câu lệnh và việc đã làm được", 1)
    par = doc.add_paragraph()
    par.paragraph_format.space_after = Pt(8)
    nk.style_run(par.add_run(
        "Theo trình tự thời gian. Câu lệnh in trong khối nền xanh, mang đúng số của nó; "
        "bên dưới là phần kỹ thuật của lượt làm việc đó."), size=10, color=nk.INK_SOFT)

    ngay_cu = None
    for m in mucs:
        ngay = m["khi"].split("~")[0].strip()
        if ngay and ngay != ngay_cu:
            nk.add_heading(doc, f"Ngày {ngay}", 2)
            ngay_cu = ngay

        head = doc.add_paragraph()
        head.paragraph_format.space_before = Pt(12)
        head.paragraph_format.space_after = Pt(3)
        nhan = (f"#{m['nums'][0]}–{m['nums'][-1]}" if len(m["nums"]) > 1 else f"#{m['nums'][0]}")
        nk.style_run(head.add_run(nhan), bold=True, mono=True, size=12, color=nk.STAMP)
        nk.style_run(head.add_run(f"   ·   {m['khi']}   ·   " if m["khi"] else "   ·   "),
                     mono=True, size=8.5, color=nk.INK_FAINT)
        nk.style_run(head.add_run(m["task"]), bold=True, size=11.5, color=nk.INK)
        nk.par_border(head, ("bottom",), size=6, color="1A1D21")
        nk.keep_with_next(head)

        for phan in m["cau_lenh"]:
            so, chu, chung = phan
            lab = doc.add_paragraph()
            lab.paragraph_format.space_before = Pt(6)
            lab.paragraph_format.space_after = Pt(2)
            nk.style_run(lab.add_run(f"CÂU LỆNH {nhan_so(phan)}"),
                         bold=True, mono=True, size=8, color=nk.STAMP)
            if chung:
                nk.style_run(lab.add_run("   — ghi chung, nhật ký không tách riêng từng câu"),
                             italic=True, size=8, color=nk.CAUTION)
            nk.keep_with_next(lab)
            if chu is None:
                nk.add_text_par(doc, m["thieu"], size=10.5)
            else:
                nk.add_mono_block(doc, chu)

        for nhan_tr, f in m["ky_thuat"]:
            nk.add_label(doc, nhan_tr)
            for child in f.children:
                if not isinstance(child, Tag):
                    continue
                cls = child.get("class") or []
                if "field-label" in cls:
                    continue
                if child.name == "pre":
                    nk.add_mono_block(doc, child.get_text().rstrip("\n"))
                elif child.name == "p":
                    if bo_doan(child):
                        continue
                    nk.add_text_par(doc, child, size=10.5)
                elif child.name == "ul":
                    mono = "files" in cls
                    for li in child.find_all("li", recursive=False):
                        p = doc.add_paragraph()
                        p.paragraph_format.left_indent = Cm(0.6)
                        p.paragraph_format.space_after = Pt(1)
                        nk.style_run(p.add_run("→ " if mono else "• "),
                                     mono=mono, size=9.5, color=nk.STAMP)
                        nk.add_inline(p, li, mono=mono, size=9.5 if mono else 10.5)
                elif child.name == "table":
                    nk.render_table(doc, child)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)


def build(src: Path, dst: Path):
    soup = BeautifulSoup(src.read_text(encoding="utf-8"), "html.parser")
    sheet = soup.find("div", class_="sheet")
    mucs = [doc_muc(a) for a in sheet.find_all("article", class_="entry")]

    doc = Document()
    sec = doc.sections[0]
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    normal = doc.styles["Normal"]
    normal.font.name = nk.F_BODY
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), nk.F_BODY)
    normal.paragraph_format.space_after = Pt(5)
    chan = sec.footer.paragraphs[0]
    chan.alignment = WD_ALIGN_PARAGRAPH.CENTER
    nk.add_page_field(chan)

    mo_dau(doc, src.name)

    # Phần A — kiến trúc và tiến độ, đọc thẳng hai sơ đồ + biểu đồ của Mục 3
    nk.add_heading(doc, "PHẦN A — Kiến trúc phần mềm và tiến độ", 1)
    for fig in sheet.find_all("figure", class_="so-do"):
        nk.render_so_do(doc, fig)
    for fig in sheet.find_all("figure", class_="tien-do"):
        nk.render_tien_do(doc, fig)

    da_ra = bang_tra(doc, mucs)
    chi_tiet(doc, mucs)

    # Phụ lục — bảng tệp và bảng commit của Mục 6
    bang = [w.find("table") for w in sheet.find_all("div", class_="table-wrap")]
    bang = [b for b in bang if b is not None]
    phu_luc = [b for b in bang
               if b.find("th") and "tệp" in nk.clean(b.find("th").get_text(strip=True)).lower()]
    commit = [b for b in bang
              if b.find("th") and "ngày" in nk.clean(b.find("th").get_text(strip=True)).lower()]
    def ghi_chu(chu):
        par = doc.add_paragraph()
        par.paragraph_format.space_after = Pt(8)
        nk.style_run(par.add_run(chu), size=9.5, color=nk.INK_SOFT, italic=True)

    if phu_luc:
        doc.add_page_break()
        nk.add_heading(doc, "PHỤ LỤC 1 — Tệp do AI viết mới", 1)
        ghi_chu("Bảng liệt kê từng tệp kèm số dòng và chức năng. Tổng theo nhật ký là 131 "
                "tệp — lớn hơn số dòng bảng, vì vài dòng gộp cả một thư mục (ví dụ “kèm 5 tệp "
                "CSV mẫu”). Đối chiếu đầy đủ ở Mục 6 của NHAT_KY_AI.docx.")
        nk.render_table(doc, phu_luc[0])
    if commit:
        doc.add_page_break()
        nk.add_heading(doc, "PHỤ LỤC 2 — Mã commit đối chiếu", 1)
        ghi_chu("Mỗi dòng là một commit có mặt trong nhật ký, kèm ngày giờ và nội dung thay "
                "đổi. Tổng theo nhật ký là 95 commit tính tới 15/09; từ 12/09 dự án nằm ở kho "
                "rbda-kiosk, commit trước đó tra ở kho cũ.")
        nk.render_table(doc, commit[0])

    nk.normalize_cells(doc)
    props = doc.core_properties
    props.title = "Phần mềm RB-DA đã được lập trình ra sao"
    props.subject = f"Phụ lục kỹ thuật — {TONG_CAU_LENH} câu lệnh, chép nguyên văn"
    props.comments = "Sinh tự động từ NHAT_KY_AI.html bằng tao_danh_sach_cau_lenh.py"
    doc.save(dst)

    # Cổng chặn: phải đủ 1..118, không thiếu, không lặp
    thuc = sorted(da_ra)
    can = list(range(1, TONG_CAU_LENH + 1))
    if thuc != can:
        thieu = sorted(set(can) - set(thuc))
        lap = sorted({x for x in thuc if thuc.count(x) > 1})
        raise ValueError(f"danh sách câu lệnh sai: thiếu {thieu} · lặp {lap}")
    return len(mucs), len(thuc)


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "NHAT_KY_AI.html"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else here / "QUA_TRINH_LAP_TRINH.docx"
    n_muc, n_cl = build(src, dst)
    print(f"Đã ghi {dst} — {n_cl} câu lệnh trong {n_muc} lượt làm việc.")
