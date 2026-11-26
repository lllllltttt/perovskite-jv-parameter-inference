# Sync checklist v2 — what must follow the Figure 2 / Figure 3 revision

**Nothing here has been applied.** Both Word files are untouched. This lists the
positions a later round must edit, with the reason and the source text, so the
author can approve the scope before editing starts.

This supersedes the phase-1 checklist. Sections A, B and E are carried over
(their numbers re-verified today, see the note under each), section C is
**changed** by this round, and sections F and G are **new**: they answer two
questions the brief asks explicitly. Rows marked *new* have no phase-1
counterpart.

Files referenced — both confirmed present, 2026-10-06:

* **MS** = `E:\project\work1\202660929\Manuscript_20260928_RG.docx`
  (the folder name really is misspelled `202660929`)
* **SI** = `E:\project\work1\20260929_si_provenance_wording\Supplementary_Information_provenance_wording_20260929.docx`

> **Which SI is current.** The S13 provenance-wording round produced a newer SI
> 29 minutes after `20260929_si_rg_sync\Supplementary_Information_RG_synced_20260929.docx`,
> and project memory records that the `si_rg_sync` file is superseded. Scans were
> re-run against the provenance-wording file. The two files agree on every
> position below, but the indices are only guaranteed for the file named above.

Paragraph indices are python-docx body-paragraph indices. They were **re-checked
directly against the two current files on 2026-10-06** (the phase-1 dumps
`_refs_raw.txt` / `_si_tables_raw.txt` in the phase-1 report folder agree with
them, and those dumps are the source of the quoted source text). Re-run the
scanners before editing, because indices shift the moment a paragraph is
inserted.

---

## A. Manuscript

| # | Loc | Class | What is there now | What must change | Why |
|---|---|---|---|---|---|
| A1 | MS p17 | xref | "(Fig. 2a)" — cites the nine individual-parameter correlations | repoint to the **new SI figure** | the nine-parameter grid leaves Figure 2 |
| A2 | MS p19 | xref | "(Fig. 2b and Table S11)" | repoint to **Fig. 2g** | panel letters shift (old 2b → new 2g) |
| A3 | MS p20 | xref | "(Fig. 2c and Table S11)" | repoint to **Fig. 2h** | panel letters shift (old 2c → new 2h) |
| A4 | MS p19–p20 | numbers | 68 / 61 / 66 % and 8 / 3 / 1 % | **no change** | re-verified against `params_train` and the frozen predictions; all six reproduce to <5e-7 in this round's build |
| A5 | MS p23 | caption | Figure 2 caption: "all nine panels share a 0-1 range", "in the model's normalized log10 coordinates" | **full rewrite** | new a–h layout; state log₁₀ units; name the correlation **Pearson**; give the physical unit basis of the shared-scale logarithm; one common range for the three ratio panels |
| A6 | MS p25 | text | "Fig. 3a-c"; "differs by approximately a factor of 280"; "approximately a factor of 72" | **rewrite with the final example pairs** | see §G — those factors belong to the *current* examples (1010, 2641) and (8271, 10258), not to the sketch's pairs |
| A7 | MS p29 | caption | Figure 3 caption: "7,666 retained pairs", "only pairs with i < j are kept, so samples may recur", "(d) … (e) …" | **full rewrite** | corrected dedup; see §G for the pair/letter changes |
| A8 | MS p72 | Methods | the coordinate-transform paragraph (a = …, r = …) | confirm it states the transform is in **physical log₁₀**, applied to truth and prediction alike | the figure's axis labelling depends on it |
| A9 | MS p5 | wording | "over the past decade" | **no change** | a period of time, not a unit |
| A10 | MS p29 | caption | "(c) Absolute per-parameter differences \|log₁₀(θi/θj)\|" | **no change — already correct** | *new row.* The Word already defines the quantity correctly; the phase-1 **sketch** was the only place that drew a second logarithm. Recorded so nobody "fixes" the Word |
| A11 | MS p40 | wording | "**The decisive comparison** is against the uncertainty available without reading the curve at all" | **no change** | *new row.* This "decisive" is in the uncertainty section and is unrelated to the Figure 3 tier judgements that §2 of this round removes. The removal must **not** be applied here |

**Manuscript totals: 11 positions — 5 need edits (A1, A2, A3, A5, A6+A7), 6 are
no-ops (A4, A8, A9, A10, A11, and A6/A7's letter-check).**

---

## B. Supplementary Information — Table S6 block (nearest-neighbour analysis)

This is the block the corrected deduplication changes. Every number below was
recomputed this round from `source_data/fig3_pairs_v2.csv` and independently
reproduced; values agree with the phase-1 checklist.

**B1. The rule paragraph (SI p19)** — the Table S6 caption itself (SI p18) is
short. The rule and its counts sit in the paragraph at **SI p19**:

> old: "…7,666 retained nearest-neighbor pairs, formed by pairing every test
> curve with its nearest other curve and keeping only pairs with i < j; this rule
> is not the set of all unique undirected edges, and samples may recur (the set
> contains 12,487 distinct samples, 2,497 of which appear more than once)"

new: every test curve contributes one **directed** nearest-neighbour relation;
after mapping each relation to its unordered pair and deduplicating, **11,245**
undirected edges covering **all 15,307** test curves; a curve may participate in
more than one edge — **5,859** do, the maximum being 5. The "i < j" rule and the
"samples may recur" caveat both go, because the corrected set no longer drops
edges by direction.

**B2. Table S6.1 — d_J distribution** (SI table block 6):

| | archived | corrected |
|---|---|---|
| count | 7,666 | **11,245** |
| mean | 0.00395 | **0.004236** |
| std | 0.00513 | **0.005811** |
| min | 0.00004 | **0.000040** |
| 25% | 0.00128 | **0.001365** |
| 50% | 0.00267 | **0.002862** |
| 75% | 0.00483 | **0.005165** |
| 90% | 0.00791 | **0.008278** |
| 99% | 0.02500 | **0.026912** |
| max | 0.11523 | **0.173429** |

**B3. Table S6.2 — d_Θ distribution:**

| | archived | corrected |
|---|---|---|
| count | 7,666 | **11,245** |
| mean | 0.2089 | **0.210959** |
| std | 0.0841 | **0.084251** |
| min | 0.0330 | **0.019512** |
| 25% | 0.1464 | **0.147911** |
| 50% | 0.1999 | **0.202068** |
| 75% | 0.2636 | **0.266259** |
| 90% | 0.3218 | **0.324668** |
| 99% | 0.4329 | **0.434120** |
| max | 0.6053 | **0.617473** |

**B4. Table S6.3 — coupling statistics** (SI table block 8):

| | archived | corrected |
|---|---|---|
| Spearman(d_J, d_Θ) | 0.158 | **0.154458** |
| Pearson(d_J, d_Θ) | 0.079 | **0.073193** |
| NN d_Θ median | 0.200 | **0.202** |
| NN d_J median | 0.00267 | **0.00286** |
| random d_Θ median | 0.349 | **unchanged** |
| random d_J median | 0.117 | **unchanged** |

**B5. Table S6.4 — closest-N% tiers** (n / median d_J / median d_Θ):

| tier | archived | corrected |
|---|---|---|
| 10% | 767 / 0.000420 / 0.1683 | **1,124 / 0.000447 / 0.1729** |
| 5% | 383 / 0.000291 / 0.1554 | **562 / 0.000320 / 0.1665** |
| 1% | 77 / 0.000153 / 0.1443 | **112 / 0.000171 / 0.1452** |
| 0.5% | 38 / 0.000118 / 0.1337 | **56 / 0.000133 / 0.1407** |
| 0.1% | 8 / 0.000079 / 0.1021 | **11 / 0.000090 / 0.1041** |

**B6. SI body prose that quotes the tier numbers (SI p24)** — "closest 0.5% ()
0.1337; closest 0.1% () 0.1021" must become 0.1407 and 0.1041, and the pair
counts change as in B5.

**B7. Table S6 caption (SI p18)** *(new row)* — it says "all five representative
collision cases". If the final Figure 3 adopts the sketch's two example pairs,
check whether the five *archived* representative cases are still the ones
tabulated; the caption's count follows whatever the table holds.

---

## C. Supplementary Information — Table S10 (metric comparison) — **changed by this round**

The phase-1 checklist left C3 as an author decision ("correct M2–M6, or state
that they retain the archived rule"). **This round authorizes and applies the
uniform rule**, so all six rows are definite edits. The archived
`i < NN(i)` rule silently dropped 3,345–3,579 edges per metric; the corrected
rule is applied identically to M1–M6. Detail in `TABLE_S10_DRAFT_V2.md`.

**C1. Table S10 caption (SI p64)** — quotes "0.200–0.219" and "0.144 (M1) to
0.182 (M2)":

* nearest-neighbour median range **0.200–0.219 → 0.202–0.222**
* closest-1% median range **0.144 (M1) to 0.182 (M2) → 0.145 (M1) to 0.189 (M2)**

The rest of the caption — the six metric definitions, the random baseline
(0.349), and the statement that pair identities and parameter-level rankings are
metric dependent — is **unchanged**.

**C2. Table S10 row M1** — pairs **7,666 → 11,245**; `d_Θ` all-NN **0.1999 →
0.2021**; closest 1% **0.1443 → 0.1452**; closest 0.5% **0.1337 → 0.1407**;
closest 0.1% **0.1021 → 0.1041**; Spearman(d_J, d_Θ) **0.158 → 0.1545**.

**C3. Table S10 rows M2–M6** — each produced by the same defective rule under
its own metric, so each is corrected (no longer conditional):

| metric | pairs | all-NN median | closest 1% | closest 0.5% | closest 0.1% |
|---|---|---|---|---|---|
| M2 | 7,635 → **11,060** | 0.2165 → **0.2194** | 0.1816 → **0.1885** | 0.1855 → **0.1812** | 0.1898 → **0.2125** |
| M3 | 7,638 → **11,104** | 0.2164 → **0.2191** | 0.1679 → **0.1808** | 0.1564 → **0.1564** | 0.1506 → **0.1502** |
| M4 | 7,666 → **11,208** | 0.2072 → **0.2092** | 0.1520 → **0.1509** | 0.1505 → **0.1532** | 0.1263 → **0.1133** |
| M5 | 7,670 → **11,212** | 0.2073 → **0.2094** | 0.1520 → **0.1509** | 0.1505 → **0.1532** | 0.1263 → **0.1133** |
| M6 | 7,691 → **11,036** | 0.2190 → **0.2220** | 0.1686 → **0.1838** | 0.1592 → **0.1589** | 0.1633 → **0.1595** |

The robustness conclusion survives for every metric; only the quoted numbers
change. See C5 for the one caveat the text must not contradict.

**C4. T10.1 caption (SI p65)** — the tier columns inside it change per C2/C3.

**C5. New caveat — do not imply monotonicity** *(new row)*. For M2 the
closest-0.1% median (0.2125) is *higher* than the closest-1% median (0.1885).
This is not introduced by the fix — the archived numbers are also non-monotone
(0.1898 vs 0.1816) — but the corrected table makes it more visible. The SI text
must not read as if the medians fall monotonically with tier tightness.

---

## D. Supplementary Information — other affected positions

| # | Loc | What | Action |
|---|---|---|---|
| D1 | SI p16 (Table S5) | cites "(Fig. 2a)" | repoint to the **new SI figure** |
| D2 | SI p85 (Table S16) | cites "the normalized-scale ρ of Fig. 2a" | repoint to the **new SI figure** |
| D3 | SI p19 | the Table S6 rule paragraph | see B1 |
| D4 | SI p24 | running text: "closest 0.5% () 0.1337; closest 0.1% () 0.1021" | see B6 |
| D5 | SI p64, p65 | Table S10 caption and T10.1 caption | see C1–C5 |
| D6 | SI p68 (Table S11 caption) | "median absolute log-error 0.20–0.21 decades" | **wording:** "decades" → "log₁₀ units"; the value itself does not change |
| D7 | Table S11 header (table block 31) | "Median absolute log-error (decades)" | header text → log₁₀ units |
| D8 | Table 27 header | "Param log10-RMSE (physical log10 decades)" | header text → log₁₀ units |
| D9 | **new figure** | the nine individual-parameter scatterplots, moved out of Figure 2 | **must be created**, numbered, captioned, and cited from A1/D1/D2. The SI currently runs Figures S1–S5 (pp. 102, 105, 107, 116, 119), so the next free number is **Figure S6** |

---

## E. "decades" → "log₁₀ units" sweep

Unchanged from phase 1. The **main text is clean** — its single occurrence
(MS p5, "over the past decade") is a period of time and must not be touched.

The **SI has 20 occurrences across 12 positions**, plus two table headers:

| Loc | ×  |
|---|---|
| SI p9 | 1 |
| SI p48 | 1 |
| SI p51 | 1 |
| SI p68 | 1 |
| SI p83 | 4 |
| SI p85 | 2 |
| SI p89 | 2 |
| SI p91 | 3 |
| SI p93 | 2 |
| SI p94 | 1 |
| Table 27 header | 1 |
| Table 31 header | 1 |

Also outside Word: the **Figure 3 x-axis label in the current artwork** reads
"(decades)" and must become log₁₀ units in the final render.

"Decade" is legitimate when it means a factor of ten in a ratio or a log-scale
span, so each occurrence needs a one-line read rather than a blind replace.

---

## F. Withdrawn inferential statistics — where they do and do not appear *(new section)*

Section 2 of this round withdraws the paired Wilcoxon signed-rank p-values and
the per-pair bootstrap confidence intervals from the Figure 3 tier analysis,
because the tiers reuse samples across pairs (closest 1%: 112 pairs / 196
distinct curves / 27 repeated).

**Checked directly in both Word files on 2026-10-06, by paragraph scan:**

| file | occurrences of Wilcoxon / bootstrap / p-value / signed-rank |
|---|---|
| **MS** | **none** |
| **SI** | 4 paragraphs — of which **2 are false positives** and **2 are unrelated to Figure 3** |

The SI occurrences, identified:

* SI p60, p62 — false positives: the pattern matched physical notation such as
  "τn = τp = 10 ns" and "μn = μp = 20 cm² V⁻¹ s⁻¹". No statistics.
* SI p74 (Table S13, leakage-free multi-seed benchmark) — p-values comparing
  model families across seeds. The brief states explicitly that this round's
  withdrawal does **not** apply to the S13 cross-seed tests. **Stays.**
* SI p113 (Figure S3, decoder–COMSOL cycle consistency) — "two-sided paired
  Wilcoxon W = 231, p = 9.01 × 10⁻⁴", on the 45-sample cohort. That is a
  genuinely paired, independent design (one pair per cohort sample), not the
  Figure 3 tier construction. **Stays.** The manuscript's matching text is in
  Methods §2.12 and the Discussion.

**Conclusion: the Figure 3 tier Wilcoxon and bootstrap statistics were never
adopted into either Word file.** The withdrawal is confined to the phase-1
delivery, and no Word edit is required for it. The three "decisive"-family
judgements likewise do not appear as Figure 3 tier claims in the Word (see A11
for the one unrelated "decisive" that must be left alone).

---

## G. Figure 3 — the example pairs and their quoted factors *(new section)*

This is the one substantive conflict the correction exposes, and it needs an
author decision.

The **current Word** Figure 3 uses two examples, named in the body text
(MS p25) and the caption (MS p29) as **τ_ETL** (differing by "approximately a
factor of 280") and **r_rad** (a factor of 72). Those two examples are:

| Word example | test indices | parameter with the largest \|Δlog₁₀\| | \|Δlog₁₀\| | factor |
|---|---|---|---|---|
| τ_ETL | 1010 / 2641 | `tau_ETL` | 2.444 | **×278** ✓ quoted as 280 |
| r_rad | 8271 / 10258 | `rad_c` | 1.856 | **×72** ✓ quoted as 72 |

**Both reproduce exactly from the raw parameters** — the Word's quoted factors
are correct, and they were computed from raw log₁₀ differences, i.e. the correct
quantity. This is further evidence that the double-log defect never reached the
Word (see A10).

The **phase-1/v2 sketch** uses different examples, selected by the
maximise-the-ratio-difference rule:

| sketch example | test indices | parameter with the largest \|Δlog₁₀\| | \|Δlog₁₀\| | factor |
|---|---|---|---|---|
| (a) mobility ratio | 2890 / 5067 | `tau_p_pvk` | 2.646 | ×443 |
| (b) lifetime ratio | 500 / 4560 | `tau_HTL` | 1.544 | ×35 |

The sketch's cases were chosen by a rule, not by which parameter dominates, so
their largest differences fall on different parameters. **Consequences:**

* **G1.** If the final Figure 3 keeps the sketch's pairs, then MS p25 and MS p29
  must be rewritten: the names τ_ETL / r_rad and the factors 280 / 72 no longer
  describe the figure, and the correct statements are `tau_p_pvk` ×443 for
  (2890, 5067) and `tau_HTL` ×35 for (500, 4560). A7/A6 depend on this.
* **G2.** If instead the figure keeps the Word's existing examples
  (1010, 2641) and (8271, 10258), both are still present in the corrected pair
  set, the quoted factors stand, and only the layout letters change. The sketch's
  two pairs then remain illustrative only.
* **G3.** Either way, the caption must carry the disclosure the sketch already
  carries: each pair is an extreme member of the closest 1% selected by the
  stated rule, other parameters differ simultaneously, and a small normalised
  curve distance is not experimental indistinguishability.

**Open item for the author** (see `PHASE1_REPORT_v2.md` Appendix B).

---

## H. Not found / blocked

| Item | Status |
|---|---|
| `Style_Sheet_20260928.md` | **not found anywhere** in `E:\project\` or `C:\Users\Administrator\.claude\` (case-insensitive search). Final styling is blocked pending this file. Interim convention = the v5 figure package's `figstyle.py`, continued in `figstyle_v2.py`. Not a blocker for phase 1. |

---

## I. Summary counts

| Area | Positions | Need edits | No-ops |
|---|---|---|---|
| Manuscript | 11 | 5 | 6 |
| SI table S6 block (incl. B7) | 7 | 7 | 0 |
| SI table S10 (C1–C5) | 6 | 6 | 0 |
| SI other (D1–D9) | 9 | 9 (incl. 1 new figure) | 0 |
| "decades" sweep | 14 (12 SI + 2 headers) + 1 artwork | 15 | 0 |
| Withdrawn statistics (F) | 4 SI occurrences examined | **0** | 4 |
| Figure 3 example pairs (G) | 2 positions + 1 decision | **decision first** | — |
| **Total** | **52** | **42 (+1 decision)** | **10** |

Word files modified in this round: **none.**

Companion machine-readable form: `sync_checklist_v2.csv`.
