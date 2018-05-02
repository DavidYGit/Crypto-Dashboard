#!/bin/bash

pip install -r install.txt
python createtable.py &
sleep 10
python createdash.py &
sleep 10
xdg-open http://127.0.0.1:8050/dash/
