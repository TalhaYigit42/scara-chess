import math
import serial

SERIAL_PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
PULSE_MIN_US = 500
PULSE_MAX_US = 2500
PWM_FREQUENCY = 50
PWM_RESOLUTION = 4096
PERIOD_US = 1_000_000 / PWM_FREQUENCY
TICK_US = PERIOD_US / PWM_RESOLUTION
GEAR_RADIUS_MM = 32
SERVOS = {
    "shoulder": {"channel": 0, "offset": 0, "min": 0, "max": 180},
    "elbow": {"channel": 1, "offset": 0, "min": 0, "max": 180},
    "z": {"channel": 2, "offset": 0, "min": 0, "max": 180},
}


def angle_to_pulse_us(angle):
    pulseWidth = PULSE_MIN_US + ((angle / 180) * (PULSE_MAX_US - PULSE_MIN_US))
    return pulseWidth


def pulse_us_to_ticks(pulse_us):
    ticks = round(pulse_us / TICK_US)
    return ticks


def height_to_angle(height_mm):
    angle = math.degrees(height_mm / GEAR_RADIUS_MM)
    return angle


if __name__ == "__main__":
    for angle, expected in ((0, 102), (90, 307), (180, 512)):
        ticks = pulse_us_to_ticks(angle_to_pulse_us(angle))
        status = "ok" if ticks == expected else f"WRONG, expected {expected}"
        print(f"{angle:>3} deg -> {ticks} ticks  {status}")

    for height, expected in ((0, 0.0), (84, 150.4), (100, 179.0)):
        angle = height_to_angle(height)
        status = "ok" if abs(angle - expected) < 0.1 else f"WRONG, expected {expected}"
        print(f"{height:>3} mm  -> {angle:.1f} deg  {status}")
