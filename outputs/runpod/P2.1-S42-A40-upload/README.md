# P2.1 S42 — RunPod A40 upload kit

Dataset: `phase2-final.zip`. The notebook verifies SHA-256
`ebcfdfd6eb7b1607eb6d57e60fae88456d03bcb8ae2c6688ea398042c856224b` and extracts it to `/workspace/SeqLogAD/runtime/2cc81d1e4e01-ebcfdfd6eb7b/phase2`.
You do not need to unzip it manually.

1. Create one RunPod Pod with NVIDIA A40 48 GB and a Network Volume mounted at `/workspace`.
2. Use an image with Python 3.12. The notebook installs the frozen PyTorch CUDA 12.8 environment.
3. Create RunPod secret `huggingface_token` and map it to environment variable `HF_TOKEN`.
4. Create `/workspace/uploads` and upload the three files in this directory there.
5. Open `P2.1_run_all_semantic_s42.ipynb` in JupyterLab and choose **Run All Cells**.
6. Stop the Pod only after `FINAL_PERSISTENT_BACKUP=PASS` and `SAFE_TO_STOP_RUNTIME=YES`.

Final artifact: `/workspace/SeqLogAD/P2.1/seqlogad_outputs_P2.1_S42_FINAL.zip`.
BGL-S42 is registered and skipped; the notebook trains/resumes HDFS-S42 and Hadoop-S42.
