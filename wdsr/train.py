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
"""wdsr train script"""
import os
from mindspore import context
from mindspore import dataset as ds
import mindspore.nn as nn
from mindspore.context import ParallelMode
from mindspore.train.serialization import load_checkpoint, load_param_into_net
from mindspore.communication.management import init, get_rank
from mindspore.train.callback import ModelCheckpoint, CheckpointConfig, LossMonitor, TimeMonitor
from mindspore.common import set_seed
from mindspore.train.model import Model
from mindspore.train.loss_scale_manager import DynamicLossScaleManager
from src.args import args
from src.data.div2k import DIV2K
from src.model import WDSR

def train_net():
    """train wdsr"""
    set_seed(1)
    if args.device_target == 'GPU':
        context.set_context(mode=context.GRAPH_MODE,
                            device_target=args.device_target,
                            device_id=args.device_id,
                            save_graphs=False)
    elif args.device_target == 'Ascend':
        device_id = int(os.getenv('DEVICE_ID', '0'))
        rank_id = int(os.getenv('RANK_ID', '0'))
        device_num = int(os.getenv('RANK_SIZE', '1'))
        context.set_context(mode=context.GRAPH_MODE,
                            device_target="Ascend",
                            save_graphs=False,
                            device_id=device_id)
    rank = 0
    # if distribute:
    if args.run_distribute:
        print("distribute")
        if args.device_target == 'GPU':
            init("nccl")
            device_num = args.device_num
            context.reset_auto_parallel_context()
            rank = get_rank()
            context.set_auto_parallel_context(device_num=device_num, parallel_mode=ParallelMode.DATA_PARALLEL,
                                              gradients_mean=True)
        elif args.device_target == 'Ascend':
            init()
            context.set_auto_parallel_context(parallel_mode=ParallelMode.DATA_PARALLEL,
                                              device_num=device_num, gradients_mean=True)

    train_dataset = DIV2K(args, name=args.data_train, train=True, benchmark=False)
    train_dataset.set_scale(args.task_id)
    if args.device_target == 'GPU':
        train_de_dataset = ds.GeneratorDataset(train_dataset, ["LR", "HR"],
                                               num_shards=args.device_num,
                                               shard_id=rank, shuffle=True)
    elif args.device_target == 'Ascend':
        train_de_dataset = ds.GeneratorDataset(train_dataset, ["LR", "HR"],
                                               num_shards=device_num,
                                               shard_id=rank_id, shuffle=True)
    train_de_dataset = train_de_dataset.batch(args.batch_size, drop_remainder=True)
    net_m = WDSR(scale=args.scale[args.task_id], n_resblocks=args.n_resblocks, n_feats=args.n_feats)
    print("Init net successfully")
    if args.ckpt_path:
        param_dict = load_checkpoint(args.ckpt_path)
        load_param_into_net(net_m, param_dict)
        print("Load net weight successfully")
    step_size = train_de_dataset.get_dataset_size()
    lr = []
    for i in range(0, args.epochs):
        cur_lr = args.lr / (2 ** ((i + 1)//args.decay))
        lr.extend([cur_lr] * step_size)
    opt = nn.Adam(net_m.trainable_params(), learning_rate=lr, loss_scale=args.loss_scale)
    loss = nn.L1Loss()
    loss_scale_manager = DynamicLossScaleManager(init_loss_scale=args.init_loss_scale, \
             scale_factor=2, scale_window=1000)
    model = Model(net_m, loss_fn=loss, optimizer=opt, loss_scale_manager=loss_scale_manager)
    time_cb = TimeMonitor(data_size=step_size)
    loss_cb = LossMonitor()
    cb = [time_cb, loss_cb]
    config_ck = CheckpointConfig(save_checkpoint_steps=args.ckpt_save_interval * step_size,
                                 keep_checkpoint_max=args.ckpt_save_max)
    ckpt_cb = ModelCheckpoint(prefix="wdsr", directory=args.ckpt_save_path, config=config_ck)
    if rank == 0:
        cb += [ckpt_cb]
    model.train(args.epochs, train_de_dataset, callbacks=cb, dataset_sink_mode=True)


if __name__ == "__main__":
    train_net()
