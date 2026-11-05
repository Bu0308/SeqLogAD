# P2.2 S42 V13R1 — RunPod A40 upload kit

1. Create an A40 48 GB Pod with a Network Volume mounted at `/workspace`.
2. Use `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404` and map `HF_TOKEN`
   from a RunPod secret.
3. Upload all five files in this directory to `/workspace/uploads`.
4. Open `P2.2_run_all_sequence_lora_s42_v13r1.ipynb` in JupyterLab and click **Run All Cells**.
5. Stop only when `SAFE_TO_STOP_RUNTIME=YES`.

The notebook verifies the code/data/source-development ZIPs and the pinned
Projmem wheel by SHA-256. V13R1 checkpoints use source-development F1 for early
stopping; NLL, accuracy, precision, recall, AUROC and AP are logged. These are
source-development metrics, not target anomaly evaluation results.

Scientific ZIP: `/workspace/SeqLogAD/sequence-v13r1/P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip`.
Projmem database: `/workspace/SeqLogAD/sequence-v13r1/.pmem/pmem.db`.
Download the entire `sequence-v13r1` directory, including `.pmem`, `attempts`, and `projmem_exports`, with the scientific ZIP. Bootstrap failures are journaled before Projmem installs; their journals are registered in Projmem on the next successful setup. Training attempts stream to `attempts/<id>/training.log`.
