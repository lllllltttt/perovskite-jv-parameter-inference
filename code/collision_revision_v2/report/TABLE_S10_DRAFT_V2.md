# Table S10 (draft v2) — collision robustness under alternative J-V similarity metrics

Pair construction: each sample's directed nearest neighbour -> `(min(i,j), max(i,j))` -> unique unordered set, applied identically to M1-M6.

| metric | definition | unique pairs (archived -> corrected) | median $d_\Theta$ all-NN | random baseline | closest 1% | closest 0.1% |
|---|---|---|---|---|---|---|
| M1 | normalized-J full-curve RMSE, 131 pts (paper metric) | 7666 $\to$ 11245 | 0.202 | 0.349 | 0.145 | 0.104 |
| M2 | physical-current full-curve RMSE, 131 pts (mA cm$^{-2}$) | 7635 $\to$ 11060 | 0.219 | 0.349 | 0.189 | 0.212 |
| M3 | M2 / pair-mean $\vert J_{sc}\vert$ | 7638 $\to$ 11104 | 0.219 | 0.349 | 0.181 | 0.150 |
| M4 | physical-current 0-1.0 V RMSE, 101 pts | 7666 $\to$ 11208 | 0.209 | 0.349 | 0.151 | 0.113 |
| M5 | M4 / pair-mean $\vert J_{sc}\vert$ | 7670 $\to$ 11212 | 0.209 | 0.349 | 0.151 | 0.113 |
| M6 | J/$\vert J_{sc}\vert$ shape RMSE, 131 pts (supplementary only) | 7691 $\to$ 11036 | 0.222 | 0.349 | 0.184 | 0.160 |

$d_\Theta$ is the fixed RMSE over the nine normalized-log parameters and is identical by construction for every J metric. Random baseline: frozen seed-42 draw of 200,000 ordered index pairs, self-pairs removed (199985 retained), median $d_\Theta$ = 0.3490.

Tier rounding: $k=\max(1,\mathrm{round}(M f))$ with $M$ the number of unique pairs; tiers are the $k$ smallest $d_J$ values, stable-sorted, so ties are kept in index order.
