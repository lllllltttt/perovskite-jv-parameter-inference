# EXP1 Phase P/Q — model-outcome & leakage-effect analysis

Frozen VAE-v6 reference (full-data scaling): per-param r = 0.906, 0.919, 0.878, 0.881, 0.909, 0.896, 0.594, 0.720, 0.559, mean = 0.8069

## Per-seed mean Pearson r (across 9 parameters), test cohort
model        mean_r     sd_r   min..max
vae          0.8056   0.0067     0.7966..0.8137
det_ae       0.8054   0.0038     0.7988..0.8085
mlp          0.7935   0.0085     0.7836..0.8013

## Phase P — outcome classification (descriptive; n=5 seeds/family)
vae - det_ae: delta_mean_r = +0.0002  (Wilcoxon p=0.812, paired-t p=0.919)
vae - mlp: delta_mean_r = +0.0122  (Wilcoxon p=0.062, paired-t p=0.042)
det_ae - mlp: delta_mean_r = +0.0119  (Wilcoxon p=0.062, paired-t p=0.016)

VAE vs best deterministic baseline: delta_mean_r = +0.0122
VERDICT: B (VAE probabilistic advantage only — deterministic AE within ~0.02 of VAE)

## Phase Q — preprocessing-leakage effect (frozen vs leakage-free VAE)
mu_n     frozen 0.9063 -> lf-mean 0.9040  delta -0.0023
mu_p     frozen 0.9194 -> lf-mean 0.9165  delta -0.0029
tau_n    frozen 0.8783 -> lf-mean 0.8782  delta -0.0001
tau_p    frozen 0.8808 -> lf-mean 0.8801  delta -0.0007
Nc       frozen 0.9090 -> lf-mean 0.9055  delta -0.0035
Nv       frozen 0.8956 -> lf-mean 0.8910  delta -0.0046
tau_ETL  frozen 0.5936 -> lf-mean 0.5939  delta +0.0003
tau_HTL  frozen 0.7199 -> lf-mean 0.7228  delta +0.0029
rad_c    frozen 0.5592 -> lf-mean 0.5588  delta -0.0004

overall delta_mean_r = -0.0013  (leakage-free mean 0.8056 vs frozen 0.8069)
LEAKAGE-EFFECT CLASSIFICATION (overall mean |delta_r|): NEGLIGIBLE
largest single-parameter delta: Nv -0.0046
