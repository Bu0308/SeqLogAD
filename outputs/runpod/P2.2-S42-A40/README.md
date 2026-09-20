# P2.2 S42 — RunPod A40 upload kit

1. Create one RunPod A40 48 GB Pod with a Network Volume mounted at `/workspace`.
2. Use `runpod/pytorch:1.0.3-cu1281-torch291-ubuntu2404`.
3. Map a RunPod secret to environment variable `HF_TOKEN`.
4. Upload the three files in this directory into `/workspace/uploads`.
5. Open `P2.2_run_all_sequence_lora_s42.ipynb` in JupyterLab and click **Run All Cells** once.
6. Stop only after `SAFE_TO_STOP_RUNTIME=YES`.

The notebook verifies code `412f096249201edf6ba2ca908c0282b5d3d5d504c05a973023b2dcf95408bd64`, data `4ed76b92e4b001138b28b4b3b4d3017d6ff7f30dd31e8cca0649bfdf34ede781`
and bundle manifest `1268b669a8b1b474658cfa7daa6556c987b0f31f07e0101ed30af250a8d7f129` before loading the model. Interrupted targets
resume from `/workspace/SeqLogAD/P2.2/recovery`.

Final artifact: `/workspace/SeqLogAD/P2.2/seqlogad_outputs_P2.2_S42_FINAL.zip`.
