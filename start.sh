#!/usr/bin/env bash

python3 alcohol_study.py
until [ $? -eq 0 ]; do
    python3 alcohol_study.py
done