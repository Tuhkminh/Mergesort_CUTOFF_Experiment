import java.util.Arrays;
import java.util.Random;

/** Kiểm tra tính đúng đắn + tính ổn định của Merge.sort với mọi CUTOFF. Chạy trước khi đo. */
public class MergeTest {
    /** Phần tử có khoá + số thứ tự gốc, để kiểm tra stability. */
    static class Item implements Comparable<Item> {
        final int key, id;
        Item(int key, int id) { this.key = key; this.id = id; }
        public int compareTo(Item o) { return Integer.compare(key, o.key); }
    }

    public static void main(String[] args) {
        Random rnd = new Random(1);
        int checks = 0;
        int[] sizes = {0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 15, 16, 17, 31, 32, 33, 63, 64, 65, 100, 1000, 12345};
        for (int n : sizes) {
            for (int range : new int[]{3, 1_000_000}) {       // nhiều trùng khoá / ít trùng khoá
                for (int cutoff = 1; cutoff <= 70; cutoff++) {
                    Item[] a = new Item[n];
                    for (int i = 0; i < n; i++) a[i] = new Item(rnd.nextInt(range), i);
                    Item[] ref = a.clone();
                    Arrays.sort(ref, (x, y) -> x.key != y.key ? Integer.compare(x.key, y.key)
                                                              : Integer.compare(x.id, y.id));  // đáp án ổn định
                    Merge.sort(a, cutoff);
                    for (int i = 0; i < n; i++)
                        if (a[i] != ref[i]) throw new AssertionError("SAI: n=" + n + " cutoff=" + cutoff + " range=" + range);
                    checks++;
                }
                Item[] b = new Item[n];
                for (int i = 0; i < n; i++) b[i] = new Item(rnd.nextInt(range), i);
                Item[] ref = b.clone();
                Arrays.sort(ref, (x, y) -> x.key != y.key ? Integer.compare(x.key, y.key) : Integer.compare(x.id, y.id));
                Merge.sort(b);
                for (int i = 0; i < n; i++)
                    if (b[i] != ref[i]) throw new AssertionError("SAI (pure): n=" + n);
                checks++;
            }
        }
        System.out.println("MergeTest: OK (" + checks + " trường hợp, gồm cả kiểm tra stability)");
    }
}
