#! /bin/bash
cd $(dirname $0)

DIZZY_DATA_ROOT=./custom_data

cleanup() {
    if ps -p $SERVE_PID > /dev/null; then
        echo "Killing server"
        kill -2 $SERVE_PID  # Send SIGINT
        sleep 1              # Wait for a moment to allow graceful shutdown
        if ps -p $SERVE_PID > /dev/null; then
            echo "Server did not terminate, forcing kill"
            kill -9 $SERVE_PID  # Force kill if still running

            if ps -p $SERVE_PID > /dev/null; then
                echo "Server still running, failed?"
            else
                echo "Server killed, done."
            fi
        fi
    fi
    exit 0
}
trap cleanup SIGINT
trap cleanup SIGTERM

# Start the server
python serve.py &
SERVE_CODE=$?
SERVE_PID=$!
if [ $SERVE_CODE -ne 0 ]; then
    echo "Server failed to start..."
    exit 1
fi
sleep 1

# Start the client
if ps -p $SERVE_PID > /dev/null; then
    echo "Server running, PID: $SERVE_PID"
    python request.py
else
    echo "Server no longer running, failed?"
fi