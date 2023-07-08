#!/bin/sh

./export_collections.py --csv_header

sqlite3 database.db "drop table records"
sqlite3 database.db ".import --csv records.csv records"

sqlite3 database.db "drop table files"
sqlite3 database.db ".import --csv files.csv files"
