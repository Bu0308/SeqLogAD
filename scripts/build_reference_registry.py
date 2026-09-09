"""Build docs/references/reference_registry.yaml (Excel-anchored reference registry).

The `used_by` task lists for the workbook's S1-S11 are derived from
`configs/plan/excel-roadmap-v1.yaml`, not hand-maintained, so they cannot drift from
the workbook. Verified bibliographic metadata is held in this file and was confirmed
against Crossref, the arXiv API and the Zenodo record API on the dates recorded.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import yaml

REGISTRY = "docs/references/reference_registry.yaml"
ACTIVE_MD = "docs/references/ACTIVE_REFERENCES.md"

# Human-readable grouping. Every ACTIVE source must appear in exactly one section,
# and the renderer fails if one is unassigned.
SECTIONS = [
    ("Dataset / log sources", ["S1", "S16", "S12", "S13", "S14", "S15"]),
    ("Parsing / normalization", ["S2", "S17"]),
    ("Cross-system protocol / domain shift", ["S3", "S4"]),
    ("LLM / representation", ["S5", "S11"]),
    ("LoRA / parameter-efficient tuning", ["S7"]),
    ("Graph / temporal expert", ["S6"]),
    ("Adaptation / calibration / uncertainty", ["S8"]),
    ("Fusion / abstention", ["S9"]),
    ("Baselines", ["S10"]),
]

RELEVANCE = {
    "S1": "Provenance and architecture diversity of the four active corpora.",
    "S2": "Fixed-depth-tree log parsing; the optional auxiliary template field only.",
    "S3": "Published evidence that cross-system domain-invariant representation is a live direction.",
    "S4": "Design reference for the zero-label target protocol.",
    "S5": "Design reference for LLaMA-family next-log modelling.",
    "S6": "Graph features over log entities for cross-system detection.",
    "S7": "Frozen base plus separate low-rank adapters.",
    "S8": "Adversarial domain adaptation, enabled only after a pre-declared diagnostic.",
    "S9": "Abstention with an explicit reject option and risk-coverage framing.",
    "S10": "Explicit unsupervised anomaly baseline for P3.6.",
    "S11": "Llama-3.1-8B revision, tokenizer and licence provenance.",
    "S12": "Origin and block-trace labelling of HDFS_v1.",
    "S13": "Origin of the BGL log and its inline alert markers.",
    "S14": "Origin of the Hadoop corpus and its injected-failure labels.",
    "S15": "Origin of the OpenStack capture and its anomalous-instance labels.",
    "S16": "Download source, CC-BY-4.0 licence and published MD5 digests.",
    "S17": "Official Drain3 implementation pinned at 0.9.11.",
}
ROADMAP = "configs/plan/excel-roadmap-v1.yaml"
VERIFIED_ON = "2026-09-07"

# Verified metadata. Every field below was returned by an authoritative service;
# nothing here is inferred. `workbook_label` is what the workbook says, kept so a
# discrepancy is visible rather than silently overwritten.
SOURCES: list[dict] = [
    {
        "id": "S1", "workbook_label": "Loghub — Zhu et al. (2020)",
        "title": "Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics",
        "authors": ["Jieming Zhu", "Shilin He", "Pinjia He", "Jinyang Liu", "Michael R. Lyu"],
        "year": 2023, "venue": "IEEE International Symposium on Software Reliability Engineering (ISSRE)",
        "doi": "10.1109/ISSRE59848.2023.00071", "arxiv": "2008.06448",
        "official_url": "https://doi.org/10.1109/ISSRE59848.2023.00071",
        "preprint_url": "https://arxiv.org/abs/2008.06448",
        "repo_url": "https://github.com/logpai/loghub",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref + arXiv API",
        "note": (
            "The workbook cites the 2020 arXiv preprint. The peer-reviewed ISSRE 2023 "
            "version is the stronger source for the same claim and is recorded as "
            "canonical; the preprint URL is retained because the workbook uses it."
        ),
        "claims": [
            {"claim": "Loghub distributes the HDFS, BGL, Hadoop and OpenStack corpora with documented provenance and architecture diversity.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S2", "workbook_label": "Drain — He et al. (2017)",
        "title": "Drain: An Online Log Parsing Approach with Fixed Depth Tree",
        "authors": ["Pinjia He", "Jieming Zhu", "Zibin Zheng", "Michael R. Lyu"],
        "year": 2017, "venue": "IEEE International Conference on Web Services (ICWS)",
        "doi": "10.1109/ICWS.2017.13", "arxiv": None, "pages": "33-40",
        "official_url": "https://doi.org/10.1109/ICWS.2017.13",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref",
        "claims": [
            {"claim": "Fixed-depth-tree online log parsing is an established way to derive templates from raw logs.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "SeqLogAD treats the Drain3 template as an optional auxiliary field and populates none in Phase 1.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
    },
    {
        "id": "S3", "workbook_label": "LogDLR — Liu et al. (2025)",
        "title": "LogDLR: Unsupervised Cross-System Log Anomaly Detection Through Domain-Invariant Latent Representation",
        "authors": ["Zhou", "Ying", "Wang", "Zhao"],
        "year": 2025, "venue": "IEEE Transactions on Dependable and Secure Computing",
        "doi": "10.1109/TDSC.2025.3548050", "arxiv": None,
        "official_url": "https://doi.org/10.1109/TDSC.2025.3548050",
        "source_type": "journal_article", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref title search (IEEE Xplore returns HTTP 418 to non-browser clients)",
        "correction": (
            "The workbook attributes this to 'Liu et al.'. Crossref returns the author "
            "family names Zhou, Ying, Wang, Zhao. The workbook's Xplore link resolves to "
            "the same article; the DOI is added here for durability."
        ),
        "claims": [
            {"claim": "Cross-system log anomaly detection via a domain-invariant representation is an active, published research direction.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "SeqLogAD's specific leave-one-architecture-out fold design.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
    },
    {
        "id": "S4", "workbook_label": "ZeroLog — Zhao et al. (2025)",
        "title": "ZeroLog: Zero-Label Generalizable Cross-System Log-based Anomaly Detection",
        "authors": ["Xinlong Zhao", "Tong Jia", "Minghua He", "Ying Li", "Gang Huang"],
        "year": 2025, "venue": "arXiv", "doi": None, "arxiv": "2511.05862",
        "official_url": "https://arxiv.org/abs/2511.05862",
        "source_type": "preprint", "publication_status": "PREPRINT_NOT_PEER_REVIEWED",
        "verification": "arXiv API (published 2025-11-08)",
        "claims": [
            {"claim": "A zero-label target protocol is a coherent research design for cross-system log anomaly detection.",
             "classification": "LITERATURE_INFORMED_SEQLOGAD_DECISION"},
            {"claim": "SeqLogAD's burn-in buffer rule, contamination bound and readiness minima.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
        "use_boundary": "Preprint. Design reference only; it establishes no performance for this project.",
    },
    {
        "id": "S5", "workbook_label": "LogLLaMA — Yang & Harris (2025)",
        "title": "LogLLaMA: Transformer-based log anomaly detection with LLaMA",
        "authors": ["Zhuoyi Yang", "Ian G. Harris"],
        "year": 2025, "venue": "arXiv", "doi": None, "arxiv": "2503.14849",
        "official_url": "https://arxiv.org/abs/2503.14849",
        "source_type": "preprint", "publication_status": "PREPRINT_NOT_PEER_REVIEWED",
        "verification": "arXiv API (published 2025-03-19)",
        "claims": [
            {"claim": "A LLaMA-family base model can be adapted to next-log modelling for anomaly detection.",
             "classification": "LITERATURE_INFORMED_SEQLOGAD_DECISION"},
        ],
        "use_boundary": "Uses LLaMA-2; it does not validate this project's Llama-3.1-8B choice.",
    },
    {
        "id": "S6", "workbook_label": "LogGT — Wang et al. (2024)",
        "title": "LogGT: Cross-system log anomaly detection via heterogeneous graph feature and transfer learning",
        "authors": ["Peipeng Wang", "Xiuguo Zhang", "Zhiying Cao", "Weigang Xu", "Wangwang Li"],
        "year": 2024, "venue": "Expert Systems with Applications", "volume": "251", "pages": "124082",
        "doi": "10.1016/j.eswa.2024.124082", "arxiv": None,
        "official_url": "https://doi.org/10.1016/j.eswa.2024.124082",
        "source_type": "journal_article", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref",
        "claims": [
            {"claim": "Heterogeneous graph features over log entities support cross-system anomaly detection.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "The 'GTAT' temporal-graph formulation named in the workbook.",
             "classification": "LITERATURE_INFORMED_SEQLOGAD_DECISION"},
        ],
        "reference_support_gap": "RSG-001",
    },
    {
        "id": "S7", "workbook_label": "LoRA — Hu et al. (2021)",
        "title": "LoRA: Low-Rank Adaptation of Large Language Models",
        "authors": ["Edward J. Hu", "Yelong Shen", "Phillip Wallis", "Zeyuan Allen-Zhu", "Yuanzhi Li"],
        "year": 2021, "venue": "arXiv (later ICLR 2022)", "doi": None, "arxiv": "2106.09685",
        "official_url": "https://arxiv.org/abs/2106.09685",
        "source_type": "preprint", "publication_status": "PREPRINT_LATER_PEER_REVIEWED",
        "verification": "arXiv API (v1 2021-06-17, v2 2021-10-16)",
        "claims": [
            {"claim": "A frozen base model with separate low-rank adapters is an established parameter-efficient adaptation method.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "SeqLogAD's requirement that the two adapters never share weights or checkpoints.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
    },
    {
        "id": "S8", "workbook_label": "DANN — Ganin et al. (2015)",
        "title": "Domain-Adversarial Training of Neural Networks",
        "authors": ["Yaroslav Ganin", "Evgeniya Ustinova", "Hana Ajakan", "Pascal Germain", "Hugo Larochelle"],
        "year": 2016, "venue": "Journal of Machine Learning Research, vol. 17, pp. 1-35",
        "doi": None, "arxiv": "1505.07818",
        "official_url": "https://www.jmlr.org/papers/v17/15-239.html",
        "preprint_url": "https://arxiv.org/abs/1505.07818",
        "source_type": "journal_article", "publication_status": "PEER_REVIEWED",
        "verification": "arXiv API journal_ref: 'Journal of Machine Learning Research 2016, vol. 17, p. 1-35'",
        "note": "The workbook's year 2015 is the preprint; the JMLR version is 2016. Both are recorded.",
        "claims": [
            {"claim": "Adversarial domain adaptation is an established technique for domain shift.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "SeqLogAD enables the adversarial branch only after a pre-declared diagnostic and ablation.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
    },
    {
        "id": "S9", "workbook_label": "SelectiveNet — Geifman & El-Yaniv (2019)",
        "title": "SelectiveNet: A Deep Neural Network with an Integrated Reject Option",
        "authors": ["Yonatan Geifman", "Ran El-Yaniv"],
        "year": 2019, "venue": "Proceedings of Machine Learning Research, vol. 97 (ICML)",
        "doi": None, "arxiv": None,
        "official_url": "https://proceedings.mlr.press/v97/geifman19a.html",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "PMLR URL HTTP 200",
        "claims": [
            {"claim": "Abstention with an explicit reject option and risk-coverage framing is an established formulation.",
             "classification": "LITERATURE_SUPPORTED"},
            {"claim": "SeqLogAD's specific abstain thresholds and UNKNOWN/REVIEW state.",
             "classification": "SEQLOGAD_PROTOCOL_DECISION"},
        ],
    },
    {
        "id": "S10", "workbook_label": "Isolation Forest — Liu et al. (2008)",
        "title": "Isolation Forest",
        "authors": ["Fei Tony Liu", "Kai Ming Ting", "Zhi-Hua Zhou"],
        "year": 2008, "venue": "IEEE International Conference on Data Mining (ICDM)", "pages": "413-422",
        "doi": "10.1109/ICDM.2008.17", "arxiv": None,
        "official_url": "https://doi.org/10.1109/ICDM.2008.17",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref",
        "claims": [
            {"claim": "Isolation Forest is an established unsupervised anomaly-detection baseline.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S11", "workbook_label": "Meta Llama 3.1 (2024)",
        "title": "Introducing Llama 3.1: Our most capable models to date",
        "authors": ["Meta AI"], "year": 2024, "venue": "Meta AI official release",
        "doi": None, "arxiv": None,
        "official_url": "https://ai.meta.com/blog/meta-llama-3-1/",
        "source_type": "official_vendor_documentation", "publication_status": "VENDOR_DOCUMENTATION",
        "verification": "HTTP 200",
        "claims": [
            {"claim": "Base-model revision, tokenizer and licence provenance for Llama-3.1-8B.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
        "use_boundary": "Vendor documentation, not peer-reviewed. Correct for licence and revision provenance only.",
    },
    # ---- added by this consolidation; not workbook S# but required by active work ----
    {
        "id": "S12", "title": "Detecting large-scale system problems by mining console logs",
        "authors": ["Wei Xu", "Ling Huang", "Armando Fox", "David Patterson", "Michael I. Jordan"],
        "year": 2009, "venue": "ACM SIGOPS Symposium on Operating Systems Principles (SOSP)",
        "doi": "10.1145/1629575.1629587", "arxiv": None,
        "official_url": "https://doi.org/10.1145/1629575.1629587",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref", "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.2", "ARCH-HDFS registry row", "docs/datasets/hdfs.md"],
        "claims": [
            {"claim": "Origin and block-trace labelling of the HDFS_v1 corpus.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S13", "title": "What Supercomputers Say: A Study of Five System Logs",
        "authors": ["Adam Oliner", "Jon Stearley"], "year": 2007,
        "venue": "IEEE/IFIP International Conference on Dependable Systems and Networks (DSN)",
        "doi": "10.1109/DSN.2007.103", "arxiv": None,
        "official_url": "https://doi.org/10.1109/DSN.2007.103",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref", "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.2", "ARCH-BGL registry row", "docs/datasets/bgl.md"],
        "claims": [
            {"claim": "Origin of the BGL supercomputer log and its inline alert-marker labelling.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S14", "title": "Log clustering based problem identification for online service systems",
        "authors": ["Qingwei Lin", "Hongyu Zhang", "Jian-Guang Lou", "Yu Zhang", "Xuewei Chen"],
        "year": 2016, "venue": "International Conference on Software Engineering Companion (ICSE-C)",
        "doi": "10.1145/2889160.2889232", "arxiv": None, "pages": "102-111",
        "official_url": "https://doi.org/10.1145/2889160.2889232",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref", "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.2", "ARCH-HADOOP registry row"],
        "claims": [
            {"claim": "Origin of the Hadoop WordCount/PageRank corpus and its injected-failure application labels.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S15", "title": "DeepLog: Anomaly Detection and Diagnosis from System Logs through Deep Learning",
        "authors": ["Min Du", "Feifei Li", "Guineng Zheng", "Vivek Srikumar"],
        "year": 2017, "venue": "ACM SIGSAC Conference on Computer and Communications Security (CCS)",
        "doi": "10.1145/3133956.3134015", "arxiv": None,
        "official_url": "https://doi.org/10.1145/3133956.3134015",
        "source_type": "conference_paper", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref", "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.2", "ARCH-OPENSTACK registry row"],
        "claims": [
            {"claim": "Origin of the OpenStack capture and its anomalous-VM-instance labels.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S16", "title": "Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics (dataset record)",
        "authors": ["LOGPAI"], "year": 2023, "venue": "Zenodo",
        "doi": "10.5281/zenodo.8196385", "arxiv": None,
        "official_url": "https://doi.org/10.5281/zenodo.8196385",
        "source_type": "dataset_record", "publication_status": "PUBLISHED_DATASET",
        "license": "CC-BY-4.0", "access": "open", "publication_date": "2023-07-31",
        "verification": "Zenodo record API: license cc-by-4.0, access_right open, published 2023-07-31",
        "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.2", "P1.8", "P4.6", "configs/datasets/hdfs.yaml",
                          "configs/datasets/bgl.yaml", "data/registry/dataset_registry.json"],
        "claims": [
            {"claim": "Download source, CC-BY-4.0 licence and published MD5 digests for all four active corpora.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
    {
        "id": "S17", "title": "Drain3 — official reference implementation",
        "authors": ["LOGPAI"], "year": None, "venue": "GitHub",
        "doi": None, "arxiv": None,
        "official_url": "https://github.com/logpai/Drain3",
        "repo_url": "https://github.com/logpai/Drain3",
        "source_type": "official_implementation", "publication_status": "SOFTWARE_REPOSITORY",
        "pinned_version": "0.9.11",
        "verification": "HTTP 200", "added_by": "REFERENCE-CONSOLIDATION-001",
        "extra_used_by": ["P1.4", "configs/parsing/drain3-v1.yaml",
                          "src/seqlogad/parsing/drain_parser.py"],
        "claims": [
            {"claim": "The frozen parser state and RESTORE_ONLY match semantics used for the auxiliary template field.",
             "classification": "ENGINEERING_DECISION"},
        ],
    },
]

HISTORICAL_SOURCES = [
    {
        "id": "H1", "title": "Deep learning for anomaly detection in log data: A survey",
        "authors": ["Max Landauer", "Sebastian Onder", "Florian Skopik", "Markus Wurzenberger"],
        "year": 2023, "venue": "Machine Learning with Applications, vol. 12",
        "doi": "10.1016/j.mlwa.2023.100470", "arxiv": "2207.03820",
        "official_url": "https://doi.org/10.1016/j.mlwa.2023.100470",
        "source_type": "journal_article", "publication_status": "PEER_REVIEWED",
        "verification": "Crossref + arXiv API journal_ref",
        "active_status": "HISTORICAL",
        "used_by": ["retired Day-2 reading note (deleted); retained here so the source survives the cleanup"],
        "claims": [
            {"claim": "Log anomaly-detection results depend on collection, parsing, grouping and evaluation split, so comparisons need aligned preprocessing and leakage controls.",
             "classification": "LITERATURE_SUPPORTED"},
        ],
    },
]

REFERENCE_SUPPORT_GAPS = [
    {
        "id": "RSG-001",
        "claim": "The temporal graph expert is referred to as 'GTAT' in the workbook (P2.4, EXP-GTAT-001).",
        "problem": (
            "S6 (LogGT) is a real, verified and relevant cross-system graph paper, but it "
            "presents a heterogeneous graph feature with transfer learning. It does not "
            "establish the acronym or formulation 'GTAT'."
        ),
        "affected_tasks": ["P2.4", "P2.5", "P4.3"],
        "resolution_required_before": "P2.4 write-up (specification required before training)",
        "recommended_action": (
            "Either cite the specific source of the GTAT formulation, or state plainly that "
            "GTAT is a SeqLogAD architectural decision informed by S6."
        ),
        "classification_if_unresolved": "LITERATURE_INFORMED_SEQLOGAD_DECISION",
        "methodology_changed": False,
    },
]


def build(project_root: Path) -> dict:
    roadmap = yaml.safe_load((project_root / ROADMAP).read_text(encoding="utf-8"))["roadmap"]
    workbook_use: dict[str, list[str]] = collections.defaultdict(list)
    for task in roadmap["tasks"]:
        for key in task.get("playbook", {}).get("citations", []):
            workbook_use[key].append(task["task_id"])

    entries = []
    for source in SOURCES:
        record = dict(source)
        used_by = sorted(workbook_use.get(source["id"], []))
        extra = record.pop("extra_used_by", [])
        record["used_by"] = {"workbook_tasks": used_by, "repository": extra}
        record["active_status"] = "ACTIVE"
        record["verified_on"] = VERIFIED_ON
        entries.append(record)
    for source in HISTORICAL_SOURCES:
        record = dict(source)
        record["used_by"] = {"workbook_tasks": [], "repository": record.pop("used_by")}
        record["verified_on"] = VERIFIED_ON
        entries.append(record)

    return {
        "reference_registry": {
            "id": "REFERENCE-REGISTRY-001",
            "version": "1.0",
            "status": "AUTHORITATIVE",
            "plan": "Bang_ke_hoach_SeqLogAD.xlsx",
            "plan_projection": ROADMAP,
            "generated_by": "scripts/build_reference_registry.py",
            "verified_on": VERIFIED_ON,
            "verification_services": [
                "https://api.crossref.org", "http://export.arxiv.org/api/query",
                "https://zenodo.org/api/records", "direct HTTP for official pages",
            ],
            "note": (
                "Machine-readable source of truth for every reference the active plan "
                "uses. Workbook S# identifiers are preserved and their task mappings are "
                "derived from the workbook projection, so they cannot drift. Regenerate "
                "rather than hand-editing."
            ),
            "classifications": [
                "LITERATURE_SUPPORTED", "LITERATURE_INFORMED_SEQLOGAD_DECISION",
                "SEQLOGAD_PROTOCOL_DECISION", "ENGINEERING_DECISION",
            ],
            "reference_support_gaps": REFERENCE_SUPPORT_GAPS,
            "sources": entries,
        }
    }


def render_active_markdown(payload: dict) -> str:
    by_id = {s["id"]: s for s in payload["sources"]}
    assigned = {sid for _, ids in SECTIONS for sid in ids}
    active = {s["id"] for s in payload["sources"] if s["active_status"] == "ACTIVE"}
    missing = active - assigned
    if missing:
        raise SystemExit(f"ACTIVE sources not assigned to a section: {sorted(missing)}")

    lines = [
        "# Active references",
        "",
        "Generated from [`reference_registry.yaml`](reference_registry.yaml) by",
        "`scripts/build_reference_registry.py`. Do not hand-edit: regenerate.",
        "",
        f"Organised according to `{payload['plan']}`. Verified {payload['verified_on']} against "
        "Crossref, the arXiv API, the Zenodo record API and official pages.",
        "",
        f"**{len(active)} active sources.** Workbook identifiers `S1`-`S11` are preserved; "
        "`S12`-`S17` were added by this consolidation for dataset and tooling provenance "
        "that the active work relies on.",
        "",
    ]
    for title, ids in SECTIONS:
        lines += [f"## {title}", ""]
        lines += ["| ID | Title | Year | Venue | Link | Used by | Relevance |",
                  "| --- | --- | ---: | --- | --- | --- | --- |"]
        for sid in ids:
            src = by_id[sid]
            link = src.get("official_url") or ""
            venue = src.get("venue") or ""
            tasks = src["used_by"]["workbook_tasks"]
            repo = src["used_by"]["repository"]
            used = ", ".join(tasks) if tasks else ("; ".join(repo[:2]) if repo else "—")
            year = src.get("year") or "—"
            lines.append(
                f"| `{sid}` | {src['title']} | {year} | {venue} | [link]({link}) | {used} | "
                f"{RELEVANCE.get(sid, '')} |"
            )
        lines.append("")

    lines += ["## Publication status", "",
              "| ID | Status | Note |", "| --- | --- | --- |"]
    for src in payload["sources"]:
        if src["active_status"] != "ACTIVE":
            continue
        note = src.get("use_boundary") or src.get("correction") or src.get("note") or ""
        lines.append(f"| `{src['id']}` | {src['publication_status']} | {note} |")
    lines.append("")

    historical = [s for s in payload["sources"] if s["active_status"] == "HISTORICAL"]
    if historical:
        lines += ["## Historical sources", "",
                  "Retained for provenance; not cited by active work.", "",
                  "| ID | Title | Year | Link |", "| --- | --- | ---: | --- |"]
        for src in historical:
            lines.append(f"| `{src['id']}` | {src['title']} | {src.get('year')} | "
                         f"[link]({src.get('official_url')}) |")
        lines.append("")

    gaps = payload.get("reference_support_gaps", [])
    lines += ["## Reference support gaps", ""]
    if gaps:
        for gap in gaps:
            lines += [
                f"### {gap['id']}", "",
                f"**Claim.** {gap['claim']}", "",
                f"**Problem.** {gap['problem']}", "",
                f"**Affects.** {', '.join(gap['affected_tasks'])} · resolve before "
                f"{gap['resolution_required_before']}", "",
                f"**Action.** {gap['recommended_action']}", "",
                f"Methodology changed: `{gap['methodology_changed']}`.", "",
            ]
    else:
        lines += ["None.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    rendered = yaml.safe_dump(build(root), sort_keys=False, allow_unicode=True, width=100)
    target = root / REGISTRY
    if args.check:
        active_md = root / ACTIVE_MD
        stale = (
            not target.exists()
            or target.read_text(encoding="utf-8") != rendered
            or not active_md.exists()
            or active_md.read_text(encoding="utf-8")
            != render_active_markdown(build(root)["reference_registry"])
        )
        if stale:
            print("STALE: regenerate with scripts/build_reference_registry.py")
            return 1
        print("CURRENT")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered, encoding="utf-8")
    payload = build(root)["reference_registry"]
    (root / ACTIVE_MD).write_text(render_active_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "output": REGISTRY,
        "sources": len(payload["sources"]),
        "active": sum(1 for s in payload["sources"] if s["active_status"] == "ACTIVE"),
        "historical": sum(1 for s in payload["sources"] if s["active_status"] == "HISTORICAL"),
        "gaps": len(payload["reference_support_gaps"]),
        "active_markdown": ACTIVE_MD,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
