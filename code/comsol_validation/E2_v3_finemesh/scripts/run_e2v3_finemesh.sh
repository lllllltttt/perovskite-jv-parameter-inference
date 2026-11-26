#!/bin/bash
# run_e2v3_finemesh.sh -- E2-v3 FINER mesh grades m=0.18 / m=0.125.
# 12 rows (6 reps x {m0.18, m0.125}, stol 1e-6) over 4 COMSOL servers, chunk=3 rows each.
# Mirrors the round-2 launcher: kill stale servers, start 4, wait LISTENING,
# 4 MATLAB -batch workers (e2v3_comsol_batch 4-arg), final `wait`.
# Read-only model load; nothing under matlab&mph or old outputs is touched.
V3=/e/project/work1/supplementary_validation_v3/E2_finemesh
SCR="$V3/scripts"
CHUNKS="$V3/_work/chunks"
CUR="$V3/outputs/curves"
LOG="$V3/_work/logs"
SERVER="/e/comsol6_3/COMSOL63/Multiphysics/bin/win64/comsolmphserver.exe"
MATLAB="/e/MatlabR2024b/bin/win64/MATLAB.exe"
mkdir -p "$CHUNKS" "$LOG" "$CUR"

# 1) kill any stale servers on our ports
for p in 2061 2062 2063 2064; do
  pid=$(netstat -ano 2>/dev/null | grep ":$p " | grep LISTENING | awk '{print $NF}' | head -1)
  [ -n "$pid" ] && taskkill //PID "$pid" //F >/dev/null 2>&1
done
sleep 2

# 2) start 4 servers
for p in 2061 2062 2063 2064; do
  "$SERVER" -port "$p" > "$LOG/srvE2v3_$p.log" 2> "$LOG/srvE2v3_$p.err.log" &
done

# 3) wait for listening
for p in 2061 2062 2063 2064; do
  ok=0
  for i in $(seq 1 90); do
    if netstat -ano 2>/dev/null | grep -q ":$p .*LISTENING"; then ok=1; break; fi
    sleep 2
  done
  echo "port $p listening=$ok"
done

# 4) launch 4 MATLAB workers
WIN="E:\\project\\work1\\supplementary_validation_v3\\E2_finemesh"
idx=0
for p in 2061 2062 2063 2064; do
  WINCHUNK="$WIN\\_work\\chunks\\e2v3_fm_chunk_$idx.csv"
  WINCUR="$WIN\\outputs\\curves"
  WINLOG="$WIN\\_work\\logs\\e2v3_fm_$idx.log"
  WINSD="$WIN\\scripts"
  "$MATLAB" -sd "$WINSD" -batch "e2v3_comsol_batch($p,'$WINCHUNK','$WINCUR','$WINLOG')" \
      > "$LOG/e2v3_fm_$idx.log.out" 2> "$LOG/e2v3_fm_$idx.log.err" &
  idx=$((idx+1))
done
# keep launcher alive until workers finish (reaper guard)
wait
echo "E2V3_ALL_DONE rows=$(ls "$CUR"/row_*.csv 2>/dev/null | wc -l)"
