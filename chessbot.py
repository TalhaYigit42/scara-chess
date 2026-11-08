import os
import socket
import sys
import time

import cv2
import numpy as np
import chess
import chess.engine
from camera import open_camera, grab, calibrate, warp, compare_images, detect_move, print_top

#Settings

CORNER_NAMES = ["a1", "h1", "h8", "a8"]
SIZE = 800
SQ = SIZE // 8
points = []
ELO=1500

#Camera

#coming soon lol