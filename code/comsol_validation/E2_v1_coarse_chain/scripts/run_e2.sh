#!/bin/bash
# run_e2.sh -- start 4 fresh COMSOL servers and 4 MATLAB E2 workers.
# Requires E1 to have finished (its MATLAB clients disconnect -> servers exit).
# The frozen model file is opened read-only; nothing is written under matlab&mph.
E2=/e/project/work1/supplementary_validation/E2
SCR="$E2/scripts"
CHUNKS="$E2/_work/chunks"
CUR="$E2/outputs/curves"
LOG="$E2/_work/logs"
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
declare -a SRV
for p in 2041 2042 2043 2044; do
  "$SERVER" -port "$p" > "$LOG/srvE2_$p.log" 2> "$LOG/srvE2_$p.err.log" &
  SRV+=($!)
done

# 3) wait for all four ports to LISTEN
for p in 2041 2042 2043 2044; do
  for i in $(seq 1 60); do
    if netstat -ano 2>/dev/null | grep -q ":$p .*LISTENING"; then break; fi
    sleep 2
  done
  echo "port $p listening? $(netstat -ano 2>/dev/null | grep -c ":$p .*LISTENING")"
done

# 4) launch 4 MATLAB workers (qc study.run validation only on chunk0)
declare -a WID
qc=0
idx=0
for p in 2041 2042 2043 2044; do
  if [ "$idx" -eq 0 ]; then qc=1; else qc=0; fi
  WIN="E:\\project\\work1\\supplementary_validation\\E2"
  WINCHUNK="$WIN\\_work\\chunks\\e2_chunk_$idx.csv"
  WINCUR="$WIN\\outputs\\curves"
  WINLOG="$WIN\\_work\\logs\\e2_full_$idx.log"
  WINSD="$WIN\\scripts"
  "$MATLAB" -sd "$WINSD" -batch "e2_comsol_batch($p,'$WINCHUNK','$WINCUR','$WINLOG',$qc)" \
      > "$LOG/e2_full_$idx.log.out" 2> "$LOG/e2_full_$idx.log.err" &
  WID+=($!)
  idx=$((idx+1))
done
echo "launched MATLAB PIDs: ${WID[*]}"
# Keep this shell alive until the workers finish: if it exits early the
# background-task reaper kills the child MATLAB processes (seen empirically).
echo "waiting for E2 workers to finish..."
wait
echo "E2_ALL_DONE rows=$(ls "$CUR"/row_*.csv 2>/dev/null | wc -l)"
