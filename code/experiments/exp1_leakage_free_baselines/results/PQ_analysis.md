# EXP1 Phase P/Q — model-outcome & leakage-effect analysis

Frozen VAE-v6 reference (full-data scaling): per-param r = 0.906, 0.919, 0.878, 0.881, 0.909, 0.896, 0.594, 0.720, 0.559, mean = 0.8069

## Per-seed mean Pearson r (across 9 parameters), test cohort
model        mean_r     sd_r   min..max
vae          0.7954   0.0100     0.7823..0.8090
det_ae       0.8128   0.0068     0.8067..0.8238
mlp          0.7894   0.0088     0.7810..0.7998

## Phase P — outcome classification (descriptive; n=5 seeds/family)
vae - det_ae: delta_mean_r = -0.0175  (Wilcoxon p=0.062, paired-t p=0.005)
vae - mlp: delta_mean_r = +0.0060  (Wilcoxon p=0.062, paired-t p=0.099)
det_ae - mlp: delta_mean_r = +0.0235  (Wilcoxon p=0.062, paired-t p=0.004)

VAE vs best deterministic baseline: delta_mean_r = +0.0060
VERDICT: C (architectures comparable — framework remains the contribution)

## Phase Q — preprocessing-leakage effect (frozen vs leakage-free VAE)
mu_n     frozen 0.9063 -> lf-mean 0.8936  delta -0.0127
mu_p     frozen 0.9194 -> lf-mean 0.9079  delta -0.0115
tau_n    frozen 0.8783 -> lf-mean 0.8704  delta -0.0079
tau_p    frozen 0.8808 -> lf-mean 0.8721  delta -0.0087
Nc       frozen 0.9090 -> lf-mean 0.8981  delta -0.0109
Nv       frozen 0.8956 -> lf-mean 0.8864  delta -0.0092
tau_ETL  frozen 0.5936 -> lf-mean 0.5780  delta -0.0156
tau_HTL  frozen 0.7199 -> lf-mean 0.7086  delta -0.0113
rad_c    frozen 0.5592 -> lf-mean 0.5432  delta -0.0160

overall delta_mean_r = -0.0115  (leakage-free mean 0.7954 vs frozen 0.8069)
LEAKAGE-EFFECT CLASSIFICATION (overall mean |delta_r|): SMALL
largest single-parameter delta: rad_c -0.0160
