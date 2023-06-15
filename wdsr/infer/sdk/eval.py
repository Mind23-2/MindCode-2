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
"""eval for sdk"""
import argparse
import os
import math
import cv2
import numpy as np


def parser_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label_dir", type=str, default="../data/DIV2K/label/",
                        help="path of label images directory")
    parser.add_argument("--infer_dir", type=str, default="output", help="path of infer images directory")
    parser.add_argument("--scale", type=int, default=2)
    return parser.parse_args()


def calc_psnr(sr, hr, scale, rgb_range):
    """calculate psnr"""
    hr = np.float32(hr)
    sr = np.float32(sr)
    diff = (sr - hr) / rgb_range
    gray_coeffs = np.array([65.738, 129.057, 25.064]).reshape((1, 3, 1, 1)) / 256
    diff = np.multiply(diff, gray_coeffs).sum(1)
    if hr.size == 1:
        return 0
    if scale != 1:
        shave = scale
    else:
        border_add = 6
        shave = scale + border_add
    if scale == 1:
        valid = diff
    else:
        valid = diff[..., shave:-shave, shave:-shave]
    mse = np.mean(pow(valid, 2))
    return -10 * math.log10(mse)


if __name__ == '__main__':
    args = parser_args()
    infer_path_list = os.listdir(args.infer_dir)
    infer_path_list.sort()
    total_num = len(infer_path_list)
    mean_psnr = 0.0
    for infer_p in infer_path_list:
        infer_path = os.path.join(args.infer_dir, infer_p)
        label_path = os.path.join(args.label_dir, infer_p.replace('_infer', ''))
        print(infer_p)
        infer_img = cv2.imread(infer_path)
        label_img = cv2.imread(label_path)
        infer_img = np.expand_dims(infer_img, 0).transpose((0, 3, 1, 2))
        label_img = np.expand_dims(label_img, 0).transpose((0, 3, 1, 2))

        psnr = calc_psnr(infer_img, label_img, args.scale, 255.0)
        mean_psnr += psnr/total_num
        print("current psnr: ", psnr)
    print('Mean psnr of %s images is %.4f' % (total_num, mean_psnr))
    