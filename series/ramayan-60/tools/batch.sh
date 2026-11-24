#!/bin/bash
# Make episodes end to end: batch.sh 3 4 5 ...  (stops cleanly when the budget cap is reached)
cd "$(dirname "$0")/.."
for n in "$@"; do
  if [ -f "$(printf 'ep%02d/out/Ramayan_Ep%02d.mp4' $n $n)" ]; then echo "ep$n: done already"; continue; fi
  python3 tools/voice.py $n && python3 tools/images.py $n | tail -1 && python3 tools/compose.py $n || { echo "ep$n: FAILED"; [ -f STOP ] && exit 1; python3 -c "import sys; sys.path.insert(0,'tools'); import fal; sys.exit(fal._spend() > fal.BUDGET - 0.3)" || exit 1; }
done
python3 -c "import sys; sys.path.insert(0,'tools'); import fal; print(f'estimated spend: \${fal._spend():.2f}')"
