# Thí nghiệm xác định ngưỡng CUTOFF cho Mergesort

Dự án thực nghiệm tìm giá trị `CUTOFF` (ngưỡng chuyển sang Insertion Sort cho mảng con nhỏ) tối ưu cho thuật toán Top-down Mergesort.

## Cấu trúc thư mục

```text
Mergesort_CUTOFF_Experiment/
├── src/                    # Cài đặt Mergesort, Insertion Sort và các chương trình đo
│   ├── Merge.java          # Top-down Mergesort
│   ├── Insertion.java      # Insertion Sort
│   ├── MergeTest.java      # Kiểm thử tính đúng đắn và tính ổn định
│   ├── DataGenerator.java  # Sinh 7 bộ dữ liệu test (BASE_SEED = 20261120L, tái lập 100%)
│   ├── CutoffExperiment.java     # Thí nghiệm chính (22 cutoff × 7 bộ dữ liệu)
│   ├── ScalingExperiment.java    # Thí nghiệm giả thuyết nhân đôi
│   ├── ValidationExperiment.java # Kiểm chứng độc lập trên mảng ngẫu nhiên mới
│   └── ExpUtil.java        # Tiện ích nạp dữ liệu, checksum, đo nanoTime & đếm GC
├── scripts/
│   ├── run_experiment.bat / .sh  # Biên dịch, kiểm thử, sinh dữ liệu, chạy thí nghiệm chính
│   ├── run_extra.bat / .sh       # Chạy thí nghiệm nhân đôi N và kiểm chứng độc lập
│   ├── analyze.py                # Thống kê & vẽ đồ thị
│   └── export_word_report.py     # Xuất báo cáo định dạng Word kèm đủ biểu đồ
├── data/                   # 7 tệp dữ liệu thí nghiệm (.txt)
├── results/                # Dữ liệu thô, bảng thống kê (.csv) và biểu đồ (charts/)
├── BaoCao_ThiNghiem_CUTOFF.docx  # Báo cáo thí nghiệm (bản Word)
└── README.md
```

## Yêu cầu môi trường

* **Java JDK** (đã chạy trên OpenJDK 25.0.5 LTS, 64-bit).
* **Python 3** (đã chạy trên Python 3.15.2) cùng các thư viện:
  ```bash
  pip install numpy pandas matplotlib scipy python-docx
  ```
* RAM trống tối thiểu 2.5 GB (cờ JVM: `-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC`).

## Cách chạy lại thí nghiệm

Mở terminal tại **thư mục gốc** `Mergesort_CUTOFF_Experiment`:

* **Windows (Command Prompt):**
  ```cmd
  scripts\run_experiment.bat
  scripts\run_extra.bat
  ```
* **Linux / macOS:**
  ```bash
  bash scripts/run_experiment.sh
  bash scripts/run_extra.sh
  ```
* **Xuất lại báo cáo Word (`.docx`) từ số liệu và biểu đồ đã đo:**
  ```cmd
  python scripts\export_word_report.py
  ```

## Tóm tắt kết quả trên máy thử nghiệm

* **Cấu hình:** Windows 11 64-bit, Intel Core i7-1355U (1.70 GHz), 16 GB RAM, OpenJDK 25.0.5 LTS.
* **Độ sạch phép đo:** 7.392 mẫu đo ở thí nghiệm chính, **0 mẫu bị loại do GC**.
* **Kết luận:** Mốc giáo trình (`7` và `10`) không còn tối ưu trên phần cứng/JVM hiện đại. Giá trị khuyến nghị chung là **`CUTOFF = 24`** (tối ưu *minimax regret* với mức chậm tối đa 10,16% trên cả 7 phân bố và regret trung bình trên dữ liệu ngẫu nhiên chỉ 0,70%), hoặc vùng **`24–32`** khi ưu tiên dữ liệu ngẫu nhiên.