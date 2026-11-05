"""Build and execute notebooks/FUSION_EVIDENCE_REPORT.ipynb (outputs embedded)."""
import contextlib, io, json, sys, time, traceback
from pathlib import Path

OUT = Path("/Users/apple/study/DACNTT/notebooks/FUSION_EVIDENCE_REPORT.ipynb")
cells = []
md = lambda s: cells.append(("markdown", s.strip("\n")))
code = lambda s: cells.append(("code", s.strip("\n")))

md("""
# SeqLogAD: notebook bằng chứng Fusion (E1 → E5-DEV)

Notebook này **in ra mọi chỉ số so sánh** dùng cho báo cáo. Có hai loại:
1. **Nạp kết quả đã lưu** của từng lần chạy GPU trên RunPod: E1, E1.1, E2C, E3, E4. Mỗi file kèm sha256.
2. **Tính lại trực tiếp** từ điểm thật lưu trên máy (E5-DEV, tức cohort E4) bằng CPU: chỉ số của từng expert, các luật fusion, baseline bài báo, bootstrap CI.

**Phân loại bằng chứng (đọc kỹ trước khi trích vào báo cáo):**

| Nhãn | Ý nghĩa |
|---|---|
| ✅ XÁC NHẬN | Đã đăng ký trước, chạy trên dữ liệu mới, đạt sau hiệu chỉnh Holm |
| ❌ BÁC BỎ | Đã đăng ký trước nhưng không đạt |
| 🔎 KHÁM PHÁ | Phân tích sau khi đã thấy dữ liệu. Chỉ là giả thuyết, cần kiểm trên tập mới |

**Chỉ số:**
- AP (PR-AUC) là chỉ số chính.
- Kèm AUROC, và Precision / Recall / F1 khi gắn cờ top 1% và top 5% (không cần nhãn để chọn ngưỡng).
- CI 95%: bootstrap cụm theo khối 64 unit liên tiếp, seed 42.

**Lưu ý:** toàn bộ đánh giá dùng **nhãn source** (đoạn MID của BGL/HDFS). Chưa mở nhãn hệ đích.
""")

code(r'''
import gzip, hashlib, json, sys, tempfile, time, zipfile
from pathlib import Path
import numpy as np

REPO = Path("/Users/apple/study/DACNTT")              # sửa nếu chạy ở máy khác
DATA = Path("/Users/apple/study/seqlogad-fusion")
EV = REPO / "docs/fusion/evidence"
sys.path.insert(0, str(REPO / "src"))
from seqlogad.fusion import rules
from seqlogad.fusion.calibration import transductive_pvalues as tp
from seqlogad.fusion.evaluate import single_metrics, unit_table
from seqlogad.fusion.metrics import average_precision as ap, cluster_bootstrap, summarize_interval
from seqlogad.fusion.units import build_cohort

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def f1(p, r): return 0.0 if p + r == 0 else 2 * p * r / (p + r)
def table(headers, rows):
    rows = [[("%.3f" % v) if isinstance(v, float) else str(v) for v in r] for r in rows]
    w = [max(len(str(h)), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print(" | ".join(str(h).ljust(w[i]) for i, h in enumerate(headers)))
    print("-+-".join("-" * x for x in w))
    for r in rows: print(" | ".join(c.ljust(w[i]) for i, c in enumerate(r)))
def mrow(name, m):
    a1, a5 = m["at_1pct"], m["at_5pct"]
    return [name, m["average_precision"], m["auroc"], a1["precision"], a1["recall"], f1(a1["precision"], a1["recall"]),
            a5["precision"], a5["recall"], f1(a5["precision"], a5["recall"])]
MH = ["phương pháp", "AP", "AUROC", "P@1%", "R@1%", "F1@1%", "P@5%", "R@5%", "F1@5%"]
def ci(x): return f"{x['point']:+.3f} [{x['ci_low']:+.3f}, {x['ci_high']:+.3f}] p={x['one_sided_p_le_0']:.4f}"
print("python", sys.version.split()[0], "| numpy", np.__version__, "| chạy lúc", time.strftime("%Y-%m-%d %H:%M:%S"))
''')

md("## 0. Nguồn gốc và toàn vẹn dữ liệu (sha256)")
code(r'''
files = {
 "E1 summary": EV/"E1-20261023T112847Z/runs/E1-20261023T112847Z/summary.json",
 "E1.1 summary (Semantic 8 mask)": EV/"E11-20261023T130134Z/runs/E11-20261023T130134Z/summary-best-mkmean.json",
 "E2C confirm_results": EV/"E2C-20261023T143258Z/runs/E2C-20261023T143258Z/confirm_results.json",
 "E3 block_results": EV/"E3H-20261023T161559Z/block_results.json",
 "E3 paper baselines": EV/"E3H-20261023T161559Z/e3_paper_baselines.json",
 "E3 DeepLog": EV/"E3H-20261023T161559Z/e3_deeplog.json",
 "E4 results": EV/"E4-20261023T180203Z/runs/E4-results-20261023T180203Z.json",
 "E4 D-20 diag": EV/"E4-20261023T180203Z/runs/E4-D20-dedupe-diag.json",
 "E5-DEV điểm rút gọn": DATA/"runs/E5DEV/E5DEV-compact.json.gz",
 "Prereg E4": REPO/"docs/fusion/FUSION_E4_GATED_PREREG.md",
 "Kế hoạch E5-DEV": REPO/"docs/fusion/FUSION_E5_DEV_PLAN.md",
}
table(["file", "sha256 (16 ký tự đầu)", "KB"], [[k, sha(p)[:16], round(p.stat().st_size / 1024)] for k, p in files.items()])
pods = [("E1 / E1.1", "v9v82clkksqjhv, a3xfs2sf1zj0fu (đã xoá)"), ("E2C", "9cl3v8246zip6x"), ("E3", "qgt8q0e3unb5w4"),
        ("DeepLog E3", "b62vqjcta0kdnl"), ("E4", "dar52u92uqpe7r"), ("E5-DEV", "uyay13h1ka5dtt")]
print(); table(["thí nghiệm", "pod RunPod (A40 Secure)"], pods)
''')

md(r"""
## A. FUSION BẰNG CÁCH NÀO (phương pháp, ghi đầy đủ)

**Loại fusion:** *late fusion* ở mức điểm (score-level, decision-level), **không cần train** và **không dùng nhãn**. Hai expert dùng chung Llama-3.1-8B NF4 đóng băng, mỗi expert có adapter LoRA riêng, cũng đóng băng. Fusion không sửa trọng số mô hình nào. Lý do chọn cách này: đề tài là zero-label, nên không có nhãn hệ đích để train một mạng fusion (xem D-05, D-14 trong nhật ký quyết định).

### Bước 1: mỗi expert chấm từng dòng log (điểm bất thường = NLL)
- **Sequence expert** (V13R1, rsLoRA r16). Đầu vào là tối đa 8 dòng log đứng trước cùng group/block, kèm dòng đang xét. Điểm $s_{seq}$ là NLL trung bình theo token của **dòng đang xét, khi biết ngữ cảnh**. Điểm cao nghĩa là dòng này "không hợp" với chuỗi trước nó.
- **Semantic expert** (P2.1, LoRA r16). Đầu vào là **một câu log duy nhất**, bị che khoảng 15% số từ (`[MASK]`); mô hình phải khôi phục cả câu. Điểm $s_{sem}$ là NLL trung bình khi khôi phục. Mỗi câu được chấm với **8 mẫu che khác nhau** (seed 42..49) rồi lấy trung bình (E1.1, D-17).
- **Biến thể Semantic:**
  - (i) *lọc định danh*: không tính NLL ở những từ có ≥ 3 chữ số (`fusion/volatile.py`, D-22).
  - (ii) 🔎 *chỉ câu hiếm*: chỉ giữ điểm Semantic cho câu xuất hiện dưới 100 lần trong SOURCE_TRAIN; câu phổ biến nhận điểm thấp nhất (D-23).
- **Dedupe:** encoding giống hệt nhau chỉ chấm 1 lần rồi sao chép kết quả. Đã kiểm sai lệch không đáng kể (D-20).

### Bước 2: gộp các dòng về đơn vị đánh giá (unit)
- **BGL:** 1 unit là 1 dòng.
- **HDFS:** 1 unit là 1 block. Điểm block = **max** điểm các dòng trong block (đăng ký trước ở E3). Top-3-mean và mean chỉ là khám phá.

### Bước 3: đưa hai điểm về cùng thang (calibration không nhãn)
NLL của hai expert có thang khác nhau, nên mỗi điểm được đổi thành **p-value đuôi phải theo thứ hạng (ECDF, mid-rank)** trên chính cohort đang chấm (transductive):
$$p_i = \frac{\#\{j: s_j > s_i\} + \tfrac12\#\{j \ne i: s_j = s_i\} + 1}{N + 1}$$
p nhỏ nghĩa là bất thường hơn. Bước này không dùng nhãn.

### Bước 4: luật gộp hai p-value thành một điểm cuối
Điểm cuối càng lớn càng bất thường, và luôn được đổi dấu thành $-\log(\cdot)$.

| Luật | Công thức | Tính chất |
|---|---|---|
| **Vovk–Wang (VW)**, trung bình | $-\log\big(\tfrac{p_{seq}+p_{sem}}{2}\big)$ | Kiểu **AND**: cần cả hai cùng nghi ngờ. Hợp lệ với mọi phụ thuộc (Vovk & Wang, Biometrika 2020) |
| **Cauchy** | $T=\tfrac12\tan((0{,}5-p_{seq})\pi)+\tfrac12\tan((0{,}5-p_{sem})\pi)$ | Gần kiểu **OR**: bị chi phối bởi p nhỏ nhất (Liu & Xie, JASA 2020) |
| **max / min-p** (Bonferroni) | $-\log\big(2\min(p_{seq},p_{sem})\big)$ | **OR** thuần: lấy expert nào báo mạnh hơn |
| **Trung bình tổng quát** $M_{r,w}$ | $-\log\big((w\,p_{seq}^r+(1-w)\,p_{sem}^r)^{1/r}\big)$ | r = 1 là VW, r = −1 là harmonic, r → −∞ là min. w là trọng số của Sequence |
| Fisher, Stouffer, copula | các công thức chuẩn | Chỉ dùng ở E1 |
| **Cổng tail-lift** (E4) | mở khi top-5% của hai expert trùng nhau ≥ 2 lần mức ngẫu nhiên **và** p hoán vị < 0,01; mở thì dùng VW, đóng thì dùng Sequence | ❌ đã bị bác bỏ |

### Bước 5: báo động và đánh giá
- Gắn cờ top 1% / top 5% điểm cuối (ngân sách cảnh báo, không dùng nhãn).
- Chỉ sau khi mọi điểm đã cố định mới mở **nhãn source** để tính AP, AUROC, P, R, F1, kèm bootstrap cụm.

### So với baseline bài báo
Cài lại theo cùng protocol: train trên SOURCE_TRAIN, chấm trên đúng các unit ở trên.
- PCA (Xu et al., SOSP 2009)
- Isolation Forest (Liu et al., ICDM 2008)
- DeepLog (Du et al., CCS 2017): LSTM dự đoán mẫu log kế tiếp
- kNN TF-IDF (kiểu K4)
- B0: −log tần suất câu log
""")

code(r'''
# Mã nguồn THẬT của các hàm fusion đã dùng (in ra để làm bằng chứng)
import inspect
from seqlogad.fusion import calibration, gate, rules as R
for fn in (calibration.transductive_pvalues, R.vovk_wang_score, R.cauchy_score, R.bonferroni_min_score,
           R.generalized_mean_score, gate.tail_lift, gate.is_open, gate.gated_score):
    print("=" * 100); print(f"{fn.__module__}.{fn.__name__}"); print("=" * 100); print(inspect.getsource(fn))
''')

code(r'''
# Ví dụ minh hoạ từng bước trên 6 dòng log giả (không phải dữ liệu thật)
s_seq = np.array([0.10, 0.12, 0.11, 2.50, 0.13, 0.90])   # Bước 1: NLL của Sequence
s_sem = np.array([0.40, 0.42, 3.10, 0.45, 0.41, 2.80])   # Bước 1: NLL của Semantic
p_seq, p_sem = tp(s_seq), tp(s_sem)                      # Bước 3: p-value theo thứ hạng
table(["dòng", "NLL seq", "NLL sem", "p_seq", "p_sem", "VW", "Cauchy", "max/min-p", "Harmonic"],
      [[i, float(s_seq[i]), float(s_sem[i]), float(p_seq[i]), float(p_sem[i]),
        float(R.vovk_wang_score(p_seq, p_sem)[i]), float(R.cauchy_score(p_seq, p_sem)[i]),
        float(R.bonferroni_min_score(p_seq, p_sem)[i]), float(R.generalized_mean_score(p_seq, p_sem, -1.0)[i])]
       for i in range(6)])
print("\nDòng 3: chỉ Sequence báo. Dòng 2: chỉ Semantic báo. Dòng 5: cả hai cùng nghi ngờ vừa phải.")
print("VW xếp dòng 5 (cả hai cùng nghi) cao; max/min-p xếp dòng 2, 3 (một bên báo rất mạnh) cao nhất.")
''')

md("""
## 1. Checkpoint được nạp đúng (parity anchor)
Mỗi lần chạy GPU, Sequence adapter phải tái lập AUROC/AP đã ghi lúc chọn checkpoint, với |Δ| ≤ 0,01. Nếu không đạt thì lần chạy bị dừng (fail-closed).
""")
code(r'''
rows = []
for exp, p in [("E2C", EV/"E2C-20261023T143258Z/runs/E2C-20261023T143258Z/confirm_manifest.json"),
               ("E3", EV/"E3H-20261023T161559Z/confirm_manifest.json"),
               ("E4-BGL", EV/"E4-20261023T180203Z/runs/E4-BGL-20261023T180203Z/confirm_manifest.json"),
               ("E4-HDFS", EV/"E4-20261023T180203Z/runs/E4-HDFS-20261023T180203Z/confirm_manifest.json"),
               ("E5DEV-BGL", EV/"E5DEV-20261024T031025Z/runs/E5DEV-BGL-20261024T031025Z/confirm_manifest.json"),
               ("E5DEV-HDFS", EV/"E5DEV-20261024T031025Z/runs/E5DEV-HDFS-20261024T031025Z/confirm_manifest.json")]:
    for run, per in load(p)["anchor"].items():
        for arch, v in per.items():
            rows.append([exp, run.replace("P2.2-DEVELOPMENT-", ""), arch, v["recorded"]["auroc"], v["reproduced"]["auroc"],
                         v["recorded"]["average_precision"], v["reproduced"]["average_precision"], "PASS" if v["pass"] else "FAIL"])
table(["lần chạy", "adapter", "arch", "AUROC ghi", "AUROC lại", "AP ghi", "AP lại", "kết quả"], rows)
''')

md("""
## 2. E1 và E1.1: fusion lần đầu và Semantic chấm 8 mask (cohort chọn checkpoint)
Cohort ở đây gồm 1.536 unit (đã bỏ 512 unit dùng để chọn checkpoint). HDFS chỉ chấm khoảng 1 cửa sổ mỗi block.
- E1 là kết quả chính và là **❌ BÁC BỎ**: Cauchy(Sem, Seq) có gain âm.
- E1.1 là **🔎 KHÁM PHÁ**.
""")
code(r'''
names = [("sequence_{t}_best", "Sequence"), ("semantic_{t}_best", "Semantic"), ("b0_frequency", "B0 tần suất"),
         ("cauchy", "Cauchy(Sem,Seq)"), ("vovk_wang_mean", "VW(Sem,Seq)"), ("bonferroni_min", "max/min-p(Sem,Seq)"),
         ("sequence_plus_b0_vw", "VW(Seq,B0)")]
cols = [("hdfs_bgl", "hdfs", "BGL@fold-HDFS"), ("hadoop_bgl", "hadoop", "BGL@fold-Hadoop"), ("hadoop_hdfs", "hadoop", "HDFS@fold-Hadoop")]
for title, p in [("E1 (Semantic 1 mask)", files["E1 summary"]), ("E1.1 (Semantic trung bình 8 mask)", files["E1.1 summary (Semantic 8 mask)"])]:
    s = load(p); print("\n###", title, "— AP")
    table(["phương pháp"] + [c[2] for c in cols],
          [[label] + [s.get(f"{pre}_ap_{key.format(t=tag)}", float("nan")) for pre, tag, _ in cols] for key, label in names])
''')

md("""
## 3. E2C: kiểm lại trên cohort độc lập (đăng ký trước)
BGL có 2.048 dòng (89 bất thường). HDFS có 1.969 block (18 bất thường).
- **✅ H1** VW(Seq, B0) tốt hơn cả hai thành phần trên BGL, ở cả 2 fold.
- **❌ H2** VW(Sem-8mask, Seq) không đạt.
""")
code(r'''
e2c = load(files["E2C confirm_results"])
for key, r in e2c["results"].items():
    print(f"\n### {key}  units={r['units']} positives={r['positives']}")
    table(MH, [mrow(n, m) for n, m in r["metrics"].items()])
    for t, v in r["tests"].items(): print(f"  {t:28s} {ci(v)}")
print("\nHolm, họ chính:", e2c["primary_family_holm"]["rejected_at_0.05"])
print("H4 không kém:", e2c["H4_noninferiority"])
''')

md("""
## 4. E3: HDFS chấm mọi dòng trong block, và baseline bài báo
3.000 block, 65 bất thường. Tổng hợp chính là block-max.
- **✅ H5a/H5b/H6** đạt (Holm).
- **✅ H7** không kém.
- Phần baseline bài báo ở đây là so sánh không ghép cặp.
""")
code(r'''
e3 = load(files["E3 block_results"]); b3 = load(files["E3 paper baselines"]); d3 = load(files["E3 DeepLog"])
for agg in ("max", "top3", "mean"):
    print(f"\n### HDFS block-{agg}" + ("  (CHÍNH, đăng ký trước)" if agg == "max" else "  (khám phá)"))
    rows = [mrow(k.split("@")[0], m) for k, m in e3["metrics"].items() if k.endswith("@" + agg)]
    rows += [mrow(k.split("@")[0], m) for k, m in b3["metrics"].items() if k.endswith("@" + agg) and not k.startswith("b0")]
    rows += [mrow(k.split("@")[0], m) for k, m in d3["metrics"].items() if k.endswith("@" + agg)]
    table(MH, rows)
print("\nKiểm định:"); [print(f"  {t:32s} {ci(v)}") for t, v in e3["tests"].items()]
print("Holm H5-H6:", e3["primary_family_holm"], "| H7 không kém:", e3["H7_noninferior"])
print(f"Thời gian chạy: DeepLog {d3['seconds']:.1f}s trên {d3['device']}; PCA {b3['seconds']['pca_xu2009']:.1f}s, kNN {b3['seconds']['knn_tfidf_k4']:.1f}s trên CPU")
''')

md("""
## 5. E4: fusion có cổng chọn không dùng nhãn (đăng ký trước, cohort mới)
BGL có 16.384 dòng (688 bất thường) ở 2 fold. HDFS có 3.000 block (81 bất thường).

**❌ Kết quả chính bị BÁC BỎ:** cổng tail-lift chọn sai ở 2/3 cohort.
""")
code(r'''
e4 = load(files["E4 results"])
for name, c in e4["cohorts"].items():
    g = c["gate"]
    print(f"\n### {name}  units={c['units']} positives={c['positives']}  | cổng lift={g['statistic']['lift']:.2f} "
          f"p={g['statistic']['p_value']:.4f} → {'MỞ' if g['open']['primary'] else 'ĐÓNG'}")
    table(MH, [mrow(n, m) for n, m in c["metrics"].items()])
    for t, v in c["tests"].items(): print(f"  {t:34s} {ci(v)}")
    print("  Fusion có cổng so với baseline (ΔAP, ghép cặp):"); [print(f"     vs {b:16s} {ci(v)}") for b, v in c["vs_baselines"].items()]
    print("  Sequence so với baseline (ΔAP, ghép cặp):"); [print(f"     vs {b:16s} {ci(v)}") for b, v in c["sequence_vs_baselines"].items()]
print("\nH8 (cổng đoán đúng):", e4["H8_gate_prediction"])
print("Holm, họ chính:", e4["primary_family_holm"])
print("Kiểm tra dedupe D-20:", json.dumps(load(files["E4 D-20 diag"]), indent=0)[:600])
''')

md("""
## 6. E5-DEV: tính lại TRỰC TIẾP từ điểm thật (cohort E4, CPU)
Phần này đọc điểm từng cửa sổ, tải về từ pod `uyay13h1ka5dtt`, rồi tính lại mọi chỉ số trước mắt bạn.
- Các biến thể Semantic gồm: gốc (8 mask), lọc token định danh (`semantic_template`), và **chỉ tính Semantic cho câu xuất hiện dưới 100 lần trong SOURCE_TRAIN** (🔎 KHÁM PHÁ).
- Bootstrap: 2.000 lần, seed 42.
""")
code(r'''
from collections import Counter
from seqlogad.fusion.baselines import B0, score_rows, train_messages
from seqlogad.fusion.baselines_eval import train_windows
from seqlogad.fusion.gated_eval import COHORTS, LAYOUT
from seqlogad.fusion.volatile import is_volatile
compact = json.load(gzip.open(files["E5-DEV điểm rút gọn"], "rt"))
TMP = Path(tempfile.mkdtemp(prefix="seqlogad_nb_"))      # dữ liệu train tạm, giải nén từ kit gốc
with zipfile.ZipFile(DATA / "00_inputs_immutable/inputs/phase2-sequence-s42.zip") as z:
    for f in ("FOLD-TARGET-ARCH-HDFS", "FOLD-TARGET-ARCH-HADOOP"):
        for part in ("train/windows.parquet", "metadata/events.parquet"):
            z.extract(f"phase2_sequence/folds/{f}/sequence/{part}", TMP)
ORIG = TMP / "phase2_sequence"
tmpl = lambda m: " ".join("<VOL>" if is_volatile(w) else w for w in m.split())
E5 = {}
for name, (fold, arch, tag, kind, agg) in COHORTS.items():
    run = next(k.split("/")[0] for k in compact if k.startswith(f"E5DEV-{kind.upper()}"))
    rows = [r for r in build_cohort(DATA / "00_inputs_e4" / kind / LAYOUT[kind][0], DATA / "00_inputs_e4" / kind / LAYOUT[kind][1], fold)
            if r["architecture_id"] == arch]
    count = Counter(m for _, m, _ in train_messages(ORIG, fold, arch)); tcount = Counter(tmpl(m) for m in count.elements())
    seq, sem = compact[f"{run}/sequence_{tag}_best"], compact[f"{run}/semantic_{tag}_best_mkmean"]
    floor = float(np.nanmin([v for v in sem.values() if v is not None]))
    W = {"Sequence": seq, "Semantic (8 mask)": sem,
         "Semantic lọc định danh": compact[f"{run}/semantic_template_{tag}_best_mkmean"],
         "Semantic chỉ câu hiếm<100 🔎": {r["window_id"]: (sem[r["window_id"]] if count[r["target_message"]] < 100 else floor) for r in rows},
         "Độ hiếm mẫu câu (B0-template) 🔎": {r["window_id"]: -np.log(tcount[tmpl(r["target_message"])] + 0.5) for r in rows}}
    W = {k: {w: (np.nan if v is None else v) for w, v in s.items()} for k, s in W.items()}
    t, _ = unit_table(rows, W, agg); y = t["anomaly"]; p = {k: tp(t[k]) for k in W}
    F = {"VW(Seq, Sem)": rules.vovk_wang_score(p["Sequence"], p["Semantic (8 mask)"]),
         "Cauchy(Seq, Sem)": rules.cauchy_score(p["Sequence"], p["Semantic (8 mask)"]),
         "Harmonic(Seq, Sem)": rules.generalized_mean_score(p["Sequence"], p["Semantic (8 mask)"], -1.0),
         "max/min-p(Seq, Sem)": rules.bonferroni_min_score(p["Sequence"], p["Semantic (8 mask)"]),
         "VW(Seq, Sem câu hiếm) 🔎": rules.vovk_wang_score(p["Sequence"], p["Semantic chỉ câu hiếm<100 🔎"]),
         "VW(Seq, B0-template) 🔎": rules.vovk_wang_score(p["Sequence"], p["Độ hiếm mẫu câu (B0-template) 🔎"])}
    E5[name] = dict(rows=rows, table=t, y=y, scores={**{k: t[k] for k in W}, **F}, agg=agg)
    print(f"\n### {name}  units={y.size} positives={int(y.sum())} (unit = {'block, max' if agg == 'max' else 'dòng'})")
    table(MH, [mrow(k, single_metrics(y, s, [0.01, 0.05])) for k, s in {**{k: t[k] for k in W}, **F}.items()])
''')

md("""
### 6b. Fusion gain so với expert tốt nhất (ΔAP, bootstrap ghép cặp, CI 95%)
Gain = AP(fusion) − max(AP(Sequence), AP(thành phần còn lại)).
- Tiêu chí "fusion thành công": gain > 0 trên BGL **và** không tụt quá 0,02 trên HDFS.
""")
code(r'''
pairs = [("VW(Seq, Sem)", "Semantic (8 mask)"), ("Cauchy(Seq, Sem)", "Semantic (8 mask)"),
         ("Harmonic(Seq, Sem)", "Semantic (8 mask)"), ("max/min-p(Seq, Sem)", "Semantic (8 mask)"),
         ("VW(Seq, Sem câu hiếm) 🔎", "Semantic chỉ câu hiếm<100 🔎"), ("VW(Seq, B0-template) 🔎", "Độ hiếm mẫu câu (B0-template) 🔎")]
rows = []
for fused, other in pairs:
    r = [fused]
    for name, e in E5.items():
        y, s = e["y"], e["scores"]; cl = np.array([f"c{i // 64:03d}" for i in range(y.size)])
        sc = {"f": s[fused], "a": s["Sequence"], "b": s[other]}
        st = lambda yy, q: ap(yy, q["f"]) - max(ap(yy, q["a"]), ap(yy, q["b"]))
        iv = summarize_interval(cluster_bootstrap(y, sc, cl, st, reps=2000, seed=42), st(y, sc))
        r.append(f"{iv['point']:+.3f} [{iv['ci_low']:+.3f},{iv['ci_high']:+.3f}]")
    rows.append(r)
table(["fusion"] + list(E5), rows)
''')

md("""
## 7. So với baseline bài báo, TÍNH LẠI trên cùng cohort (E4/E5-DEV)
- PCA (Xu, SOSP'09), Isolation Forest (Liu, ICDM'08), kNN TF-IDF (kiểu K4) và B0: train trên SOURCE_TRAIN của đúng fold (tối đa 32.768 cửa sổ), chấm trên đúng các unit ở trên.
- DeepLog (Du, CCS'17) cần torch, nên lấy số đã chạy trên GPU ở E4 (cùng cohort), kèm CI ghép cặp đã lưu.
""")
code(r'''
from seqlogad.fusion.paper_baselines import Vocab, count_matrix, pca_scores, iforest_scores, knn_tfidf_scores
for name, (fold, arch, tag, kind, agg) in COHORTS.items():
    e = E5[name]; rows = e["rows"]; t0 = time.time()
    train = train_windows(ORIG, fold, arch); test = [(r["context_messages"], r["target_message"]) for r in rows]
    vocab = Vocab([m for c, x in train for m in [*c, x]]); tr, te = count_matrix(train, vocab), count_matrix(test, vocab)
    raw = {"PCA (SOSP'09)": pca_scores(tr, te), "Isolation Forest (ICDM'08)": iforest_scores(tr, te),
           "kNN TF-IDF (K4)": knn_tfidf_scores([x for _, x in train], [x for _, x in test])}
    b0 = score_rows(B0(train_messages(ORIG, fold, arch)), rows)
    W = {k: {r["window_id"]: float(v) for r, v in zip(rows, vals)} for k, vals in raw.items()}
    W["B0 tần suất"] = {w: v["b0_frequency"] for w, v in b0.items()}
    bt, _ = unit_table(rows, W, agg); y = e["y"]
    assert list(bt["unit_id"]) == list(e["table"]["unit_id"]), "lệch unit"
    best_fused = "VW(Seq, Sem câu hiếm) 🔎"
    print(f"\n### {name}  (baseline tính trong {time.time() - t0:.0f}s, CPU)")
    dl = e4["cohorts"][name]["metrics"]["deeplog_du2017"]
    mets = [mrow("Sequence (của mình)", single_metrics(y, e["scores"]["Sequence"], [0.01, 0.05])),
            mrow("Semantic (của mình)", single_metrics(y, e["scores"]["Semantic (8 mask)"], [0.01, 0.05])),
            mrow(best_fused, single_metrics(y, e["scores"][best_fused], [0.01, 0.05])),
            mrow("DeepLog (CCS'17) [E4 GPU]", dl)]
    mets += [mrow(k, single_metrics(y, bt[k], [0.01, 0.05])) for k in W]
    table(MH, mets)
    cl = np.array([f"c{i // 64:03d}" for i in range(y.size)])
    print("  ΔAP ghép cặp, CI 95%:")
    for k in W:
        for mine in ("Sequence", best_fused):
            sc = {"m": e["scores"][mine], "b": bt[k]}; st = lambda yy, q: ap(yy, q["m"]) - ap(yy, q["b"])
            iv = summarize_interval(cluster_bootstrap(y, sc, cl, st, reps=2000, seed=42), st(y, sc))
            print(f"     {mine:28s} − {k:28s} {ci(iv)}")
    print(f"     {'Sequence':28s} − {'DeepLog (E4, đã lưu)':28s} {ci(e4['cohorts'][name]['sequence_vs_baselines']['deeplog_du2017'])}")
''')

md("""
## 8. Tóm tắt cho báo cáo (nhãn bằng chứng đã kiểm lại theo bản đăng ký trước)

**Kiểm chéo:** baseline tính lại trên CPU ở mục 7 ra **đúng y** số chạy trên pod ở E4 (PCA 0,122; IForest 0,040; kNN 0,168 / 0,026; B0 0,113 / 0,026). Hai bên chấm cùng unit và cùng protocol.

| # | Kết luận | Nhãn | Bằng chứng |
|---|---|---|---|
| 1 | Chấm cả block HDFS (block-max) tốt hơn chấm 1 dòng: +0,42 AP | ✅ H6 (E3) | Mục 4 |
| 2 | VW(Seq, B0) tốt hơn cả hai thành phần trên BGL, ở 2 fold | ✅ H1 (E2C) | Mục 3 |
| 3 | Fusion có cổng trên BGL@Hadoop (cổng mở, tức VW(Seq, Sem)) hơn **mọi** baseline: DeepLog, PCA, IForest, kNN, B0 | ✅ họ phụ E4, Holm | Mục 5 |
| 4 | Trên HDFS, Sequence hơn DeepLog +0,16 AP [+0,07; +0,25] và hơn PCA, IForest, kNN, B0 từ +0,44 đến +0,68 | 🔎 khám phá trong E4 (CI loại trừ 0) | Mục 5, 7 |
| 5 | Trên BGL, Sequence **một mình không hơn rõ** DeepLog, PCA, kNN (CI chứa 0; kNN còn cao hơn về điểm) | trung thực, ghi rõ | Mục 7 |
| 6 | Fusion Cauchy(Sem, Seq) ở E1 | ❌ | Mục 2 |
| 7 | VW(Sem-8mask, Seq) trên BGL: +0,08 đến +0,10 (4/4 lần đo dương, 1 lần có CI > 0) | ❌ H2 chưa đạt; 🔎 | Mục 3, 5, 6b |
| 8 | Cổng chọn tail-lift không nhãn | ❌ (E4) | Mục 5 |
| 9 | VW(Seq, Semantic chỉ câu hiếm): BGL +0,116 / +0,108 (CI > 0), HDFS −0,001; hơn mọi baseline trên BGL | 🔎 cần kiểm trên tập mới | Mục 6b, 7 |
| 10 | Phần lớn lợi ích ở mục 9 đến từ thông tin tần suất (ablation B0-template cũng tốt ngang) | 🔎 | Mục 6b |
""")

# ---------- execute ----------
ns, nb_cells, n = {}, [], 0
for kind, src in cells:
    if kind == "markdown":
        nb_cells.append({"cell_type": "markdown", "metadata": {}, "source": src.splitlines(True)})
        continue
    n += 1
    buf = io.StringIO(); t0 = time.time(); outputs = []
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            exec(compile(src, f"<cell {n}>", "exec"), ns)
    except Exception:
        outputs.append({"output_type": "error", "ename": "Error", "evalue": "see traceback",
                        "traceback": traceback.format_exc().splitlines()})
        print(f"cell {n} FAILED", file=sys.stderr); print(traceback.format_exc(), file=sys.stderr)
    text = buf.getvalue()
    if text:
        outputs.insert(0, {"output_type": "stream", "name": "stdout", "text": text.splitlines(True)})
    nb_cells.append({"cell_type": "code", "execution_count": n, "metadata": {}, "outputs": outputs,
                     "source": src.splitlines(True)})
    print(f"cell {n} done in {time.time() - t0:.1f}s, {len(text)} chars", file=sys.stderr)
    if outputs and outputs[-1]["output_type"] == "error":
        break
nb = {"nbformat": 4, "nbformat_minor": 5, "cells": nb_cells,
      "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                   "language_info": {"name": "python", "version": sys.version.split()[0]}}}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1))
print("WROTE", OUT, file=sys.stderr)
