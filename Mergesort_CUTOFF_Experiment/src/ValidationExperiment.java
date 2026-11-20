import java.io.*;
import java.util.*;

/**
 * Thí nghiệm kiểm chứng độc lập (held-out): mỗi lượt đo dùng MỘT MẢNG NGẪU NHIÊN MỚI (seed khác hẳn
 * các file trong data/), để chắc chắn kết luận không phụ thuộc vào 3 mảng random cố định ở thí nghiệm chính.
 * seed = 31_000_000 + jvmId*1000 + round + N   (tái lập được)
 * Tham số: <jvmId> <rounds> <outCsv> <cutoff1,cutoff2,...> <n1,n2,...>
 */
public class ValidationExperiment {
    public static void main(String[] args) throws IOException {
        int jvmId = Integer.parseInt(args[0]);
        int rounds = Integer.parseInt(args[1]);
        String out = args[2];
        int[] cutoffs = Arrays.stream(args[3].split(",")).mapToInt(Integer::parseInt).toArray();
        int[] sizes = Arrays.stream(args[4].split(",")).mapToInt(Integer::parseInt).toArray();
        Random rnd = new Random(11_000L + jvmId);

        // warm-up
        for (int w = 0; w < 8; w++)
            for (int n : sizes) {
                Integer[] a = gen(n, 5L + w);
                ExpUtil.timeOnce(a, ExpUtil.checksum(a), cutoffs[rnd.nextInt(cutoffs.length)]);
            }

        try (PrintWriter pw = new PrintWriter(new BufferedWriter(new FileWriter(out)))) {
            pw.println("jvm,round,n,cutoff,pos,time_ns,gc");
            for (int r = 1; r <= rounds; r++) {
                for (int n : sizes) {
                    Integer[] a = gen(n, 31_000_000L + jvmId * 1000L + r + n);
                    long sum = ExpUtil.checksum(a);
                    int[] order = cutoffs.clone();
                    ExpUtil.shuffle(order, rnd);
                    System.gc();
                    for (int pos = 0; pos < order.length; pos++) {
                        long[] res = ExpUtil.timeOnce(a, sum, order[pos]);
                        pw.printf("%d,%d,%d,%d,%d,%d,%d%n", jvmId, r, n, order[pos], pos, res[0], res[1]);
                    }
                }
                pw.flush();
            }
        }
    }

    static Integer[] gen(int n, long seed) {
        Random r = new Random(seed);
        Integer[] a = new Integer[n];
        for (int i = 0; i < n; i++) a[i] = Integer.valueOf(r.nextInt(10 * n));
        return a;
    }
}
