#! /bin/bash
cd $(dirname $0)

DIZZY_DATA_ROOT=./custom_data

#get pid
python serve.py &
SERVE_CODE=$?
SERVE_PID=$!
if [ $SERVE_CODE -ne 0 ]; then
    echo "Server failed to start"
    exit 1
fi

sleep 1

#if server is running, send request
if ps -p $SERVE_PID > /dev/null; then
    echo "Server running, PID: $SERVE_PID"
    python request.py

    if ps -p $SERVE_PID > /dev/null; then
        echo "Killing server"
        kill -2 $SERVE_PID
    else
        echo "Server not running, failed?"
    fi

    if ps -p $SERVE_PID > /dev/null; then
        echo "Server still running, failed?"
    else
        echo "Server killed, done."
    fi
else
    echo "Server not running, failed?"
fi
