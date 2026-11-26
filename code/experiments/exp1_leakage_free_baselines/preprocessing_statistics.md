N total = 102046  (train 71432, val 15307, test 15307)
recovery max rel err params (vs stored raw test): 4.71e-15
recovery max abs err J (vs stored raw test): 4.55e-13
split membership taken from archived npz: train 71432, val 15307, test 15307
NOTE: independent sklearn seed-42 reproduction does NOT match the archived
membership (documented in detail in README.md §Split). Blocks used verbatim.
saved split_indices_original_reproduced.npz

===== TRAIN-ONLY PARAM SCALER =====
param train min (log10): [ -6.34103516  -6.3439018   -9.3080349   -9.34582346  22.76641285
  22.63447727 -12.         -14.         -12.        ]
param train max (log10): [ -2.65560773  -2.68193667  -1.65560773  -1.69036983  26.34830486
  26.33845649  -8.         -10.          -9.        ]
J train min (first/last cols): 0.348842 / -6052.56
J train max (first/last cols): 24.0962 / -1.24791e-05

===== OUT-OF-[0,1] STATISTICS (train-only scalers) =====
Parameter (log10 space, unscaled-for-[0,1]):
param            val<0     val>1    test<0    test>1
mu_n_pvk        0.0000    0.0000    0.0000    0.0001
mu_p_pvk        0.0001    0.0001    0.0000    0.0001
tau_n_pvk       0.0001    0.0000    0.0001    0.0000
tau_p_pvk       0.0000    0.0000    0.0001    0.0000
Nc_eff_pvk      0.0001    0.0000    0.0001    0.0000
Nv_eff_pvk      0.0000    0.0000    0.0000    0.0000
tau_ETL         0.0000    0.0000    0.0000    0.0000
tau_HTL         0.0000    0.0000    0.0000    0.0000
rad_c           0.0000    0.0000    0.0000    0.0000
max param extrapolation: val 0.0064  test 0.0279

J columns out-of-[0,1]:
  val fraction <0: 0.00002   >1: 0.00000   min -0.0920  max 1.0000
  test fraction <0: 0.00003   >1: 0.00002   min -0.2487  max 1.0001
  val: columns with any <0: [np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(67), np.int64(68), np.int64(103), np.int64(104), np.int64(105), np.int64(106), np.int64(107), np.int64(108), np.int64(109), np.int64(110), np.int64(111), np.int64(112), np.int64(113), np.int64(114), np.int64(115), np.int64(116), np.int64(117), np.int64(118), np.int64(119), np.int64(120), np.int64(121), np.int64(122), np.int64(123), np.int64(124), np.int64(125), np.int64(126), np.int64(127), np.int64(128), np.int64(129), np.int64(130)] (V=[0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.67, 0.68, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19, 1.2, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.3])
  val: columns with any >1: [np.int64(126), np.int64(127), np.int64(128)] (V=[1.26, 1.27, 1.28])
  test: columns with any <0: [np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7), np.int64(8), np.int64(9), np.int64(10), np.int64(11), np.int64(12), np.int64(13), np.int64(14), np.int64(15), np.int64(16), np.int64(17), np.int64(18), np.int64(71), np.int64(72), np.int64(73), np.int64(74), np.int64(75), np.int64(76), np.int64(77), np.int64(78), np.int64(79), np.int64(80), np.int64(81), np.int64(98), np.int64(99), np.int64(100), np.int64(101), np.int64(102), np.int64(103), np.int64(104), np.int64(105), np.int64(106), np.int64(107), np.int64(108), np.int64(109), np.int64(110), np.int64(111), np.int64(112), np.int64(113), np.int64(114), np.int64(115), np.int64(116), np.int64(117), np.int64(124), np.int64(125), np.int64(126), np.int64(127), np.int64(128), np.int64(129), np.int64(130)] (V=[0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.71, 0.72, 0.73, 0.74, 0.75, 0.76, 0.77, 0.78, 0.79, 0.8, 0.81, 0.98, 0.99, 1.0, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09, 1.1, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29, 1.3])
  test: columns with any >1: [np.int64(76), np.int64(77), np.int64(78), np.int64(79), np.int64(80), np.int64(81), np.int64(82), np.int64(83), np.int64(84), np.int64(85), np.int64(86), np.int64(87), np.int64(88), np.int64(89), np.int64(90), np.int64(111), np.int64(112), np.int64(113), np.int64(114), np.int64(115), np.int64(116), np.int64(117), np.int64(118), np.int64(119), np.int64(120), np.int64(121)] (V=[0.76, 0.77, 0.78, 0.79, 0.8, 0.81, 0.82, 0.83, 0.84, 0.85, 0.86, 0.87, 0.88, 0.89, 0.9, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19, 1.2, 1.21])

saved train_only_scalers.pkl
saved leakage_free_dataset.npz
