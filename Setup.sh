#!/bin/bash

PROJECT_PATH=$PWD

cd $PROJECT_PATH

python -m venv venv || python3 -m venv venv

source /venv/bin/activate

pip install -r requirements.txt || pip3 install -r requirements.txt

export BACKEND_SCRIPT_PATH="$PROJECT_PATH/back.py"
export PID_FILE="$PROJECT_PATH/backend_process.pid"
export ERROR_FILE="$PROJECT_PATH/error_message.txt"
export ALERT_FILE="$PROJECT_PATH/alert.mp3"
export TEMPLATE_PATH="$PROJECT_PATH/templates"
export STATIC_PATH="$PROJECT_PATH/static"

cmd_path=$(which python || which python3)
$cmd_path "$PROJECT_PATH/front.py"




