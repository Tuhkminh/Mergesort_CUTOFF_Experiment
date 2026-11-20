import java.io.*;
import java.util.Random;

/**
 * Sinh bộ dữ liệu thí nghiệm (có seed cố định => tái lập được 100%).
 * Định dạng file: dòng 1 = N, sau đó mỗi dòng một số nguyên.
 *
 *  random_{10000,100000,1000000}.txt : số ngẫu nhiên đều trong [0, 10N)
 *  sorted_400000.txt                 : đã sắp xếp tăng
 *  nearly_sorted_400000.txt          : sắp xếp tăng rồi hoán đổi ngẫu nhiên 1% N cặp
 *  reverse_400000.txt                : sắp xếp giảm
 *  few_unique_400000.txt             : chỉ có 10 giá trị phân biệt (0..9)
 */
public class DataGenerator {
    private static final long BASE_SEED = 20261120L;

    public static void main(String[] args) throws IOException {
        String dir = args.length > 0 ? args[0] : "data";
        new File(dir).mkdirs();

        for (int n : new int[]{10_000, 100_000, 1_000_000}) {
            Random r = new Random(BASE_SEED + n);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = r.nextInt(10 * n);
            save(dir + "/random_" + n + ".txt", a);
        }

        final int N = 400_000;
        int[] sorted = new int[N];
        for (int i = 0; i < N; i++) sorted[i] = i;
        save(dir + "/sorted_" + N + ".txt", sorted);

        Random r2 = new Random(BASE_SEED + 2);
        int[] nearly = sorted.clone();
        for (int s = 0; s < N / 100; s++) {
            int i = r2.nextInt(N), j = r2.nextInt(N);
            int t = nearly[i]; nearly[i] = nearly[j]; nearly[j] = t;
        }
        save(dir + "/nearly_sorted_" + N + ".txt", nearly);

        int[] rev = new int[N];
        for (int i = 0; i < N; i++) rev[i] = N - i;
        save(dir + "/reverse_" + N + ".txt", rev);

        Random r3 = new Random(BASE_SEED + 3);
        int[] few = new int[N];
        for (int i = 0; i < N; i++) few[i] = r3.nextInt(10);
        save(dir + "/few_unique_" + N + ".txt", few);
    }

    private static void save(String path, int[] a) throws IOException {
        try (BufferedWriter bw = new BufferedWriter(new FileWriter(path), 1 << 16)) {
            bw.write(Integer.toString(a.length)); bw.write('\n');
            for (int v : a) { bw.write(Integer.toString(v)); bw.write('\n'); }
        }
        System.out.println("  ghi " + path + " (" + a.length + " phần tử)");
    }
}
