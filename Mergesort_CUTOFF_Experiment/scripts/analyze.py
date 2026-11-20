#!/usr/bin/env python3
"""
Phân tích thống kê kết quả thí nghiệm CUTOFF.
Đọc : results/raw_cutoff_jvm*.csv   (+ results/raw_scaling_jvm*.csv nếu có)
Ghi : results/*.csv (bảng thống kê) và results/charts/*.png (đồ thị)
"""
import glob, sys, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from functools import lru_cache

R = "results"; CH = R + "/charts"
os.makedirs(CH, exist_ok=True)
rng = np.random.default_rng(12345)
plt.rcParams.update({"figure.dpi": 100, "font.size": 12, "axes.grid": True, "grid.alpha": .3})

# ------------------------------------------------------------------ nạp dữ liệu
raw = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(R + "/raw_cutoff_jvm*.csv"))], ignore_index=True)
raw["ms"] = raw.time_ns / 1e6
BK = ["jvm", "round", "dataset", "n"]
n_all = len(raw)
bad = raw.groupby(BK).gc.transform("sum") > 0         # block có GC xảy ra trong lúc đo -> loại cả block
n_drop = int(bad.sum())
df = raw[~bad].copy()
df["ref"] = df.groupby(BK).ms.transform("median")
df["rel"] = df.ms / df.ref
ncut = df.cutoff.nunique()
blocks_per = df.groupby(["dataset", "n"]).apply(lambda g: g.groupby(BK[:2]).ngroups, include_groups=False)
print(f"Tổng mẫu: {n_all}; loại {n_drop} mẫu do GC; cutoff: {sorted(df.cutoff.unique())}")

DS = [("random", 10000), ("random", 100000), ("random", 1000000),
      ("sorted", 400000), ("nearly_sorted", 400000), ("reverse", 400000), ("few_unique", 400000)]
LBL = {k: f"{k[0]} N={k[1]:,}" for k in DS}
CUT = sorted(df.cutoff.unique())

def boot_ci(x, B=2000):
    x = np.asarray(x); idx = rng.integers(0, len(x), (B, len(x)))
    m = np.median(x[idx], axis=1)
    return np.percentile(m, [2.5, 97.5])

# ------------------------------------------------------------------ bảng 1: thống kê theo (dataset, cutoff)
rows = []
for k in DS:
    g = df[(df.dataset == k[0]) & (df.n == k[1])]
    for c, h in g.groupby("cutoff"):
        lo, hi = boot_ci(h.rel.values)
        rows.append(dict(dataset=k[0], n=k[1], cutoff=c, samples=len(h),
                         mean_ms=h.ms.mean(), median_ms=h.ms.median(), std_ms=h.ms.std(ddof=1),
                         cv_pct=100 * h.ms.std(ddof=1) / h.ms.mean(), min_ms=h.ms.min(), max_ms=h.ms.max(),
                         median_rel=h.rel.median(), rel_ci_lo=lo, rel_ci_hi=hi))
S = pd.DataFrame(rows)
S["norm_ms"] = S.apply(lambda r: r.median_rel * df[(df.dataset == r.dataset) & (df.n == r.n)].ref.median(), axis=1)
S["regret_pct"] = 100 * (S.median_rel / S.groupby(["dataset", "n"]).median_rel.transform("min") - 1)
S.round(4).to_csv(R + "/summary_by_cutoff.csv", index=False)

# ------------------------------------------------------------------ bảng 2: cutoff tốt nhất + kiểm định cặp
def holm(p):
    p = np.asarray(p); o = np.argsort(p); m = len(p); adj = np.empty(m); run = 0
    for i, j in enumerate(o):
        run = max(run, (m - i) * p[j]); adj[j] = min(1, run)
    return adj

tests, best_rows = [], []
for k in DS:
    g = df[(df.dataset == k[0]) & (df.n == k[1])]
    piv = g.pivot_table(index=["jvm", "round"], columns="cutoff", values="rel")
    s = S[(S.dataset == k[0]) & (S.n == k[1])].set_index("cutoff")
    best = int(s.median_rel.idxmin())
    ps = []
    for c in CUT:
        if c == best: ps.append(np.nan); continue
        d = piv[c] - piv[best]
        try: ps.append(stats.wilcoxon(d, alternative="two-sided").pvalue)
        except ValueError: ps.append(1.0)
    ps = np.array(ps); mask = ~np.isnan(ps); adj = np.full(len(ps), np.nan); adj[mask] = holm(ps[mask])
    for c, p, a in zip(CUT, ps, adj):
        tests.append(dict(dataset=k[0], n=k[1], best=best, cutoff=c, p_raw=p, p_holm=a,
                          indistinguishable=(c == best) or (a >= 0.05)))
    T = pd.DataFrame(tests[-len(CUT):]).set_index("cutoff")
    plateau = [c for c in CUT if T.loc[c, "indistinguishable"]]
    within1 = [c for c in CUT if s.loc[c, "regret_pct"] <= 1.0]
    best_rows.append(dict(dataset=k[0], n=k[1], best_cutoff=best, best_median_ms=s.loc[best, "median_ms"],
        ms_c1=s.loc[1, "median_ms"], ms_c7=s.loc[7, "median_ms"], ms_c10=s.loc[10, "median_ms"],
        gain_vs_c1_pct=100 * (1 - s.loc[best, "median_rel"] / s.loc[1, "median_rel"]),
        regret_c7_pct=s.loc[7, "regret_pct"], regret_c10_pct=s.loc[10, "regret_pct"],
        p_holm_best_vs_7=T.loc[7, "p_holm"], p_holm_best_vs_10=T.loc[10, "p_holm"],
        plateau_not_sig_diff=" ".join(map(str, plateau)), within_1pct=" ".join(map(str, within1))))
TT = pd.DataFrame(tests); TT.round(5).to_csv(R + "/paired_tests.csv", index=False)
B = pd.DataFrame(best_rows); B.round(3).to_csv(R + "/best_cutoff_summary.csv", index=False)

# ------------------------------------------------------------------ bảng 3: regret ma trận + minimax
M = S.pivot_table(index=["dataset", "n"], columns="cutoff", values="regret_pct").loc[DS]
M.round(2).to_csv(R + "/regret_matrix.csv")
def agg(keys):
    sub = M.loc[keys]
    return pd.DataFrame({"mean_regret_pct": sub.mean(), "max_regret_pct": sub.max()})
OV = agg(DS).join(agg([k for k in DS if k[0] == "random"]).add_prefix("random_only_"))
OV.round(3).to_csv(R + "/overall_regret.csv")
best_minimax = int(OV.max_regret_pct.idxmin()); best_mean = int(OV.mean_regret_pct.idxmin())
print("Minimax regret cutoff (mọi dataset):", best_minimax, " | trung bình regret nhỏ nhất:", best_mean)

# ------------------------------------------------------------------ cấu trúc đệ quy: kích thước lá thực tế
def leaf_stats(n, c):
    """Mô phỏng sort(): trả (số lá, độ sâu trung bình theo phần tử, tổng s(s-1)/4 trên các lá, kích thước lá trung bình)."""
    @lru_cache(None)
    def rec(size, depth):
        if size <= c: return {(size, depth): 1}
        L = (size + 1) // 2; Rr = size // 2     # mid = lo+(hi-lo)/2  => nửa trái có ceil(size/2) phần tử
        out = {}
        for sub in (rec(L, depth + 1), rec(Rr, depth + 1)):
            for key, v in sub.items(): out[key] = out.get(key, 0) + v
        return out
    d = rec(n, 0)
    leaves = sum(d.values()); tot = sum(s * v for (s, _), v in d.items())
    avg_depth = sum(s * dep * v for (s, dep), v in d.items()) / tot
    ins = sum(s * (s - 1) / 4 * v for (s, _), v in d.items())
    return leaves, avg_depth, ins, tot / leaves

# ------------------------------------------------------------------ mô hình chi phí: t = a*N*depth + b*Insertion + c*N
fit_rows = []
mod = {}
for k in [("random", 10000), ("random", 100000), ("random", 1000000)]:
    s = S[(S.dataset == k[0]) & (S.n == k[1])].set_index("cutoff")
    X = []; y = []
    for c in CUT:
        lv, ad, ins, ml = leaf_stats(k[1], c)
        X.append([k[1] * ad, ins, k[1]]); y.append(s.loc[c, "norm_ms"])
    X = np.array(X); y = np.array(y)
    from scipy.optimize import nnls
    coef, _ = nnls(X, y); pred = X @ coef
    r2 = 1 - ((y - pred) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    mod[k] = (coef, pred, r2)
    fit_rows.append(dict(n=k[1], a_merge_ns_per_elem_level=coef[0] * 1e6, b_insertion_ns_per_inversion=coef[1] * 1e6,
                         c_const_ns_per_elem=coef[2] * 1e6, R2=r2, model_best_cutoff=CUT[int(np.argmin(pred))],
                         measured_best_cutoff=int(s.median_rel.idxmin())))
pd.DataFrame(fit_rows).round(4).to_csv(R + "/cost_model_fit.csv", index=False)
lf = pd.DataFrame([dict(n=n, cutoff=c, **dict(zip(["leaves", "avg_depth", "insertion_inversions", "mean_leaf_size"], leaf_stats(n, c))))
                   for n in (10000, 100000, 1000000, 400000) for c in CUT])
lf.round(3).to_csv(R + "/leaf_structure.csv", index=False)

# ------------------------------------------------------------------ đồ thị
def band(ax, k, label=None, color=None, marker="o"):
    s = S[(S.dataset == k[0]) & (S.n == k[1])].sort_values("cutoff")
    ax.plot(s.cutoff, s.median_rel, marker=marker, ms=3.5, lw=1.4, label=label or LBL[k], color=color)
    ax.fill_between(s.cutoff, s.rel_ci_lo, s.rel_ci_hi, alpha=.18, color=ax.lines[-1].get_color())

# Chart 1: dữ liệu ngẫu nhiên, 3 kích thước
fig, axs = plt.subplots(1, 3, figsize=(14, 4.6), sharey=False)
for ax, k in zip(axs, [("random", 10000), ("random", 100000), ("random", 1000000)]):
    band(ax, k); ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8, 16, 32, 64]); ax.set_xticklabels([1, 2, 4, 8, 16, 32, 64])
    for v, col in [(7, "tab:red"), (10, "tab:green")]: ax.axvline(v, ls="--", lw=1, color=col, alpha=.7)
    bst = int(B[(B.dataset == k[0]) & (B.n == k[1])].best_cutoff.iloc[0]); ax.axvline(bst, ls=":", lw=1.5, color="k")
    ax.set_title(f"N={k[1]:,} (tốt nhất: {bst})", fontsize=12); ax.set_xlabel("CUTOFF"); ax.set_ylabel("thời gian tương đối")
fig.suptitle("Hình 1. Thời gian tương đối theo CUTOFF - dữ liệu ngẫu nhiên", fontsize=13)
fig.tight_layout(); fig.savefig(CH + "/chart1_random_cutoff.png", dpi=170); plt.close(fig)

# Chart 2: các phân bố đặc biệt
fig, axs = plt.subplots(2, 2, figsize=(11, 7.2)); axs = axs.ravel()
for ax, k in zip(axs, [("sorted", 400000), ("nearly_sorted", 400000), ("reverse", 400000), ("few_unique", 400000)]):
    band(ax, k); ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8, 16, 32, 64]); ax.set_xticklabels([1, 2, 4, 8, 16, 32, 64])
    for v, col in [(7, "tab:red"), (10, "tab:green")]: ax.axvline(v, ls="--", lw=1, color=col, alpha=.7)
    bst = int(B[(B.dataset == k[0]) & (B.n == k[1])].best_cutoff.iloc[0]); ax.axvline(bst, ls=":", lw=1.5, color="k")
    ax.set_title(f"{k[0]} (tốt nhất: {bst})"); ax.set_xlabel("CUTOFF"); ax.set_ylabel("thời gian tương đối")
fig.suptitle("Hình 2. Thời gian tương đối theo CUTOFF - đầu vào đặc biệt (N = 400,000)", fontsize=13)
fig.tight_layout(); fig.savefig(CH + "/chart2_distributions.png", dpi=170); plt.close(fig)

# Chart 3: heatmap regret
fig, ax = plt.subplots(figsize=(12, 4.6))
vals = M.values; im = ax.imshow(np.minimum(vals, 25), aspect="auto", cmap="YlOrRd")
ax.set_xticks(range(len(CUT))); ax.set_xticklabels(CUT); ax.set_yticks(range(len(DS))); ax.set_yticklabels([LBL[k] for k in DS])
for i in range(vals.shape[0]):
    for j in range(vals.shape[1]):
        ax.text(j, i, f"{vals[i, j]:.0f}" if vals[i, j] >= 10 else f"{vals[i, j]:.1f}", ha="center", va="center", fontsize=8, color=("white" if vals[i, j] > 15 else "black"))
ax.grid(False); ax.set_xlabel("CUTOFF"); fig.colorbar(im, label="regret % (cắt ở 25)")
ax.set_title("Hình 3. Ma trận regret (% chậm hơn cutoff tốt nhất của chính dataset)", fontsize=12)
fig.tight_layout(); fig.savefig(CH + "/chart3_regret_heatmap.png", dpi=170); plt.close(fig)

# Chart 4: nhiễu đo - boxplot thời gian thô random 1M
g = df[(df.dataset == "random") & (df.n == 1000000)]
fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
axs[0].boxplot([g[g.cutoff == c].ms for c in CUT], tick_labels=CUT, showfliers=True, flierprops=dict(ms=2))
axs[0].set_xlabel("CUTOFF"); axs[0].set_ylabel("thời gian thô (ms)"); axs[0].set_title("Thời gian thô (ms)", fontsize=12)
axs[1].boxplot([g[g.cutoff == c].rel for c in CUT], tick_labels=CUT, showfliers=True, flierprops=dict(ms=2))
axs[1].set_xlabel("CUTOFF"); axs[1].set_ylabel("thời gian tương đối"); axs[1].set_title("Sau chuẩn hoá theo block", fontsize=12)
for a in axs: a.tick_params(axis="x", labelsize=8)
fig.suptitle("Hình 4. Phân tán của 48 lần đo - random N=1,000,000", fontsize=13); fig.tight_layout(); fig.savefig(CH + "/chart4_noise_boxplot.png", dpi=170); plt.close(fig)

# Chart 5: mô hình chi phí vs đo + cấu trúc lá
fig, axs = plt.subplots(3, 1, figsize=(8.5, 11))
for ax, k in zip(axs, mod):
    s = S[(S.dataset == k[0]) & (S.n == k[1])].sort_values("cutoff")
    ax.plot(s.cutoff, s.norm_ms, "o-", ms=3.5, label="đo (median, đã chuẩn hoá)")
    ax.plot(CUT, mod[k][1], "s--", ms=3, label=f"mô hình (R²={mod[k][2]:.3f})")
    ml = lf[lf.n == k[1]].sort_values("cutoff")
    ax2 = ax.twinx(); ax2.step(ml.cutoff, ml.mean_leaf_size, where="post", color="gray", alpha=.6, lw=1); ax2.set_ylabel("kích thước lá TB (xám)", color="gray"); ax2.grid(False)
    ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8, 16, 32, 64]); ax.set_xticklabels([1, 2, 4, 8, 16, 32, 64])
    ax.set_title(f"random N={k[1]:,}", fontsize=12); ax.set_xlabel("CUTOFF"); ax.set_ylabel("ms"); ax.legend(fontsize=10, loc="upper right")
fig.suptitle("Hình 5. Mô hình chi phí so với số đo (đường xám: kích thước lá thực tế)", fontsize=13)
fig.tight_layout(); fig.savefig(CH + "/chart5_cost_model.png", dpi=170); plt.close(fig)

# Chart 6: minimax regret tổng hợp
fig, ax = plt.subplots(figsize=(9.5, 4.4))
ax.plot(OV.index, OV.mean_regret_pct, "o-", label="regret trung bình (7 dataset)")
ax.plot(OV.index, OV.max_regret_pct, "s-", label="regret lớn nhất (7 dataset)")
ax.plot(OV.index, OV.random_only_mean_regret_pct, "^--", label="regret trung bình (chỉ random)")
ax.set_xscale("log", base=2); ax.set_xticks([1, 2, 4, 8, 16, 32, 64]); ax.set_xticklabels([1, 2, 4, 8, 16, 32, 64])
ax.set_ylim(0, 35); ax.set_xlabel("CUTOFF"); ax.set_ylabel("% chậm hơn mức tốt nhất (cắt ở 35)"); ax.legend(fontsize=10)
ax.set_title("Hình 6. Chọn một CUTOFF chung: regret trung bình / lớn nhất", fontsize=12); fig.tight_layout(); fig.savefig(CH + "/chart6_overall_regret.png", dpi=170); plt.close(fig)

# ------------------------------------------------------------------ thí nghiệm phụ: scaling (nhân đôi N)
sf = sorted(glob.glob(R + "/raw_scaling_jvm*.csv"))
if sf:
    sc = pd.concat([pd.read_csv(f) for f in sf], ignore_index=True); sc["ms"] = sc.time_ns / 1e6
    sc = sc[sc.groupby(["jvm", "round", "n"]).gc.transform("sum") == 0]
    t = sc.groupby(["cutoff", "n"]).ms.median().reset_index()
    out = []
    for c, h in t.groupby("cutoff"):
        h = h.sort_values("n"); ratio = h.ms.values[1:] / h.ms.values[:-1]
        slope = np.polyfit(np.log2(h.n), np.log2(h.ms), 1)[0]
        for i, (n, ms) in enumerate(zip(h.n, h.ms)):
            out.append(dict(cutoff=c, n=n, median_ms=ms, ratio=(ratio[i - 1] if i else np.nan),
                            lg_ratio=(np.log2(ratio[i - 1]) if i else np.nan),
                            ns_per_NlgN=ms * 1e6 / (n * np.log2(n)), loglog_slope=slope,
                            expected_ratio_NlgN=(2 * np.log2(n) / np.log2(n / 2) if i else np.nan)))
    pd.DataFrame(out).round(4).to_csv(R + "/scaling_doubling.csv", index=False)
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
    for c, h in t.groupby("cutoff"):
        h = h.sort_values("n"); axs[0].loglog(h.n, h.ms, "o-", label=f"cutoff={c}")
        axs[1].plot(h.n, h.ms * 1e6 / (h.n * np.log2(h.n)), "o-", label=f"cutoff={c}")
    nn = np.array(sorted(t.n.unique()), float); ref = t[t.cutoff == t.cutoff.min()].sort_values("n").ms.values[0] * (nn * np.log2(nn)) / (nn[0] * np.log2(nn[0]))
    axs[0].loglog(nn, ref, "k:", label="N lg N chuẩn"); axs[0].set_xlabel("N"); axs[0].set_ylabel("ms"); axs[0].legend(fontsize=9); axs[0].set_title("log-log: T(N)")
    axs[1].set_xscale("log", base=2); axs[1].set_xlabel("N"); axs[1].set_ylabel("T / (N lg N)  [ns]"); axs[1].set_title("Hằng số ẩn sau N lg N"); axs[1].legend(fontsize=9)
    fig.suptitle("Hình 7. Giả thuyết nhân đôi: thời gian mergesort ~ N lg N", fontsize=13); fig.tight_layout(); fig.savefig(CH + "/chart7_scaling.png", dpi=170); plt.close(fig)


# ------------------------------------------------------------------ ước lượng mức nhiễu từ các nhóm cutoff "cùng một cây đệ quy"
nf = []
for n in (10000, 100000, 1000000):
    g = lf[lf.n == n].copy(); g["key"] = g.leaves.astype(str) + "_" + g.insertion_inversions.round(1).astype(str)
    s_ = S[(S.dataset == "random") & (S.n == n)].set_index("cutoff")
    for key, h in g.groupby("key", sort=False):
        cs = list(h.cutoff)
        if len(cs) >= 3:
            v = s_.loc[cs, "median_rel"].values
            nf.append(dict(n=n, cutoffs=" ".join(map(str, cs)), leaf_size=h.mean_leaf_size.iloc[0], spread_pct=100 * (v.max() - v.min()) / v.mean(), std_pct=100 * v.std(ddof=1) / v.mean()))
NF = pd.DataFrame(nf); NF.round(3).to_csv(R + "/noise_floor.csv", index=False)
print("\n== Nhiễu ước lượng từ nhóm cutoff cùng cấu trúc:\n", NF.round(2).to_string())

# ------------------------------------------------------------------ thí nghiệm kiểm chứng (mảng ngẫu nhiên mới ở mỗi lượt)
vf = sorted(glob.glob(R + "/raw_validation_jvm*.csv"))
if vf:
    V = pd.concat([pd.read_csv(f) for f in vf], ignore_index=True); V["ms"] = V.time_ns / 1e6
    V = V[V.groupby(["jvm", "round", "n"]).gc.transform("sum") == 0]
    V["ref"] = V.groupby(["jvm", "round", "n"]).ms.transform("median"); V["rel"] = V.ms / V.ref
    vrows = []; vt = []
    VC = sorted(V.cutoff.unique())
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    for ax, n in zip(axs, sorted(V.n.unique())):
        g = V[V.n == n]; piv = g.pivot_table(index=["jvm", "round"], columns="cutoff", values="rel")
        med = piv.median(); bestv = int(med.idxmin()); cis = {c: boot_ci(piv[c].values) for c in VC}
        for c in VC:
            d = piv[c] - piv[bestv]
            p = stats.wilcoxon(d).pvalue if c != bestv else np.nan
            vrows.append(dict(n=n, cutoff=c, samples=len(piv), median_ms=g[g.cutoff == c].ms.median(), median_rel=med[c],
                              ci_lo=cis[c][0], ci_hi=cis[c][1], regret_pct=100 * (med[c] / med.min() - 1), p_vs_best=p))
        ax.errorbar(VC, [med[c] for c in VC], yerr=[[med[c] - cis[c][0] for c in VC], [cis[c][1] - med[c] for c in VC]], fmt="o-", capsize=3)
        ax.set_xscale("log", base=2); ax.set_xticks(VC); ax.set_xticklabels(VC); ax.set_xlabel("CUTOFF"); ax.set_ylabel("thời gian tương đối")
        ax.set_title(f"N={n:,} (tốt nhất: {bestv})", fontsize=12)
    fig.suptitle("Hình 8. Kiểm chứng độc lập: 48 mảng ngẫu nhiên mới cho mỗi N", fontsize=13)
    fig.tight_layout(); fig.savefig(CH + "/chart8_validation.png", dpi=170); plt.close(fig)
    VR = pd.DataFrame(vrows); VR.round(4).to_csv(R + "/validation_summary.csv", index=False)
    print("\n== Kiểm chứng:\n", VR.round(3).to_string())

# ------------------------------------------------------------------ in tóm tắt
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print("\n== Mẫu/ô (dataset,cutoff):", S.samples.min(), "-", S.samples.max())
print(B[["dataset", "n", "best_cutoff", "best_median_ms", "gain_vs_c1_pct", "regret_c7_pct", "regret_c10_pct", "p_holm_best_vs_7", "p_holm_best_vs_10", "plateau_not_sig_diff", "within_1pct"]].to_string())
print("\n", OV.round(2).to_string())
print("\n", pd.DataFrame(fit_rows).round(3).to_string())
with open(R + "/analysis_meta.txt", "w") as f:
    f.write(f"samples_total={n_all}\nsamples_dropped_gc={n_drop}\nminimax_cutoff={best_minimax}\nmean_regret_cutoff={best_mean}\n")
