#!/bin/bash

HEATER_EN=25
HEATER_FAULT=5

PM_HEATER_EN=11
PM_HEATER_FAULT=7

pinctrl set $HEATER_EN op
pinctrl set $PM_HEATER_EN op
pinctrl set $HEATER_FAULT ip
pinctrl set $PM_HEATER_FAULT ip

case $1 in
  heater-on)
    pinctrl set $HEATER_EN dh
    ;;
  heater-off)
    pinctrl set $HEATER_EN dl
    ;;
  pm-heater-on)
    pinctrl set $PM_HEATER_EN dh
    ;;
  pm-heater-off)
    pinctrl set $PM_HEATER_EN dl
    ;;
  fault)
    pinctrl get $HEATER_FAULT
    pinctrl get $PM_HEATER_FAULT
    ;;
  *)
    echo "Unknown command"
    ;;
esac
