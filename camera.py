import cv2
import numpy as np
import chess
import os
import sys

CORNER_NAMES = ["a1", "h1", "h8", "a8"]
SIZE = 800
SQ = SIZE // 8
points = []


def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
        points.append((x, y))


def calibrate(img):
    cv2.namedWindow("Board")
    cv2.setMouseCallback("Board", on_click)

    while len(points) < 4:
        view = img.copy()                       
        for (x, y) in points:                   
            cv2.circle(view, (x, y), 8, (0, 0, 255), -1)
        name = CORNER_NAMES[len(points)]        
        cv2.putText(view, f"Click {name}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        cv2.imshow("Board", view)
        cv2.waitKey(30)    

   
    src = np.float32(points)
    dst = np.float32([[0, SIZE], [SIZE, SIZE], [SIZE, 0], [0, 0]])
    return cv2.getPerspectiveTransform(src, dst)


def warp(img, matrix):
    return cv2.warpPerspective(img, matrix, (SIZE, SIZE))

def square_box(square, margin=0.0):
    file = chess.square_file(square)
    rank = chess.square_rank(square)
    x0 = file * SQ
    y0 = (7 - rank) * SQ
    m = int(SQ * margin)                
    return x0 + m, y0 + m, x0 + SQ - m, y0 + SQ - m
  
def draw_grid(warped):
  view = warped.copy()   
  for field in chess.SQUARES:
    x0,y0,x1,y1 = square_box(field)
    cv2.rectangle(view, (x0, y0), (x1, y1), (0, 255, 0), 1)
    name = chess.square_name(field)
    cv2.putText(view, name, (x0 + 5, y0 + 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
  return view

def prep(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)
  
def print_top(scores, n=6):
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:n]
    for sq, value in top:
        print(f"{chess.square_name(sq)}: {value:.1f}")

def compare_images(before, after):
    a = prep(before)
    b = prep(after)
    diff = cv2.absdiff(a, b)

    raw = {}
    for sq in chess.SQUARES:
        x0, y0, x1, y1 = square_box(sq, 0.15)
        part = diff[y0:y1, x0:x1]
        raw[sq] = float(part.mean())

    noise = float(np.median(list(raw.values())))
    scores = {}
    for sq, value in raw.items():
        scores[sq] = value - noise
    return scores
    
def wait_for_q():
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord("q"):
            break
          
def touched_squares(board, move):
    squares = {move.from_square, move.to_square}    
    rank = chess.square_rank(move.from_square)      
    
    if board.is_kingside_castling(move):
        squares |= {chess.square(7, rank), chess.square(5, rank)}

    elif board.is_queenside_castling(move):
        squares |= {chess.square(0, rank), chess.square(3, rank)}

    if board.is_en_passant(move):
        file = chess.square_file(move.to_square)
        squares.add(chess.square(file, rank))

    return squares

def detect_move(board, scores):
    best_move = None
    best_score = -1.0

    for move in board.legal_moves:
        if move.promotion and move.promotion != chess.QUEEN:
            continue

        squares = touched_squares(board, move)
        weakest = min(scores[sq] for sq in squares)

        if weakest>best_score:
          best_score= weakest
          best_move= move
          
    return best_move, best_score


if __name__ == "__main__":
    before = cv2.imread("imgs/before.png")
    after = cv2.imread("imgs/after.png")
    if before is None or after is None:
        sys.exit("Images not found, check imgs/before.png and imgs/after.png")

    if os.path.exists("calib.npy"):
        matrix = np.load("calib.npy")
    else:
        matrix = calibrate(before)
        np.save("calib.npy", matrix)

    warped_before = warp(before, matrix)
    warped_after = warp(after, matrix)

    scores = compare_images(warped_before, warped_after)
    print_top(scores)

    board = chess.Board()
    move, conf = detect_move(board, scores)
    print("Detected:", board.san(move), f"{conf:.1f}")

    cv2.imshow("Grid", draw_grid(warped_after))
    wait_for_q()
    cv2.destroyAllWindows()
    


