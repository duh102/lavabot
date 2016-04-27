#!/bin/bash
thisDir=$(dirname $0)
source ${thisDir}/env/bin/activate
python ${thisDir}/lavabot.py
deactivate
