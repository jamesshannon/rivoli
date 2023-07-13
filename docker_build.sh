#!/bin/bash

mkdir -p ./processor/build/third_party
mkdir -p ./webui/build

if [[ -d $1 ]]; then
  cp -r $1 ./processor/build/third_party
fi
cp -r protos ./processor/build/
cp -r protos ./webui/build

docker build -t rivoli-backend ./processor/
docker build -t rivoli-webui ./webui/

rm -rf ./processor/build
rm -rf ./webui/build
