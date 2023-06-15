#!/bin/bash
# Copyright 2021 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================

if [[ $# -gt 4 ]]; then 
    echo "Usage: bash ./scripts/run_distribute_train_ascend.sh [RANK_TABLE] [DEVICE_NUM] [RANK_SIZE] [DATASET_NAME]"
exit 1
fi

ulimit -u unlimited
export DEVICE_NUM=$2
export RANK_SIZE=$3
RANK_TABLE_FILE=$(realpath $1)
export RANK_TABLE_FILE
echo "RANK_TABLE_FILE=${RANK_TABLE_FILE}"

for((i=0; i<${DEVICE_NUM}; i++))
do
    export DEVICE_ID=$i
    export RANK_ID=$i
    rm -rf ./train_parallel$i
    mkdir ./train_parallel$i
    cp -r ./src ./train_parallel$i
    cp ./train.py ./train_parallel$i
    echo "start training for rank $RANK_ID, device $DEVICE_ID"
    cd ./train_parallel$i ||exit
    env > env.log
    python train.py --device_id=$DEVICE_ID --dataset_name=$4 > log 2>&1 &
    cd ..
done
