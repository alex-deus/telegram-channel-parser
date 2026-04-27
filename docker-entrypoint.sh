#!/usr/bin/env sh

case "$1" in
  shell)
    shift
    exec sh -c "$*"
    ;;
  sleep)
    exec sh -c "while true; do sleep 20; done"
    ;;
  cli)
    shift
    exec ./cli.py "$@"
    ;;
esac
