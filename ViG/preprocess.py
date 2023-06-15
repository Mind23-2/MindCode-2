# Copyright 2022 Huawei Technologies Co., Ltd
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
"""preprocess"""
import argparse
import json
import os

parser = argparse.ArgumentParser('preprocess')
parser.add_argument('--dataset_name', type=str, choices=["imagenet2012"], default="imagenet2012")
parser.add_argument('--data_path', type=str, default='', help='eval data dir')
def create_label(result_path, dir_path):
    """
    create_label
    """
    dirs = os.listdir(dir_path)
    file_list = []
    for file in dirs:
        file_list.append(file)
    file_list = sorted(file_list)
    total = 0
    img_label = {}
    for i, file_dir in enumerate(file_list):
        files = os.listdir(os.path.join(dir_path, file_dir))
        for f in files:
            img_label[f] = i
        total += len(files)
    json_file = os.path.join(result_path, "imagenet_label.json")
    with open(json_file, "w+") as label:
        json.dump(img_label, label)
    print("[INFO] Completed! Total {} data.".format(total))

args = parser.parse_args()
if __name__ == "__main__":
    create_label('./preprocess_Result/', args.data_path)
