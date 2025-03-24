cd $(dirname $0)

DIZZY_DATA_ROOT=./custom_data

#get pid
python serve.py & > /dev/null
SERVE_PID=$!
sleep 2

if [ -n "$SERVE_PID" ]; then
    python request.py
    kill $SERVE_PID
else
    echo "Server not running, failed?"
fi
