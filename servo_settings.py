import math

from kinematics import inverse_kinematics, square_to_xy

PULSE_MIN_US = 500
PULSE_MAX_US = 2500
PWM_FREQUENCY = 50  # Hz
PWM_RESOLUTION = 4096  # steps per period
PERIOD_US = 1_000_000 / PWM_FREQUENCY  # 20 000 us
TICK_US = PERIOD_US / PWM_RESOLUTION  # 4.8828125 us
GEAR_RADIUS_MM = 32

SERVOS = {
    "shoulder": {"channel": 0, "offset": 0, "min": 0, "max": 180},
    "elbow": {"channel": 1, "offset": 0, "min": 0, "max": 180},
    "z": {"channel": 2, "offset": 0, "min": 0, "max": 180},
}


def angle_to_pulse_us(angle):
    return PULSE_MIN_US + (angle / 180) * (PULSE_MAX_US - PULSE_MIN_US)


def pulse_us_to_ticks(pulse_us):
    return round(pulse_us / TICK_US)


def height_to_angle(height_mm):
    return math.degrees(height_mm / GEAR_RADIUS_MM)


def check_limits(joint, servo_angle):
    low = SERVOS[joint]["min"]
    high = SERVOS[joint]["max"]
    if not low <= servo_angle <= high:
        raise ValueError(f"{joint}: {servo_angle:.1f} deg outside {low}-{high}")


def joint_to_servo_angle(joint, value):
    if joint == "shoulder":
        servo_angle = value
    elif joint == "elbow":
        servo_angle = value + 180
    elif joint == "z":
        servo_angle = height_to_angle(value)
    else:
        raise ValueError(f"unknown joint: {joint}")

    servo_angle += SERVOS[joint]["offset"]
    check_limits(joint, servo_angle)
    return servo_angle


if __name__ == "__main__":
    for angle, expected in ((0, 102), (90, 307), (180, 512)):
        ticks = pulse_us_to_ticks(angle_to_pulse_us(angle))
        status = "ok" if ticks == expected else f"WRONG, expected {expected}"
        print(f"{angle:>3} deg -> {ticks} ticks  {status}")

    
    for height, expected in ((0, 0.0), (84, 150.4), (100, 179.0)):
        angle = height_to_angle(height)
        status = "ok" if abs(angle - expected) < 0.1 else f"WRONG, expected {expected}"
        print(f"{height:>3} mm  -> {angle:.1f} deg  {status}")

    
    x, y = square_to_xy(4, 3)
    theta1, theta2 = inverse_kinematics(x, y)
    for joint, value, expected in (("shoulder", theta1, 94.1), ("elbow", theta2, 70.8)):
        angle = joint_to_servo_angle(joint, value)
        status = "ok" if abs(angle - expected) < 0.1 else f"WRONG, expected {expected}"
        print(f"e4 {joint:<8} -> {angle:.1f} deg  {status}")

    
    for joint, value in (("z", 120), ("wrist", 10)):
        try:
            joint_to_servo_angle(joint, value)
            print(f"{joint} {value}: WRONG, no error")
        except ValueError as error:
            print(f"{joint} {value}: ok ({error})")