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

if [ $# != 4 ];
then
    echo "Usage: bash train_distribute_gpu.sh [DEVICE_NUM] [VISIABLE_DEVICES(0,1,2,3,4,5,6,7)] \
         [DATA_PATH] [TRAIN_SPLIT_FILE_PATH]"
    exit 1
fi

if [ $1 -lt 1 ] && [ $1 -gt 8 ]
then
    echo "error: DEVICE_NUM=$1 is not in (1-8)"
exit 1
fi

export DEVICE_NUM=$1
export RANK_SIZE=$1
export CUDA_VISIBLE_DEVICES="$2"

mpirun -n $1 --allow-run-as-root --output-filename log_output --merge-stderr-to-stdout \
python3 train.py --device_target GPU --run_distribute 1 --device_num $1 \
--data_path $3 --train_split_file_path $4  > train_distribute_gpu.log 2>&1 &
