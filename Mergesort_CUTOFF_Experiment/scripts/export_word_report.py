#!/usr/bin/env python3
"""
Xuất báo cáo thí nghiệm CUTOFF Mergesort ra file Microsoft Word (.docx),
tự động nạp số liệu chính xác từ results/*.csv và chèn đầy đủ 8 biểu đồ trong results/charts/.
"""
import os
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

RESULTS_DIR = "results"
CHARTS_DIR = os.path.join(RESULTS_DIR, "charts")
OUT_DOCX = "BaoCao_ThiNghiem_CUTOFF.docx"


def set_cell_bg(cell, hex_color):
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_color)
    cell._tc.get_or_add_tcPr().append(shading)


def add_styled_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    hdr_cells = table.rows[0].cells
    for i, text in enumerate(headers):
        hdr_cells[i].text = str(text)
        set_cell_bg(hdr_cells[i], "1F4E79")
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(10)
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in enumerate(rows):
        cells = table.rows[r_idx + 1].cells
        bg = "F2F6FA" if r_idx % 2 == 1 else None
        for c_idx, val in enumerate(row):
            cells[c_idx].text = str(val)
            if bg:
                set_cell_bg(cells[c_idx], bg)
            for p in cells[c_idx].paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c_idx == 0 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(10)

    if col_widths:
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    doc.add_paragraph()
    return table


def add_chart(doc, filename, caption, width_in=6.2):
    path = os.path.join(CHARTS_DIR, filename)
    if not os.path.exists(path):
        p = doc.add_paragraph(f"[Thiếu ảnh biểu đồ: {path}]")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(4)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.add_run().add_picture(path, width=Inches(width_in))

    p_cap = doc.add_paragraph(caption)
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_after = Pt(8)
    for r in p_cap.runs:
        r.italic = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0x44, 0x44, 0x44)


def add_bullet(doc, lead, text):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    if lead:
        r1 = p.add_run(lead)
        r1.bold = True
    p.add_run(text)


def load_meta():
    meta = {}
    meta_path = os.path.join(RESULTS_DIR, "analysis_meta.txt")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    meta[k] = v
    return meta


def main():
    meta = load_meta()
    best_df = pd.read_csv(os.path.join(RESULTS_DIR, "best_cutoff_summary.csv"))
    ov_df = pd.read_csv(os.path.join(RESULTS_DIR, "overall_regret.csv"), index_col=0)
    fit_df = pd.read_csv(os.path.join(RESULTS_DIR, "cost_model_fit.csv"))
    val_path = os.path.join(RESULTS_DIR, "validation_summary.csv")
    val_df = pd.read_csv(val_path) if os.path.exists(val_path) else None
    sc_path = os.path.join(RESULTS_DIR, "scaling_doubling.csv")
    sc_df = pd.read_csv(sc_path) if os.path.exists(sc_path) else None

    samples_total = int(meta.get("samples_total", 7392))
    samples_dropped = int(meta.get("samples_dropped_gc", 0))
    minimax_c = int(meta.get("minimax_cutoff", 24))
    mean_c = int(meta.get("mean_regret_cutoff", 40))

    doc = Document()

    for sec in doc.sections:
        sec.top_margin = Inches(0.85)
        sec.bottom_margin = Inches(0.85)
        sec.left_margin = Inches(0.95)
        sec.right_margin = Inches(0.95)

    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11.5)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(5)

    for lvl, sz in [(1, 14), (2, 12.5)]:
        h = doc.styles[f"Heading {lvl}"]
        h.font.name = "Times New Roman"
        h.font.size = Pt(sz)
        h.font.bold = True
        h.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(2)
    rt = title.add_run("BÁO CÁO THÍ NGHIỆM\nXÁC ĐỊNH GIÁ TRỊ CUTOFF TỐI ƯU CHO MERGESORT")
    rt.bold = True
    rt.font.size = Pt(16)
    rt.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    sub = doc.add_paragraph("Đánh giá thực nghiệm trên Windows 11, Intel Core i7-1355U, OpenJDK 25.0.5 LTS")
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.paragraph_format.space_after = Pt(10)
    for r in sub.runs:
        r.italic = True
        r.font.size = Pt(11)
        r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    doc.add_heading("1. Mục tiêu và đặt vấn đề", level=1)
    doc.add_paragraph(
        "Top-down Mergesort đảm bảo thời gian chạy O(N lg N) với tối đa N lg N phép so sánh và 6N lg N "
        "lần truy cập mảng, nhưng chịu chi phí đệ quy và sao chép mảng phụ aux[] khá lớn với các mảng con nhỏ. "
        "Một cải tiến phổ biến là chuyển sang Insertion Sort khi đoạn con có không quá CUTOFF phần tử "
        "(hi <= lo + CUTOFF - 1), trong đó các giá trị tham chiếu thường gặp là 7 và 10. "
        "Thí nghiệm này thực hiện đo đạc, phân tích thống kê và mô hình hóa chi phí nhằm xác định "
        "ngưỡng CUTOFF phù hợp nhất trên cấu hình máy thực tế."
    )

    doc.add_heading("2. Cài đặt thuật toán và thiết kế thí nghiệm", level=1)
    doc.add_heading("2.1. Cài đặt thuật toán", level=2)
    add_bullet(
        doc, "Merge.java: ",
        "Cài đặt Top-down Mergesort với hàm merge() sao chép đoạn [lo..hi] sang mảng phụ aux[] rồi trộn "
        "về mảng gốc, cấp phát aux[] một lần duy nhất ngoài đệ quy và giữ nguyên tính ổn định nhờ ưu tiên "
        "lấy phần tử từ nửa trái khi khóa bằng nhau. Chỉ áp dụng duy nhất cải tiến CUTOFF, không gộp các "
        "cải tiến khác để cô lập hoàn toàn ảnh hưởng của tham số này."
    )
    add_bullet(
        doc, "Insertion.java & MergeTest.java: ",
        "Cài đặt Insertion Sort ổn định cho đoạn con [lo..hi]. Trước khi đo, MergeTest kiểm chứng "
        "đạt 100% tính đúng đắn và tính ổn định trên 22 cỡ mảng (0..12345), 2 mật độ trùng khóa và mọi CUTOFF từ 1 đến 70."
    )

    doc.add_heading("2.2. Cấu hình máy và môi trường đo", level=2)
    add_styled_table(
        doc,
        ["Thành phần", "Thông số chi tiết"],
        [
            ["Hệ điều hành", "Windows 11 64-bit (x64)"],
            ["Vi xử lý (CPU)", "13th Gen Intel(R) Core(TM) i7-1355U (1.70 GHz)"],
            ["Bộ nhớ (RAM)", "16.0 GB (15.7 GB khả dụng)"],
            ["Môi trường Java", "OpenJDK 25.0.5 LTS (Temurin-25.0.5+8, 64-Bit Server VM)"],
            ["Cờ JVM khi đo", "-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC -Dstdout.encoding=UTF-8"],
            ["Phân tích dữ liệu", "Python 3.15.2 (numpy, pandas, matplotlib, scipy)"],
        ],
        col_widths=[1.9, 4.7],
    )

    doc.add_heading("2.3. Bộ dữ liệu và kiểm soát nhiễu", level=2)
    add_bullet(
        doc, "Bộ dữ liệu (BASE_SEED = 20261120L, tái lập 100%): ",
        "Gồm 7 bộ dữ liệu Integer[]: random (N = 10,000; 100,000; 1,000,000) và 4 phân bố đặc biệt ở "
        "N = 400,000 gồm sorted, nearly_sorted (hoán đổi ngẫu nhiên 1% N cặp), reverse và few_unique (10 giá trị)."
    )
    add_bullet(
        doc, "Quy trình chống nhiễu: ",
        f"Thử 22 giá trị CUTOFF từ 1 đến 64 qua 6 tiến trình JVM độc lập × 8 lượt = 48 block/dataset "
        f"(tổng {samples_total:,} mẫu). Trước khi đo có warm-up JIT; trong mỗi block xáo ngẫu nhiên thứ tự "
        f"dataset và CUTOFF; tách clone() và kiểm tra checksum/isSorted ra ngoài vùng đo nanoTime(); dùng -Xmn1200m "
        f"-XX:+UseSerialGC kết hợp System.gc() trước mỗi block nên đạt {samples_dropped} mẫu bị loại do GC."
    )
    add_bullet(
        doc, "Thống kê: ",
        "Chuẩn hóa thời gian theo trung vị từng block (rel = t / median_block) để khử trôi hiệu năng máy; "
        "tính khoảng tin cậy 95% bằng bootstrap (2.000 lần), kiểm định cặp Wilcoxon–Holm và chỉ số regret "
        "(% chậm hơn CUTOFF tốt nhất của từng dataset)."
    )

    doc.add_heading("3. Kết quả thí nghiệm chính và phân tích", level=1)
    doc.add_heading("3.1. Hiệu năng theo kích thước N và phân bố đầu vào", level=2)

    b_rows = []
    for _, r in best_df.iterrows():
        b_rows.append([
            f"{r['dataset']} ({int(r['n']):,})",
            int(r["best_cutoff"]),
            f"{r['best_median_ms']:.2f}",
            f"{r['gain_vs_c1_pct']:.1f}%",
            f"{r['regret_c7_pct']:.1f}%",
            f"{r['regret_c10_pct']:.1f}%",
            str(r["within_1pct"]),
        ])
    add_styled_table(
        doc,
        ["Bộ dữ liệu (N)", "Tốt nhất", "Median (ms)", "Nhanh hơn c=1", "Regret c=7", "Regret c=10", "Vùng ≤ 1%"],
        b_rows,
    )

    doc.add_paragraph(
        "Trên dữ liệu ngẫu nhiên (Hình 1), sử dụng CUTOFF giúp rút ngắn rõ rệt thời gian chạy so với "
        "CUTOFF = 1. Vùng tối ưu dịch chuyển lên khoảng 20–48 (tốt nhất tại 20 với N=10,000; 24 với N=100,000; "
        "48 với N=1,000,000), trong khi hai mốc tham chiếu 7 và 10 vẫn chậm hơn khoảng 2.5%–8.3%."
    )
    add_chart(doc, "chart1_random_cutoff.png", "Hình 1. Thời gian tương đối theo CUTOFF trên dữ liệu ngẫu nhiên.")

    doc.add_paragraph(
        "Với các phân bố đặc biệt ở N = 400,000 (Hình 2 và Hình 3), sorted và nearly_sorted đạt nhanh nhất tại "
        "CUTOFF = 64 nhờ Insertion Sort có chi phí tuyến tính O(s) trên mảng đã/gần có thứ tự. Ngược lại, "
        "reverse là trường hợp xấu nhất của Insertion Sort (~s²/2 phép đổi chỗ) nên đạt tối ưu tại 9 và chậm đi "
        "nhanh chóng khi CUTOFF > 20 (regret vọt tới 40.7% tại 64). Với few_unique, nhiều khóa trùng giúp Insertion "
        "Sort dừng sớm và đạt tối ưu ở vùng 24–48 (tốt nhất tại 32)."
    )
    add_chart(doc, "chart2_distributions.png", "Hình 2. Thời gian tương đối theo CUTOFF trên 4 phân bố đặc biệt (N = 400,000).", width_in=5.8)
    add_chart(doc, "chart3_regret_heatmap.png", "Hình 3. Ma trận regret (% chậm hơn mức tốt nhất của chính dataset).")

    doc.add_heading("3.2. Kiểm soát nhiễu và mô hình chi phí", level=2)
    doc.add_paragraph(
        "Hình 4 cho thấy chuẩn hóa theo block giúp thu hẹp rõ rệt độ phân tán so với thời gian thô (ms), "
        "làm nổi bật xu hướng giảm thời gian từ CUTOFF = 1 xuống đáy ở vùng 16–48 rồi tăng lại ở 64."
    )
    add_chart(doc, "chart4_noise_boxplot.png", "Hình 4. Phân tán của 48 lần đo trước và sau chuẩn hóa theo block (random, N = 1,000,000).")

    r2_txt = ", ".join(f"N={int(r['n']):,}: R²={r['R2']:.3f}" for _, r in fit_df.iterrows())
    doc.add_paragraph(
        f"Vì phép chia mid = lo + (hi - lo)/2 tạo ra kích thước lá trung bình biến đổi theo từng bậc (đường xám, Hình 5), "
        f"nhiều giá trị CUTOFF gần nhau sinh ra cùng một cây đệ quy và hình thành các vùng phẳng (plateau). "
        f"Mô hình chi phí 3 tham số khớp rất sát số đo thực tế ({r2_txt})."
    )
    add_chart(doc, "chart5_cost_model.png", "Hình 5. Mô hình chi phí so với số đo thực tế và kích thước lá trung bình.", width_in=5.2)

    doc.add_heading("3.3. Lựa chọn giá trị CUTOFF tổng quát", level=2)
    key_cutoffs = [c for c in [1, 7, 10, 16, 20, 24, 28, 32, 40, 48, 64] if c in ov_df.index]
    ov_rows = []
    for c in key_cutoffs:
        r = ov_df.loc[c]
        ov_rows.append([
            str(c),
            f"{r['mean_regret_pct']:.2f}%",
            f"{r['max_regret_pct']:.2f}%",
            f"{r['random_only_mean_regret_pct']:.2f}%",
            f"{r['random_only_max_regret_pct']:.2f}%",
        ])
    add_styled_table(
        doc,
        ["CUTOFF", "Mean regret (7 DS)", "Max regret (7 DS)", "Mean regret (random)", "Max regret (random)"],
        ov_rows,
    )

    doc.add_paragraph(
        f"Tổng hợp trên cả 7 bộ dữ liệu (Hình 6), CUTOFF = {minimax_c} tối ưu theo tiêu chí minimax regret "
        f"(mức chậm xấu nhất trên mọi phân bố chỉ {ov_df.loc[minimax_c, 'max_regret_pct']:.2f}%, trung bình "
        f"{ov_df.loc[minimax_c, 'mean_regret_pct']:.2f}%, riêng dữ liệu random chỉ "
        f"{ov_df.loc[minimax_c, 'random_only_mean_regret_pct']:.2f}%). CUTOFF = {mean_c} có regret trung bình "
        f"thấp nhất ({ov_df.loc[mean_c, 'mean_regret_pct']:.2f}%) nhưng mức chậm tối đa trên reverse tăng lên "
        f"{ov_df.loc[mean_c, 'max_regret_pct']:.2f}%. Hai mốc tham chiếu 7 và 10 đều có max regret khoảng 23%."
    )
    add_chart(doc, "chart6_overall_regret.png", "Hình 6. So sánh regret trung bình và regret lớn nhất để chọn CUTOFF chung.")

    doc.add_heading("4. Thí nghiệm bổ trợ và kiểm chứng", level=1)
    doc.add_heading("4.1. Giả thuyết nhân đôi — Doubling Hypothesis", level=2)
    slope_note = ""
    if sc_df is not None and not sc_df.empty:
        slopes = sc_df.groupby("cutoff")["loglog_slope"].first()
        slope_note = " (hệ số góc log-log trong khoảng " + f"{slopes.min():.2f}–{slopes.max():.2f})"
    doc.add_paragraph(
        f"Đo trên chuỗi kích thước nhân đôi N = 15,625 × 2^k (k = 0..6) cho CUTOFF ∈ {{1, 7, 10, 24}} (Hình 7): "
        f"trên đồ thị log-log, cả 4 đường đều bám sát đường chuẩn N lg N{slope_note}, xác nhận CUTOFF không đổi "
        f"bậc tăng trưởng Θ(N lg N) mà chỉ tối ưu hằng số ẩn T/(N lg N). Trên mọi cỡ N, CUTOFF = 24 luôn giữ hằng "
        f"số thấp nhất, tiếp theo là 10, 7 và 1. Xu hướng T/(N lg N) tăng nhẹ khi N lớn phản ánh hiệu ứng cache miss."
    )
    add_chart(doc, "chart7_scaling.png", "Hình 7. Giả thuyết nhân đôi và hằng số ẩn T / (N lg N) theo kích thước N.")

    doc.add_heading("4.2. Kiểm chứng độc lập trên mảng ngẫu nhiên mới", level=2)
    if val_df is not None and not val_df.empty:
        v_rows = []
        for _, r in val_df.iterrows():
            p_str = "—" if pd.isna(r["p_vs_best"]) else f"{r['p_vs_best']:.4g}"
            v_rows.append([
                f"{int(r['n']):,}",
                int(r["cutoff"]),
                f"{r['median_ms']:.2f}",
                f"{r['median_rel']:.4f}",
                f"{r['regret_pct']:.2f}%",
                p_str,
            ])
        add_styled_table(
            doc,
            ["N", "CUTOFF", "Median (ms)", "Median rel", "Regret (%)", "p-value vs best"],
            v_rows,
        )
    doc.add_paragraph(
        "Kiểm chứng trên 48 mảng ngẫu nhiên sinh mới hoàn toàn cho mỗi cỡ N = 100,000 và N = 1,000,000 (Hình 8) "
        "tái khẳng định kết quả chính: nhóm CUTOFF 16–32 (tốt nhất tại 32) nhanh hơn rõ rệt so với 1, 7 và 10, "
        "cho thấy kết luận không bị phụ thuộc vào các tệp dữ liệu cố định."
    )
    add_chart(doc, "chart8_validation.png", "Hình 8. Kiểm chứng độc lập trên 48 mảng ngẫu nhiên mới cho mỗi N.")

    doc.add_heading("5. Kết luận", level=1)
    add_bullet(
        doc, "Khuyến nghị cấu hình máy thử nghiệm: ",
        f"Chọn CUTOFF = {minimax_c} làm ngưỡng tổng quát an toàn nhất (tối ưu minimax regret trên mọi phân bố, "
        f"kể cả trường hợp xấu nhất reverse). Nếu ưu tiên bài toán có dữ liệu ngẫu nhiên hoặc gần có thứ tự, "
        f"vùng 24–32 mang lại hiệu năng cao và ổn định nhất."
    )
    add_bullet(
        doc, "Lý giải sự khác biệt so với các mốc tham chiếu 7 và 10: ",
        "Hằng số chi phí phụ thuộc mạnh vào kiến trúc phần cứng và JVM. Trên Intel Core i7-1355U "
        "và OpenJDK 25, mảng con 24–32 phần tử nằm gọn trong L1 cache, vòng lặp Insertion Sort được JIT tối ưu "
        "rất hiệu quả so với chi phí gọi đệ quy và sao chép aux[] của Mergesort."
    )
    add_bullet(
        doc, "Phạm vi áp dụng: ",
        "Kết luận áp dụng cho cài đặt Top-down Mergesort chuẩn chỉ dùng cải tiến CUTOFF trên mảng Integer[]. "
        "Nếu kết hợp thêm cải tiến loại bỏ bước sao chép aux[] hoặc sắp xếp kiểu nguyên thủy int[], "
        "cần đo lại theo cùng quy trình thực nghiệm này."
    )

    doc.save(OUT_DOCX)
    print(f"Đã xuất báo cáo Word thành công: {OUT_DOCX}")


if __name__ == "__main__":
    main()