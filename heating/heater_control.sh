#!/bin/bash

HEATER_EN=25
HEATER_FAULT=5

PM_HEATER_EN=11
PM_HEATER_FAULT=7

# Set GPIO directions
gpio -g mode $HEATER_EN out
gpio -g mode $PM_HEATER_EN out
gpio -g mode $HEATER_FAULT in
gpio -g mode $PM_HEATER_FAULT in

case $1 in
  heater-on)
    gpio -g write $HEATER_EN 1
    ;;
  heater-off)
    gpio -g write $HEATER_EN 0
    ;;
  pm-heater-on)
    gpio -g write $PM_HEATER_EN 1
    ;;
  pm-heater-off)
    gpio -g write $PM_HEATER_EN 0
    ;;
  fault)
    gpio -g read $HEATER_FAULT
    gpio -g read $PM_HEATER_FAULT
    ;;
  *)
    echo "Unknown command"
    ;;
esac
