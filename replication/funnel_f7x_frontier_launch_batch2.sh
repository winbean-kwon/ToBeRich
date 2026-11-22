# 3+2 switch (2026-11-22 17:58 KST): run seeds 3333, 4444 after seeds 0,1111,2222 reach END.
OUT=~/f4work/frontier/f7out
until [ "$(cat $OUT/s0.log $OUT/s1111.log $OUT/s2222.log 2>/dev/null | grep -c END)" -ge 3 ]; do sleep 300; done
echo "$(date -Is) second batch start" >> $OUT/batch2.log
for S in 3333 4444; do echo "$(date -Is) stopped by resource action at 135 pairs (not counted as attempt)" >> $OUT/s$S.log; bash ~/f4work/frontier/f7_run.sh $S & done; wait
echo "$(date -Is) second batch END" >> $OUT/batch2.log
