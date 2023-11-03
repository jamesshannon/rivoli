#!/bin/bash

# Make the temporary build directories and then copy relevant build files
mkdir -p ./processor/build/third_party
mkdir -p ./webui/build

if [[ -d $1 ]]; then
  cp -r $1 ./processor/build/third_party
fi
cp -r protos ./processor/build/
cp -r protos ./webui/build

# Make the files input directory
mkdir -p ~/Documents/rivoli/input_files

docker build -t rivoli-backend ./processor/
docker build -t rivoli-webui ./webui/

# Remove the build directories
rm -rf ./processor/build
rm -rf ./webui/build
