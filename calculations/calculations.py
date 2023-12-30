#!/usr/bin/python

# motor and speed calculations


# %% Constants
import math

motor_torque = 0.03  # Nm
motor_rps = 1 / 4  # revolutions per second
door_weight = 0.7  # kg

d_motor = 0.012  # m
r_motor = d_motor / 2

F_motor = motor_torque / r_motor  # N
print(f"{F_motor=:.3f} N")


d_outer = 0.04  # m
d_inner = 0.02  # m

F_pulley = F_motor * d_outer / d_inner  # N
print(f"{F_pulley=:.3f} N")

print(f"Max weigth: {F_pulley / 9.81:.3f} kg")

# F = T/r


gear_ratio = d_outer / d_motor  # 12 teeth on motor, 40 on pulley

pulley_circumference = d_inner * math.pi

lift_height = 0.4  # m

# % ---- calculations ----
rps = motor_rps / gear_ratio

feed_rate = rps * pulley_circumference  # m/s

print(f"{feed_rate=:.3f} m/s")


t_lift = lift_height / feed_rate  # s
print(f"{t_lift=:.2f} s")

#
