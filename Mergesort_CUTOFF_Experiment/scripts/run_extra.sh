set -e
JVMS=${1:-6}; ROUNDS=${2:-8}
JOPTS="-Xms2g -Xmx2g -Xmn1200m -XX:+UseSerialGC -Dstdout.encoding=UTF-8"
rm -f results/raw_scaling_jvm*.csv results/raw_validation_jvm*.csv
for j in $(seq 1 $JVMS); do
  java $JOPTS -cp bin ScalingExperiment $j $ROUNDS results/raw_scaling_jvm$j.csv 1,7,10,24 data
done
for j in $(seq 1 $JVMS); do
  java $JOPTS -cp bin ValidationExperiment $j $ROUNDS results/raw_validation_jvm$j.csv 1,7,10,16,24,32 100000,1000000
done
python3 scripts/analyze.py
