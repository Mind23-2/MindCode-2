# Copyright 2020-2022 Huawei Technologies Co., Ltd
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
"""Dataset preprocessing."""
import os
import multiprocessing
import math as m
import numpy as np
from PIL import Image
import mindspore.common.dtype as mstype
import mindspore.dataset as ds
import mindspore.dataset.transforms as c
import mindspore.dataset.vision as vc
from src.model_utils.config import config


class _CaptchaDataset:
    """
    create train or evaluation dataset for warpctc

    Args:
        img_root_dir(str): root path of images
        max_captcha_digits(int): max number of digits in images.
        device_target(str): platform of training, support Ascend and GPU.
    """

    def __init__(self, img_root_dir, max_captcha_digits, device_target='Ascend'):
        if not os.path.exists(img_root_dir):
            raise RuntimeError("the input image dir {} is invalid!".format(img_root_dir))
        self.img_root_dir = img_root_dir
        self.img_names = [i for i in os.listdir(img_root_dir) if i.endswith('.png')]
        self.max_captcha_digits = max_captcha_digits
        self.target = device_target
        self.blank = 10
        self.label_length = [len(os.path.splitext(n)[0].split('-')[-1]) for n in self.img_names]

    def __len__(self):
        return len(self.img_names)

    def __getitem__(self, item):
        img_name = self.img_names[item]
        im = Image.open(os.path.join(self.img_root_dir, img_name))
        r, g, b = im.split()
        im = Image.merge("RGB", (b, g, r))
        image = np.array(im)
        label_str = os.path.splitext(img_name)[0]
        label_str = label_str[label_str.find('-') + 1:]
        label = [int(i) for i in label_str]
        label.extend([int(self.blank)] * (self.max_captcha_digits - len(label)))
        label = np.array(label)
        return image, label


def create_dataset(dataset_path, batch_size=1, num_shards=1, shard_id=0, device_target='Ascend',
                   num_parallel_workers=8):
    """
     create train or evaluation dataset for warpctc

     Args:
        dataset_path(str): dataset path
        batch_size(int): batch size of generated dataset, default is 1
        num_shards(int): number of devices
        shard_id(int): rank id
        device_target(str): platform of training, support Ascend and GPU
        num_parallel_workers(int): Number of data processing threads.
     """
    cores = multiprocessing.cpu_count()
    if num_parallel_workers > cores:
        print("The num_parallel_workers {} is set too large, now set it {}".format(num_parallel_workers, cores))
        num_parallel_workers = cores
    dataset = _CaptchaDataset(dataset_path, config.max_captcha_digits, device_target)
    data_set = ds.GeneratorDataset(dataset, ["image", "label"], shuffle=True, num_shards=num_shards, shard_id=shard_id)

    image_trans = [
        vc.Rescale(1.0 / 255.0, 0.0),
        vc.Normalize([0.9010, 0.9049, 0.9025], std=[0.1521, 0.1347, 0.1458]),
        vc.Resize((m.ceil(config.captcha_height / 16) * 16, config.captcha_width)),
        vc.HWC2CHW()
    ]
    label_trans = [
        c.TypeCast(mstype.int32)
    ]
    data_set = data_set.map(operations=image_trans, input_columns=["image"],
                            num_parallel_workers=num_parallel_workers)
    data_set = data_set.map(operations=label_trans, input_columns=["label"],
                            num_parallel_workers=num_parallel_workers)

    data_set = data_set.batch(batch_size, drop_remainder=True)
    return data_set
