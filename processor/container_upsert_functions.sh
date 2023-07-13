#!/bin/sh

# This script creates function JSON file(s) and upserts them into the active
# mongodb database. It creates function entities for all Rivoli functions plus
# every package that's been copied to third_party/

mkdir -p functions

./generate_function_entities.py ./functions/rivoli.json

for D in ./third_party/*; do
  if [ -d "${D}" ]; then
    module=$(basename $D)
    echo $module
    ./generate_function_entities.py --module $module ./functions/$module.json
  fi
done

./upsert_functions.py functions/
