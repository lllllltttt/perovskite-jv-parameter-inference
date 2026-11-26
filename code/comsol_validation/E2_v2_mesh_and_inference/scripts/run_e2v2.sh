#!/bin/bash
# run_e2v2.sh -- E2-v2 fine-mesh + fine-mesh tolerance recheck solves.
# 18 rows (6 reps x {m0.35, m0.25, m0.25 stol1e-7}) over 4 COMSOL servers.
# Copy of the round-1 E2 worker (read-only model load, mesh bases via getDouble,
# size+size1 scaled, sol1.runAll). Nothing under matlab&mph or old outputs is written.
V2=/e/project/work1/supplementary_validation_v2/E2_mesh_and_inference
SCR="$V2/scripts"
CHUNKS="$V2/_work/chunks"
CUR="$V2/outputs/curves"
LOG="$V2/_work/logs"
SERVER="/e/comsol6_3/COMSOL63/Multiphysics/bin/win64/comsolmphserver.exe"
MATLAB="/e/MatlabR2024b/bin/win64/MATLAB.exe"
mkdir -p "$CHUNKS" "$LOG" "$CUR"

# 1) kill any stale servers on our ports
for p in 2041 2042 2043 2044; do
  pid=$(netstat -ano 2>/dev/null | grep ":$p " | grep LISTENING | awk '{print $NF}' | head -1)
  [ -n "$pid" ] && taskkill //PID "$pid" //F >/dev/null 2>&1
done
sleep 2

# 2) start 4 servers
for p in 2041 2042 2043 2044; do
  "$SERVER" -port "$p" > "$LOG/srvE2v2_$p.log" 2> "$LOG/srvE2v2_$p.err.log" &
done

# 3) wait for listening
for p in 2041 2042 2043 2044; do
  ok=0
  for i in $(seq 1 60); do
    if netstat -ano 2>/dev/null | grep -q ":$p .*LISTENING"; then ok=1; break; fi
    sleep 2
  done
  echo "port $p listening=$ok"
done

# 4) launch 4 MATLAB workers
WIN="E:\\project\\work1\\supplementary_validation_v2\\E2_mesh_and_inference"
idx=0
for p in 2041 2042 2043 2044; do
  WINCHUNK="$WIN\\_work\\chunks\\e2v2_chunk_$idx.csv"
  WINCUR="$WIN\\outputs\\curves"
  WINLOG="$WIN\\_work\\logs\\e2v2_full_$idx.log"
  WINSD="$WIN\\scripts"
  "$MATLAB" -sd "$WINSD" -batch "e2v2_comsol_batch($p,'$WINCHUNK','$WINCUR','$WINLOG',0)" \
      > "$LOG/e2v2_full_$idx.log.out" 2> "$LOG/e2v2_full_$idx.log.err" &
  idx=$((idx+1))
done
# keep launcher alive until workers finish (reaper guard)
wait
echo "E2V2_ALL_DONE rows=$(ls "$CUR"/row_*.csv 2>/dev/null | wc -l)"
