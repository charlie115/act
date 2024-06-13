#!/bin/bash
USERDEPLOYER="root"
#VARIABLES
SERVICE_NAME="trade_core_main.py"
USERDEPLOYER="root"
FOLDER=/home/trade_core
KEYWORD="python3.9"

if [[ `/usr/bin/whoami` == $USERDEPLOYER ]]
  then

    pushd .
    echo "Stopping $SERVICE_NAME......"

    #KILLING PROCESS
    processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
    echo "Trying to kill process with key $SERVICE_NAME - ignore error messages below."
    kill -9 $processPID
    sleep 2

    #KILLING PROCESS AGAIN
    processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
    echo "Trying to kill process with key $SERVICE_NAME - ignore error messages below."
    kill -9 $processPID
    sleep 5

    while [ -n "$processPID" ]
      do
    echo "Waiting process ($processPID) to shutdown...5s"
    sleep 5
        processPID=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`
      done

    echo "Ensured process with key $SERVICE_NAME is no longer running."
    popd

    #CHECKING SYSTEM STATUS
    PROC=`ps -ef | grep $SERVICE_NAME | grep $KEYWORD | grep -v grep | awk -F" " '{ print $2 }'`;

    if [ $PROC ]; then
      echo "$SERVICE_NAME is running!"
      echo "Stop then first!"
      exit
    fi
else
  echo "User must be $USERDEPLOYER !"
fi

pm2 restart trade_core # Restart will be handled by PM2 automatically. 