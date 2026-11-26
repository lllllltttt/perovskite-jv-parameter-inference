# -*- coding: utf-8 -*-
"""Drive the ten formal trainings (2 arms x 5 seeds).

One worker thread per arm; within an arm the five seeds run sequentially.  Both
arms therefore experience the same concurrent CPU load at every seed step.
A failed run is recorded and the driver continues with the next seed; nothing
is retried silently.
"""
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "config", "experiment_config.json")
LOG = os.path.join(ROOT, "logs", "driver.log")

with open(CONFIG, encoding="utf-8") as f:
    CFG = json.load(f)
SEEDS = [int(s) for s in CFG["design"]["training_seeds"]]
ARMS = ["original", "expanded"]

os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
lock = threading.Lock()


def say(msg):
    with lock:
        line = "[%s] %s" % (datetime.now(timezone.utc).strftime("%H:%M:%S"), msg)
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def worker(arm):
    for seed in SEEDS:
        t0 = time.time()
        say("start %s %d" % (arm, seed))
        env = dict(os.environ)
        env["TF_CPP_MIN_LOG_LEVEL"] = "2"
        env["TF_ENABLE_ONEDNN_OPTS"] = "0"
        env["TF_NUM_INTRAOP_THREADS"] = "8"
        env["TF_NUM_INTEROP_THREADS"] = "2"
        p = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "03_train.py"),
             "--arm", arm, "--seed", str(seed), "--quiet"],
            cwd=ROOT, env=env, capture_output=True, text=True)
        with open(os.path.join(ROOT, "logs", "stdout_%s_%d.txt" % (arm, seed)),
                  "w", encoding="utf-8") as f:
            f.write(p.stdout + "\n--- stderr ---\n" + p.stderr)
        say("end   %s %d rc=%d wall=%.0fs"
            % (arm, seed, p.returncode, time.time() - t0))


def main():
    th = [threading.Thread(target=worker, args=(a,), daemon=False) for a in ARMS]
    for t in th:
        t.start()
    for t in th:
        t.join()

    status = {}
    for arm in ARMS:
        for seed in SEEDS:
            rj = os.path.join(ROOT, "logs", "%s_%d" % (arm, seed), "run.json")
            if os.path.exists(rj):
                with open(rj, encoding="utf-8") as f:
                    r = json.load(f)
                status["%s_%d" % (arm, seed)] = {
                    "status": r.get("status"),
                    "epochs_run": r.get("epochs_run"),
                    "best_epoch": r.get("best_epoch"),
                    "stop_reason": r.get("stop_reason"),
                    "wall_s": r.get("wall_s"),
                    "error": r.get("error"),
                }
            else:
                status["%s_%d" % (arm, seed)] = {"status": "missing"}
    with open(os.path.join(ROOT, "logs", "formal_run_status.json"), "w",
              encoding="utf-8") as f:
        json.dump(status, f, indent=2)
    say("DONE %s" % json.dumps(
        {k: v["status"] for k, v in status.items()}))
    n_ok = sum(v["status"] == "completed" for v in status.values())
    return 0 if n_ok == 10 else 1


if __name__ == "__main__":
    sys.exit(main())
