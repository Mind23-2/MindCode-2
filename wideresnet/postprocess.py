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
"""post process for 310 inference"""
import os
import numpy as np
from src.model_utils.config import config as cfg

batch_size = 1


def get_top5_acc(top5_arg, gt_class):
    sub_count = 0
    for top5, gt in zip(top5_arg, gt_class):
        if gt in top5:
            sub_count += 1
    return sub_count


def cal_acc_cifar10(result_path, label_path):
    """
    result_path: path of preprocess image
    label_path: path of label
    """
    top1_correct = 0
    top5_correct = 0
    img_tot = 0

    result_shape = (1, 10)

    files = os.listdir(result_path)
    for _file in files:
        full_file_path = os.path.join(result_path, _file)
        if os.path.isfile(full_file_path):
            result = np.fromfile(full_file_path, dtype=np.float32).reshape(result_shape)
            label_file = os.path.join(label_path, _file.split(".bin")[0][:-2] + ".bin")
            gt_classes = np.fromfile(label_file, dtype=np.int32)

            top1_output = np.argmax(result, (-1))
            top5_output = np.argsort(result)[:, -5:]

            t1_correct = np.equal(top1_output, gt_classes).sum()
            top1_correct += t1_correct
            top5_correct += get_top5_acc(top5_output, [gt_classes])
            img_tot += 1
    top1_correct = float(top1_correct)
    img_tot = float(img_tot)
    top1_acc = top1_correct/img_tot
    print("top1_acc", top1_acc)
    top5_correct = float(top5_correct)
    top5_acc = top5_correct/img_tot
    print("top5_acc", top5_acc)


if __name__ == '__main__':

    cal_acc_cifar10(cfg.result_path, cfg.label_path)
