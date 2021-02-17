#!/bin/sh

set -euo pipefail

# Version of the config
CONFIG_VER=v0
CONFIG_DIR=${PWD}/torchbenchmark/score/configs/${CONFIG_VER}
CONFIG_ENV=${CONFIG_DIR}/config-${CONFIG_VER}.env
DATA_JSON_PREFIX=$(date +"%Y%m%d_%H%M%S")
DATA_DIR=$1

# Load environment variables
set -a;
source ${CONFIG_ENV}
set +a;
sudo nvidia-smi -ac ${GPU_FREQUENCY}
export CUDA_VISIBLE_DEVICES="${GPU_LIST}"
export GOMP_CPU_AFFINITY="${CORE_LIST}"

# Install benchmark dependencies
python install.py

# Run the benchmark
for c in $(seq 1 $NUM_ITER); do
    taskset -c "${CORE_LIST}" pytest test_bench.py -k "${BENCHMARK_FILTER}" \
            --benchmark-min-rounds "${NUM_ROUNDS}" \
            --benchmark-json ${DATA_DIR}/${DATA_JSON_PREFIX}_${c}.json
    # Fill in circle_build_num and circle_project_reponame
    jq --arg run_id "${GITHUB_RUN_ID}" --arg config_version "githubactions-benchmark-${CONFIG_VER}-metal-fullname" \
       '.machine_info.circle_project_name=$config_version | .machine_info.circle_build_num=$run_id' \
       ${DATA_DIR}/${DATA_JSON_PREFIX}_${c}.json > ${DATA_DIR}/${DATA_JSON_PREFIX}_${c}.json.tmp
    mv ${DATA_DIR}/${DATA_JSON_PREFIX}_${c}.json.tmp ${DATA_DIR}/${DATA_JSON_PREFIX}_${c}.json
done

echo "Benchmark finished successfully. Output data dir is ${DATA_DIR}."