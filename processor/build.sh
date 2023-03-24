#!/bin/bash

# Fail hard
rm -rf ./rivoli/protos/*_pb2*
rm -rf ./rivoli/protos/__pycache__

python -m grpc_tools.protoc --proto_path=../protos/rivoli --pyi_out=./rivoli --python_out=./rivoli ../protos/rivoli/protos/*
