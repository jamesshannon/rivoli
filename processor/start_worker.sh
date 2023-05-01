#!bin/sh

celery -A rivoli.celery_app worker -B
