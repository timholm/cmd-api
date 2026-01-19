#\!/bin/bash
cd ~/cmd-api
nohup python3 server.py > ~/cmd-api/server.log 2>&1 &
echo $\! > ~/cmd-api/server.pid
echo "Started server with PID $(cat ~/cmd-api/server.pid)"
