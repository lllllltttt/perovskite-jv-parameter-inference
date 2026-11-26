# EXP2 cross-environment numerical QC — server leg

Self-contained package. Runs the latent-uncertainty decomposition (M=500,
seeded) on 500 fixed test samples with the **frozen Stage-I VAE-v6**, and
prints a JSON summary (per-parameter median f_latent, median sigma_total,
median sigma_total/sigma_current, mean mu_total, 95% moment-matched
coverage). Compare against `cross_env_local.json` (already computed on the
local box).

## Run on the server

Transfer this whole `server_qc/` folder to the server, then **either**:

**Option A — double-click (no command line):** double-click `RUN_ME.bat`.
It runs the script, writes `cross_env_server.json` into the same folder, and
keeps the window open so you can confirm it printed `saved: cross_env_server.json`.

**Option B — command line:** from inside the folder:

```
python server_qc.py --out cross_env_server.json --tag server
```

(Default `--model_dir data_frozen/vae-v6` and `--data
data_frozen/dataset_normalized.npz` assume you run from inside the folder.)

Either way, then send `cross_env_server.json` back (paste the printed JSON is
fine). Note `--tag server` marks the JSON's `"env"` field as `"server"` (plain
double-click without the bat writes `"env": "local"` — the numbers are what
matter, not the label).

## What is compared

| quantity | what we check |
|---|---|
| median f_latent (9 params) | latent variance share identical between envs |
| median sigma_total | absolute predictive scale identical |
| median ratio_sigma | widening factor identical |
| mean mu_total | latent-averaged point predictions identical |
| cov95_moment | 95% moment-matched coverage identical |

Both envs draw the same 500 samples and the same seeded epsilons, so
differences should be at the ~1e-3 level (float32 + Keras 2 vs 3 numerics).
Anything larger than ~0.02 flags an environment problem.

Server env note: TF 2.13 / Keras 2 loads the frozen `encoder.h5` natively
(custom_objects for `Sampling` is provided anyway).
