#!/bin/bash

fuser -k 8050/tcp
pkill -f createdash.py
