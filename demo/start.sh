cd $(dirname $0)

DIZZY_DATA_ROOT=./custom_data

#get pid
python serve.py & > /dev/null
SERVE_PID=$!
sleep 2

python request.py
kill $SERVE_PID
