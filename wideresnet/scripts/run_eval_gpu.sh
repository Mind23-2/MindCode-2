#!/bin/bash
# Copyright 2020-2021 Huawei Technologies Co., Ltd
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

if [ $# != 3 ]
then 
    echo "Usage: bash run_eval_gpu.sh [DATASET_PATH] [CONFIG_PATH] [CHECKPOINT_PATH]"
exit 1
fi

get_real_path(){
  if [ "${1:0:1}" == "/" ]; then
    echo "$1"
  else
    realpath -m "$PWD"/"$1"
  fi
}

DATASET_PATH=$(get_real_path "$1")
CONFIG_PATH=$(get_real_path "$2")
CHECKPOINT_PATH=$(get_real_path "$3")

if [ ! -d "$DATASET_PATH" ]
then 
    echo "error: DATASET_PATH='$DATASET_PATH' is not a directory"
exit 1
fi 

if [ ! -f "$CONFIG_PATH" ]
then 
    echo "error: CHECKPOINT_PATH=$CONFIG_PATH is not a file"
exit 1
fi 

if [ ! -f "$CHECKPOINT_PATH" ]
then 
    echo "error: CHECKPOINT_PATH=$CHECKPOINT_PATH is not a file"
exit 1
fi 

#ulimit -u unlimited
export DEVICE_NUM=1
export DEVICE_ID=0
export RANK_SIZE=$DEVICE_NUM
export RANK_ID=0

if [ -d "eval" ];
then
    rm -rf ./eval
fi
mkdir ./eval
cp ../*.py ./eval
cp -- *.sh ./eval
cp -r ../src ./eval
cd ./eval || exit
env > env.log
echo "start evaluation for device $DEVICE_ID"
python eval.py --device_target "GPU" --data_path="$DATASET_PATH" --config_path="$CONFIG_PATH" --checkpoint_file_path="$CHECKPOINT_PATH" &> log &
cd ..
