#!/bin/bash

# move me to end
rm -rf ./processor/build
rm -rf ./webui/build

mkdir -p ./processor/build/third_party

if [[ -d $1 ]]; then
  cp -r $1 ./processor/build/third_party
fi
cp -r protos ./processor/build/
cp -r protos ./webui/build

docker build -t rivoli-backend ./processor/
docker build -t rivoli-webui ./webui/
