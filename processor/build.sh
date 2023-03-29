#!/bin/bash

# Fail hard
rm -rf ./src/rivoli/protos/*_pb2*
rm -rf ./src/rivoli/protos/__pycache__

python -m grpc_tools.protoc --proto_path=../protos/rivoli \
  --pyi_out=./src/rivoli --python_out=./src/rivoli \
  ../protos/rivoli/protos/*
