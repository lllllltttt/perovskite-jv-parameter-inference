# EXPERIMENT 3 — Manuscript Impact Assessment (10 items)

**Frozen manuscript:** `manuscript_stage1_submission_clean.md` (NOT modified —
this is an advisory record for the revision)
**Advisory status:** CORE SCIENTIFIC CLAIMS SURVIVE · NO RETRAINING · NO FIGURE
RE-GENERATION · the manuscript already frames recoverability as prior-conditional
(§2.2 "conditional on this prior"; §3.3 "prior-conditional"), and EXP3 sharpens
rather than overturns that framing.

The single new fact EXP3 adds: **within the six paired bulk parameters, the high
marginal Pearson is dominated by recovery of the shared average scale
(a: r ≈ 0.88–0.93), with a weak-but-real asymmetry-ratio channel (r ≈ 0.27–0.43,
29+ SD above a shuffled null).** Nothing below touches the frozen file.

---

### Item 1 — Abstract: "high accuracy (Pearson correlation 0.88–0.92)" should name the shared scale *(required wording)*
The abstract's "recovers bulk transport and bulk lifetime parameters with high
accuracy (Pearson correlation 0.88–0.92 in normalized log space)" is accurate
but underspecified. EXP3 shows that value is essentially the shared-scale
recoverability (a_mu 0.925, a_tau 0.882, a_D 0.925). Revision wording: the six
bulk parameters' high recoverability (Pearson 0.88–0.92) is dominated by
**shared-scale recoverability** under the effective retained prior, with the
electron–hole asymmetry ratio recovered only weakly (Pearson 0.27–0.43) though
still significantly above a shuffled-null.

### Item 2 — §3.3 recoverability hierarchy bullet (line 178): "High recoverability. The six bulk parameters reach r = 0.878–0.919" *(required reframing)*
This bullet should report the prior-coordinate split: the r = 0.878–0.919 range
reflects **shared-scale** recovery (a: 0.88–0.93, Skill_RMSE 0.78–0.86 over a
prior-only predictor); the electron–hole ratio recovers at 0.27–0.43 with only
0.07–0.18 added skill over the prior. The hierarchy ordering (bulk > interface >
radiative) is unchanged.

### Item 3 — §2.2 paired-construction paragraph (line 76): the correlation consequence can be quantified *(optional strengthening)*
The manuscript already states the marginal Spearman correlations (0.94/0.99/0.90)
and their prior-conditional meaning. EXP3 adds the *geometry* behind them:
SD(a)/SD(0.5r) = 5.4 / 12.7 / 4.3 (shared-scale variance 18–162× the half-ratio
variance) with ~zero a–r covariance (all |r(a,r)| < 0.02), reproducing the
marginal pair correlations by algebra to 0.933 / 0.988 / 0.896 (manuscript
0.94 / 0.99 / 0.90, worst deviation 0.007). One or two sentences would make the
"intentional, physically constrained prior" concrete.

### Item 4 — §3.3 prior-conditional caveat (line 215): extend to the coordinate level *(required)*
"the recoverability hierarchy is prior-conditional" is correct and now has a
precise content: the dominant recoverable channel is the shared scale, whose
prior variance swamps the ratio's. The caveat "applies to every number in
Tables 2–4" can be extended: shared-scale recoverability is also prior-assisted —
the model does not identify the shared scale independent of the retained prior.

### Item 5 — Table 2 / new supplementary table: coordinate-level recoverability *(optional addition)*
No frozen-table change. If the reviewer's response warrants it, a supplementary
table from `results/frozen_coordinate_recoverability.csv` (Pearson/Spearman/
MAE/RMSE in decades, ratio factor 10^med, Skill_RMSE vs the train-only prior
baseline for a_mu, r_mu, a_tau, r_tau, a_D, r_D) is ready to insert.

### Item 6 — Sensitivity section §3.3: coordinate-level S_i *(optional addition)*
The manuscript's per-parameter S_i are unchanged. EXP3 adds the coordinate-level
sensitivity (a_mu 0.378, r_mu 0.037, a_tau 0.500, r_tau 0.024, a_D 0.113,
r_D 0.022) showing shared scales 3–23× more J-V-sensitive than their ratios.
a_D is the mild exception (lowest shared-scale S but r = 0.925) — worth one
clause so the sensitivity–recoverability discussion stays honest.

### Item 7 — §4.1 "Bulk parameters are more recoverable" reading *(required wording)*
"Bulk parameters are more recoverable than interface and radiative parameters"
should be read and phrased as "the *shared scale* of the bulk pairs is highly
recoverable". The physical reading (majority-carrier transport and bulk
recombination shape the curve) remains; the parameter-level statement must not
imply both members of each pair are individually pinned down.

### Item 8 — Terminology guard *(must NOT regress)*
No manuscript passage claims identifiability (deliberately avoided per §3.3 and
§4). EXP3 must not be summarized in the response as "ratios contain no physical
information" or "recoverability is prior-independent" — the correct framing is
"asymmetry-ratio recoverability is weak but genuine (29+ SD above null)" and
"shared-scale recoverability under the effective retained prior". The frozen
manuscript wording and this experiment's constraints are aligned; the response
text should use the §25 terminology.

### Item 9 — Figures *(no frozen-figure change; supplementary offers)*
EXP3_FigA–F (figures/) are new, standalone figures for the revision package:
A recoverability + skill; B marginal-vs-shared-vs-ratio decomposition; C prior
geometry + algebra reproduction; D predicted-vs-truth 2×3 grid; E sensitivity vs
recoverability; F architecture robustness (5 seeds × 3 families). They cite only
frozen results and can be offered as supplementary figures or reviewer-only.

### Item 10 — Reviewer-response text *(the deliverable)*
The direct answer to the reviewer's two questions is: (1) shared-scale recovery
dominates (Outcome A) — the 0.88–0.92 marginal Pearson is mostly a_mu/a_tau/a_D;
(2) the model beats a no-J–V prior-only point predictor by Skill_RMSE 0.78–0.86
on shared scales and 0.07–0.18 on ratios. All supporting numbers, QC (12/12),
and figures are in this experiment directory. Recommended one-line response:
*"The high recoverability of the six paired bulk parameters reflects primarily
shared-scale recovery under the effective retained simulation prior; the
electron–hole asymmetry ratio is a weak-but-real secondary channel, and the J–V
observable adds substantial sample-specific information beyond a prior-only
predictor for the shared scales."*
