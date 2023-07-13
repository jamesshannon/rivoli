#!/bin/bash

# move me to end
rm -rf ./processor/build
mkdir -p ./processor/build/third_party

if [[ -d $1 ]]; then
  cp -r $1 ./processor/build/third_party
fi
cp -r protos ./processor/build/
docker build -t rivoli-backend ./processor/
