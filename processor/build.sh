#!/bin/bash

# Fail hard
rm -rf ./src/rivoli/protos/*_pb2*
rm -rf ./src/rivoli/protos/__pycache__

python -m grpc_tools.protoc --proto_path=../protos --pyi_out=./src \
  --python_out=./src ../protos/rivoli/protos/*
