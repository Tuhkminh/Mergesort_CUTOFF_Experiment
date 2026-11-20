import java.io.*;
import java.util.*;

/**
 * Thí nghiệm phụ: kiểm tra giả thuyết nhân đôi (doubling hypothesis) - thời gian ~ N log N.
 * Dùng N = 15625 * 2^k (k = 0..6) là PREFIX của random_1000000.txt, cho một vài giá trị cutoff.
 * Tham số: <jvmId> <rounds> <outCsv> <cutoff1,cutoff2,...> [dataDir]
 */
public class ScalingExperiment {
    public static void main(String[] args) throws IOException {
        int jvmId = Integer.parseInt(args[0]);
        int rounds = Integer.parseInt(args[1]);
        String out = args[2];
        String[] cs = args[3].split(",");
        int[] cutoffs = new int[cs.length];
        for (int i = 0; i < cs.length; i++) cutoffs[i] = Integer.parseInt(cs[i]);
        String dir = args.length > 4 ? args[4] : "data";
        Random rnd = new Random(9_000L + jvmId);

        int K = 7;
        Integer[][] data = new Integer[K][];
        long[] sums = new long[K];
        for (int k = 0; k < K; k++) {
            data[k] = ExpUtil.load(dir + "/random_1000000.txt", 15625 << k);
            sums[k] = ExpUtil.checksum(data[k]);
        }
        for (int w = 0; w < 6; w++)
            for (int k = 0; k < K; k++)
                ExpUtil.timeOnce(data[k], sums[k], cutoffs[rnd.nextInt(cutoffs.length)]);

        try (PrintWriter pw = new PrintWriter(new BufferedWriter(new FileWriter(out)))) {
            pw.println("jvm,round,n,cutoff,pos,time_ns,gc");
            for (int r = 1; r <= rounds; r++) {
                int[] kOrder = new int[K];
                for (int i = 0; i < K; i++) kOrder[i] = i;
                ExpUtil.shuffle(kOrder, rnd);
                for (int k : kOrder) {
                    int[] order = cutoffs.clone();
                    ExpUtil.shuffle(order, rnd);
                    System.gc();
                    for (int pos = 0; pos < order.length; pos++) {
                        long[] res = ExpUtil.timeOnce(data[k], sums[k], order[pos]);
                        pw.printf("%d,%d,%d,%d,%d,%d,%d%n", jvmId, r, 15625 << k, order[pos], pos, res[0], res[1]);
                    }
                }
                pw.flush();
            }
        }
    }
}
