# Chạy toàn bộ thí nghiệm CUTOFF (Linux/macOS). Chạy từ thư mục gốc của project.
set -e
JVMS=${1:-6}; ROUNDS=${2:-8}
JOPTS="-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC -Dstdout.encoding=UTF-8"
mkdir -p bin results data
echo "[1/5] Biên dịch";            javac -d bin src/*.java
echo "[2/5] Kiểm thử mergesort";   java -cp bin MergeTest
echo "[3/5] Sinh dữ liệu";         java -cp bin DataGenerator data
echo "[4/5] Thí nghiệm chính: $JVMS JVM x $ROUNDS lượt"
rm -f results/raw_cutoff_jvm*.csv
for j in $(seq 1 $JVMS); do
  java $JOPTS -cp bin CutoffExperiment $j $ROUNDS results/raw_cutoff_jvm$j.csv data
done
echo "[5/5] Thống kê + vẽ đồ thị";  python3 scripts/analyze.py
