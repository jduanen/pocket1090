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
    echo "ERROR: Must provide command, i.e., one of: ${COMMANDS}"
    exit 1
fi

CMD=$1

INSTALL_PATH="/opt/pocket1090/"

POCKET1090_PATH="${HOME}/Code/pocket1090/"

VERBOSE=

LOG_LEVEL=

LOG_FILE=

DISTRO=$(cat /etc/*-release | grep -w NAME | cut -d= -f2 | tr -d '"')

if [ "${DISTRO}" == "Ubuntu" ]; then
    POCKET_OPTIONS="${LOG_LEVEL} ${LOG_FILE} -p ${LAT},${LON} -o 0.0,0.0,0.0"
    DUMP_OPTIONS="--quiet --metric  --json-stats-every 0 --adaptive-range"
    DUMP1090_PATH="${HOME}/Code2/dump1090/"
    DUMP1090_BIN="${DUMP1090_PATH}dump1090"
    JSON_FILE_PATH="/tmp"
    CONFIG_FILE="${HOME}/Code/pocket1090/pocket1090.yml"
elif [ "${DISTRO}" == "Raspbian GNU/Linux" ]; then
    POCKET_OPTIONS="${LOG_LEVEL} ${LOG_FILE}"
    DUMP_OPTIONS="--quiet --metric  --json-stats-every 0"
    DUMP1090_PATH="${HOME}/Code2/dump1090/"
    DUMP1090_BIN="${DUMP1090_PATH}package-bullseye/dump1090"
    JSON_FILE_PATH="/run/user/1000"
    CONFIG_FILE="${HOME}/Code/pocket1090/pocket1090.yml"
fi

export PYTHONPATH="${PYTHONPATH}:${INSTALL_PATH}"

install() {
    if [ -d "${INSTALL_PATH}" ]; then
        echo "    Install directory exists"
    else
        echo "    Creating install directory: ${INSTALL_PATH}"
        sudo mkdir ${INSTALL_PATH}
        sudo chmod 0755 ${INSTALL_PATH}
    fi
    ASSETS_PATH="${INSTALL_PATH}assets"
    if [ -d "${ASSETS_PATH}" ]; then
        echo "    Assets directory exists"
    else
        echo "    Creating assets directory: ${ASSETS_PATH}"
        sudo mkdir "${ASSETS_PATH}"
    fi

    echo "    Copying files to ${INSTALL_PATH}"
    sudo cp ${DUMP1090_BIN} ${INSTALL_PATH}
    sudo cp ${POCKET1090_PATH}*.{py,yml,sh} ${INSTALL_PATH}

    echo "    Asset files to ${ASSETS_PATH}"
    sudo cp ${POCKET1090_PATH}assets/*.png "${ASSETS_PATH}"
}

start_dump() {
    ${INSTALL_PATH}dump1090 ${DUMP_OPTIONS} --write-json ${JSON_FILE_PATH} &
}

start_pocket() {
    ${INSTALL_PATH}pocket1090.py ${VERBOSE} ${POCKET_OPTIONS} -c ${CONFIG_FILE} ${JSON_FILE_PATH} &
}

start() {
    echo "    Starting the dump1090 server in the background"
    start_dump

    echo "     Starting the pocket1090 application in the background"
    start_pocket
}

kill_pocket() {
    for KILLPID in `ps -ef | awk '$9~/^.*pocket1090.py$/ {print $2}'`; do kill $KILLPID; done
}

kill_dump() {
    for KILLPID in `ps -ef | awk '$8~/^.*dump1090$/ {print $2}'`; do kill $KILLPID; done
}

stop() {
    echo "    Stopping the pocket1090.py application"
    kill_pocket

    echo "    Stopping the dump1090 server"
    kill_dump
    sleep 3

    status
}

status() {
    n=0
    DUMP_PIDS=`ps -ef | awk '$8~/^.*dump1090$/ {print $2}'`
    if [ $? == 0 ] && [ "$DUMP_PIDS" != "" ]; then
        echo "    dump1090 Server Running:" $DUMP_PIDS
        ((n+=1))
    else
        echo "    dump1090 Server Not Running"
    fi
    POCK_PIDS=`ps -ef | awk '$9~/^.*pocket1090.py$/ {print $2}'`
    if [ $? == 0 ] && [ "$POCK_PIDS" != "" ]; then
        echo "    pocket1090 Application Running:" $POCK_PIDS
        ((n+=1))
    else
        echo "    pocket1090 Application Not Running"
    fi
    if [[ $n -eq 2 ]]; then
        return 0
    else
        return 1
    fi
}

clean() {
    rm -rf "${INSTALL_PATH}"
}

if [ "${CMD}" == "install" ]; then
    echo "  Installing pocket1090..."
    install
elif [ "${CMD}" == "start" ]; then
    echo "  Starting pocket1090..."
    start
elif [ "${CMD}" == "stop" ]; then
    echo "    Stopping the pocket1090 application"
    stop
elif [ "${CMD}" == "status" ]; then
    echo "  Getting status of pocket1090"
    status
    exit $?
elif [ "${CMD}" == "start_pocket" ]; then
    echo "  Starting the pocket1090.py application"
    start_pocket
elif [ "${CMD}" == "start_dump" ]; then
    echo "  Starting the dump1090 application"
    start_dump
elif [ "${CMD}" == "kill_pocket" ]; then
    echo "  Killing the pocket1090.py application"
    kill_pocket
elif [ "${CMD}" == "kill_dump" ]; then
    echo "  Killing the dump1090 application"
    kill_dump
elif [ "${CMD}" == "clean" ]; then
    echo "  Removing the installed pocket1090 files/directories"
    clean
else
    echo "ERROR: invalid command: ${CMD} -- must be one of ${COMMANDS}"
    exit 1
fi

exit 0
