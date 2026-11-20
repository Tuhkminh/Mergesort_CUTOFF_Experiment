import java.io.*;
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.util.Random;

/** Các hàm cho các chương trình đo. */
public class ExpUtil {
    public static Integer[] load(String path, int limit) throws IOException {
        try (BufferedReader br = new BufferedReader(new FileReader(path), 1 << 16)) {
            int n = Integer.parseInt(br.readLine().trim());
            if (limit > 0 && limit < n) n = limit;
            Integer[] a = new Integer[n];
            for (int i = 0; i < n; i++) a[i] = Integer.valueOf(Integer.parseInt(br.readLine().trim()));
            return a;
        }
    }

    public static long gcCount() {
        long c = 0;
        for (GarbageCollectorMXBean b : ManagementFactory.getGarbageCollectorMXBeans()) c += b.getCollectionCount();
        return c;
    }

    public static long checksum(Integer[] a) {
        long s = 0;
        for (Integer x : a) s += x;
        return s;
    }

    /** Fisher-Yates với Random có seed (để thứ tự ngẫu nhiên nhưng tái lập được). */
    public static void shuffle(int[] a, Random r) {
        for (int i = a.length - 1; i > 0; i--) {
            int j = r.nextInt(i + 1);
            int t = a[i]; a[i] = a[j]; a[j] = t;
        }
    }

    /** Đo một lần: clone (ngoài vùng đo) -> sort (trong vùng đo) -> kiểm tra đúng (ngoài vùng đo). */
    public static long[] timeOnce(Integer[] original, long expectedSum, int cutoff) {
        Integer[] arr = original.clone();
        long g0 = gcCount();
        long t0 = System.nanoTime();
        Merge.sort(arr, cutoff);
        long t1 = System.nanoTime();
        long g1 = gcCount();
        if (!Merge.isSorted(arr) || checksum(arr) != expectedSum)
            throw new IllegalStateException("Kết quả sắp xếp sai! cutoff=" + cutoff);
        return new long[]{t1 - t0, g1 - g0};
    }
}
