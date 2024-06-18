#!/bin/bash

HEATER_EN=25
PM_HEATER_EN=11

# Set GPIO directions to PWM
gpio -g mode $HEATER_EN pwm
gpio -g mode $PM_HEATER_EN pwm

case $1 in
  heater-on)
    duty_cycle=$((255 * 5 / 100))  # 5% duty cycle
    gpio -g pwm $HEATER_EN $duty_cycle
    ;;
  heater-off)
    gpio -g pwm $HEATER_EN 0
    ;;
  pm-heater-on)
    duty_cycle=$((255 * 5 / 100))  # 5% duty cycle
    gpio -g pwm $PM_HEATER_EN $duty_cycle
    ;;
  pm-heater-off)
    gpio -g pwm $PM_HEATER_EN 0
    ;;
  *)
    echo "Unknown command"
    ;;
esac
