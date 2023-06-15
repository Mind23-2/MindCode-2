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
""" main.py """
import argparse
import os
from StreamManagerApi import StreamManagerApi, StringVector
from StreamManagerApi import MxDataInput, InProtobufVector, MxProtobufIn
import MxpiDataType_pb2 as MxpiDataType
import numpy as np


shape = [1, 128, 128, 64]

def parse_args(parsers):
    """
    Parse commandline arguments.
    """
    parsers.add_argument('--images_txt_path', type=str,
                         default="../data/infer_data/infer_anno.txt",
                         help='image text')
    return parsers


def read_file_list(input_file):
    """
    :param infer file content:
        1.bin 0
        2.bin 2
        ...
    :return image path list, label list
    """
    image_file = []
    if not os.path.exists(input_file):
        print('input file does not exists.')
    with open(input_file, "r") as fs:
        for line in fs.readlines():
            image_file.append(line.split()[0])
    return image_file


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Om vnet Inference')
    parser = parse_args(parser)
    args, _ = parser.parse_known_args()
    # init stream manager
    stream_manager = StreamManagerApi()
    ret = stream_manager.InitManager()
    if ret != 0:
        print("Failed to init Stream manager, ret=%s" % str(ret))
        exit()

    # create streams by pipeline config file
    with open("../data/config/vnet.pipeline", 'rb') as f:
        pipeline = f.read()
    ret = stream_manager.CreateMultipleStreams(pipeline)
    if ret != 0:
        print("Failed to create Stream, ret=%s" % str(ret))
        exit()

    # Construct the input of the stream

    res_dir_name = 'result'
    if not os.path.exists(res_dir_name):
        os.makedirs(res_dir_name)

    file_list = read_file_list(args.images_txt_path)

    img_size = len(file_list)
    results = []

    for idx, file in enumerate(file_list):
        image_path = os.path.join(args.images_txt_path.replace('infer_anno.txt', 'img'), file)

        # Construct the input of the stream
        data_input = MxDataInput()
        with open(image_path, 'rb') as f:
            data = f.read()
        data_input.data = data
        tensorPackageList1 = MxpiDataType.MxpiTensorPackageList()
        tensorPackage1 = tensorPackageList1.tensorPackageVec.add()
        tensorVec1 = tensorPackage1.tensorVec.add()
        tensorVec1.deviceId = 0
        tensorVec1.memType = 0
        for t in shape:
            tensorVec1.tensorShape.append(t)
        tensorVec1.dataStr = data_input.data
        tensorVec1.tensorDataSize = len(data)
        protobufVec1 = InProtobufVector()
        protobuf1 = MxProtobufIn()
        protobuf1.key = b'appsrc0'
        protobuf1.type = b'MxTools.MxpiTensorPackageList'
        protobuf1.protobuf = tensorPackageList1.SerializeToString()
        protobufVec1.push_back(protobuf1)

        unique_id = stream_manager.SendProtobuf(b'vnet', b'appsrc0', protobufVec1)

        keyVec = StringVector()
        keyVec.push_back(b'mxpi_tensorinfer0')
        infer_result = stream_manager.GetProtobuf(b'vnet', 0, keyVec)
        if infer_result.size() == 0:
            print("inferResult is null")
            exit()
        if infer_result[0].errorCode != 0:
            print("GetProtobuf error. errorCode=%d" % (
                infer_result[0].errorCode))
            exit()
        # get infer result
        result = MxpiDataType.MxpiTensorPackageList()
        result.ParseFromString(infer_result[0].messageBuf)
        res = np.frombuffer(result.tensorPackageVec[0].tensorVec[0].dataStr, dtype=np.float32).reshape(1, 128, 128, 64)
        res.tofile('./result/' + file)

    # destroy streams
    stream_manager.DestroyAllStreams()
