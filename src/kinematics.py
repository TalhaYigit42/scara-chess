import math

FIRST_SQUARE = 7.075
SQUARE_SIZE = 4.04
LINK_LENGTH = 26.0


def square_to_xy(file, rank):
    x = FIRST_SQUARE + SQUARE_SIZE * file
    y = FIRST_SQUARE + SQUARE_SIZE * rank
    return x, y


def inverse_kinematics(x, y):
    d = math.hypot(x, y)
    if d > LINK_LENGTH * 2:
        raise ValueError(f"target out of reach: d = {d:.1f} cm")

    else:
        phi = 2 * math.asin(d / (2 * LINK_LENGTH))
        angle02 = math.pi - phi
        beta = math.atan2(y, x)
        alpha = angle02 / 2
        angle01 = beta + alpha
        return math.degrees(angle01), math.degrees(-angle02)


def forward_kinematics(angle01, angle02):
    angle01 = math.radians(angle01)
    angle02 = math.radians(angle02)
    elbow_x = LINK_LENGTH * math.cos(angle01)
    elbow_y = LINK_LENGTH * math.sin(angle01)
    gripper_x = elbow_x + (LINK_LENGTH * math.cos(angle01 + angle02))
    gripper_y = elbow_y + (LINK_LENGTH * math.sin(angle01 + angle02))
    return gripper_x, gripper_y


if __name__ == "__main__":
    ok = 0
    for file in range(8):
        for rank in range(8):
            name = "abcdefgh"[file] + str(rank + 1)
            x, y = square_to_xy(file, rank)
            theta1, theta2 = inverse_kinematics(x, y)
            back_x, back_y = forward_kinematics(theta1, theta2)
            error = math.hypot(back_x - x, back_y - y)
            if error < 0.001:
                ok += 1
            else:
                print(
                    f"{name}: off by {error:.4f} cm  (theta1 {theta1:.2f}, theta2 {theta2:.2f})"
                )
    print(f"{ok}/64 ok")
