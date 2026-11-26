# -*- coding: utf-8 -*-
"""
Driver for the 15-run benchmark (3 families x 5 seeds) + evaluation.
Resume-safe: skips any run whose outdir already has a DONE marker.
Progress -> benchmark_progress.log; failures -> per-run FAILED marker + log.
"""
import os, sys, io, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SEEDS = [20260824, 20260825, 20260826, 20260827, 20260828]
FAMILIES = ["vae", "det_ae", "mlp"]
LOG = os.path.join(HERE, "benchmark_progress.log")


def log(msg):
    line = "[%s] %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    with io.open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    if os.path.exists(LOG):
        os.remove(LOG)
    from exp1_lib import train_one
    from evaluate_one import evaluate

    total = len(FAMILIES) * len(SEEDS)
    done = 0
    for fam in FAMILIES:
        for seed in SEEDS:
            outdir = os.path.join(HERE, "models", fam, "seed%d" % seed)
            done_marker = os.path.join(outdir, "DONE")
            if os.path.exists(done_marker):
                log("SKIP %s/%s (already done)" % (fam, seed))
                done += 1
                continue
            log("TRAIN %s/%s" % (fam, seed))
            try:
                t0 = time.time()
                _, history, secs = train_one(fam, seed, outdir)
                res = evaluate(fam, seed, outdir)
                with io.open(done_marker, "w", encoding="utf-8") as f:
                    f.write("family=%s seed=%s seconds=%.0f best_epoch=%d stop_epoch=%d\n" % (
                        fam, seed, secs, res["best_epoch"], res["stop_epoch"]))
                done += 1
                log("DONE %s/%s mean_r=%.4f (%d/%d, %.0fs, %d epochs)" % (
                    fam, seed, res["rows"][-1]["pearson_r"], done, total, secs,
                    res["stop_epoch"]))
            except Exception:
                log("FAILED %s/%s\n%s" % (fam, seed, traceback.format_exc()))
                os.makedirs(outdir, exist_ok=True)
                with io.open(os.path.join(outdir, "FAILED"), "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())
                done += 1
    log("BENCHMARK BATCH COMPLETE: %d/%d" % (done, total))
