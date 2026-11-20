import java.io.*;
import java.util.*;

/**
 * Thí nghiệm chính: đo thời gian Merge.sort(a, CUTOFF) cho nhiều CUTOFF x nhiều bộ dữ liệu.
 */
public class CutoffExperiment {
    static final int[] CUTOFFS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 40, 48, 64};
    static final String[][] DATASETS = {
        {"random",        "10000",   "random_10000.txt"},
        {"random",        "100000",  "random_100000.txt"},
        {"random",        "1000000", "random_1000000.txt"},
        {"sorted",        "400000",  "sorted_400000.txt"},
        {"nearly_sorted", "400000",  "nearly_sorted_400000.txt"},
        {"reverse",       "400000",  "reverse_400000.txt"},
        {"few_unique",    "400000",  "few_unique_400000.txt"},
    };

    public static void main(String[] args) throws IOException {
        int jvmId = Integer.parseInt(args[0]);
        int rounds = Integer.parseInt(args[1]);
        String out = args[2];
        String dir = args.length > 3 ? args[3] : "data";
        Random rnd = new Random(7_000L + jvmId);

        Integer[][] data = new Integer[DATASETS.length][];
        long[] sums = new long[DATASETS.length];
        for (int d = 0; d < DATASETS.length; d++) {
            data[d] = ExpUtil.load(dir + "/" + DATASETS[d][2], 0);
            sums[d] = ExpUtil.checksum(data[d]);
        }

        // ---- warm-up: biên dịch JIT ổn định trước khi đo ----
        for (int w = 0; w < 4; w++)
            for (int d = 0; d < DATASETS.length; d++)
                for (int k = 0; k < 4; k++)
                    ExpUtil.timeOnce(data[d], sums[d], CUTOFFS[rnd.nextInt(CUTOFFS.length)]);
        System.out.println("[jvm " + jvmId + "] warm-up xong");

        try (PrintWriter pw = new PrintWriter(new BufferedWriter(new FileWriter(out)))) {
            pw.println("jvm,round,dataset,n,cutoff,pos,time_ns,gc");
            for (int r = 1; r <= rounds; r++) {
                int[] dOrder = new int[DATASETS.length];
                for (int i = 0; i < dOrder.length; i++) dOrder[i] = i;
                ExpUtil.shuffle(dOrder, rnd);
                for (int d : dOrder) {
                    int[] order = CUTOFFS.clone();
                    ExpUtil.shuffle(order, rnd);
                    System.gc();
                    for (int pos = 0; pos < order.length; pos++) {
                        long[] res = ExpUtil.timeOnce(data[d], sums[d], order[pos]);
                        pw.printf("%d,%d,%s,%s,%d,%d,%d,%d%n", jvmId, r, DATASETS[d][0], DATASETS[d][1],
                                  order[pos], pos, res[0], res[1]);
                    }
                }
                pw.flush();
                System.out.println("[jvm " + jvmId + "] xong lượt " + r + "/" + rounds);
            }
        }
    }
}
