#!/bin/bash
#
# Script to manage (i.e., install, run, stop, get the status of, etc.) the pocket1090 application
#
# Usage: ./pocket1090.sh {'install','run','stop','status','clean'}
#
# N.B.
#   * This expects that the python environment is already configured -- e.g., 'workon POCKET_1090'
#   * The 'clean' command must be run under sudo (just to make sure)
#   * For static/desktop operation, export "LAT" and "LON" values of current location
#

COMMANDS="install, start, stop, status, clean"

if [ "$#" -ne 1 ]; then
    echo "Must provide command, i.e., one of: ${COMMANDS}"
    exit 1
fi

CMD=$1

INSTALL_PATH="/opt/pocket1090/"

POCKET1090_PATH="${HOME}/Code/pocket1090/"

DUMP1090_PATH="${HOME}/Code2/dump1090/"

DUMP1090_BIN="${DUMP1090_PATH}dump1090"

VERBOSE=

LOG_LEVEL="-L INFO"

LOG_FILE=

JSON_FILE_PATH="/tmp/"

DUMP1090_OUTPUT_FILE="/tmp/fa.txt"

DISTRO=$(cat /etc/*-release | grep -w NAME | cut -d= -f2 | tr -d '"')

if [ "${DISTRO}" == "Ubuntu" ]; then
    OPTIONS="${LOG_LEVEL} ${LOG_FILE} -p ${LAT},${LON} -o 0.0,0.0,0.0"
elif [ "${DISTRO}" == "Raspian GNU/Linux" ]; then
    OPTIONS="${LOG_LEVEL} ${LOG_FILE}"
fi

export PYTHONPATH="${PYTHONPATH}:${INSTALL_PATH}"

if [ "${CMD}" == "install" ]; then
    if [ -d "${INSTALL_PATH}" ]; then
        echo "Install directory exists"
    else
        echo "Creating install directory: ${INSTALL_PATH}"
        sudo mkdir ${INSTALL_PATH}
        sudo chmod 0755 ${INSTALL_PATH}
    fi
    ASSETS_PATH="${INSTALL_PATH}assets"
    if [ -d "${ASSETS_PATH}" ]; then
        echo "Assets directory exists"
    else
        echo "Creating assets directory: ${ASSETS_PATH}"
        sudo mkdir "${ASSETS_PATH}"
    fi

    echo "Copying files to ${INSTALL_PATH}"
    sudo cp ${DUMP1090_BIN} ${INSTALL_PATH}
    sudo cp ${POCKET1090_PATH}*.py ${INSTALL_PATH}

    echo "Asset files to ${ASSETS_PATH}"
    sudo cp ${POCKET1090_PATH}assets/*.png "${ASSETS_PATH}"
elif [ "${CMD}" == "start" ]; then
    echo "Starting the dump1090 server in the background"
#    ${INSTALL_PATH}/dump1090 --write-json ${JSON_FILE_PATH} > ${DUMP1090_OUTPUT_FILE} &

    echo "Starting the pocket1090 application in the background"
#    ${INSTALL_PATH}/pocket1090.py ${VERBOSE} ${OPTIONS} ${JSON_FILE_PATH} &
elif [ "${CMD}" == "stop" ]; then
    echo "Stopping the pocket1090 application"
    for KILLPID in `ps -ef | awk '$9~/^.*pocket1090.py$/ {print $2}'`; do kill $KILLPID; done

    echo "Stopping the dump1090 server"
    for KILLPID in `ps -ef | awk '$8~/^.*dump1090$/ {print $2}'`; do kill $KILLPID; done
elif [ "${CMD}" == "status" ]; then
    DUMP_PIDS=`ps -ef | awk '$8~/^.*dump1090$/ {print $2}'`
    if [ $? == 0 ] && [ "$DUMP_PIDS" != "" ]; then
        echo "    dump1090 Server Running:" $DUMP_PIDS
    else
        echo "    dump1090 Server Not Running"
    fi
    POCK_PIDS=`ps -ef | awk '$9~/^.*pocket1090.py$/ {print $2}'`
    if [ $? == 0 ] && [ "$POCK_PIDS" != "" ]; then
        echo "    pocket1090 Application Running:" $POCK_PIDS
    else
        echo "    pocket1090 Application Not Running"
    fi
elif [ "${CMD}" == "clean" ]; then
    rm -rf "${INSTALL_PATH}"
else
    echo "ERROR: invalid command: ${CMD} -- must be one of ${COMMANDS}"
    exit 1
fi

exit 0
