import chess
import chess.engine

ELO = 1500


def get_player_move(board):
    while True:
        text = input("Your Turn: ").strip()

        if text == "quit":
            return None
        try:
            move = chess.Move.from_uci(text)
            if move in board.legal_moves:
                return move
        except ValueError:
            pass
        try:
            return board.parse_san(text)
        except ValueError:
            print("Illegal or non existing turn, please try again")


def main():
    board = chess.Board()
    engine = chess.engine.SimpleEngine.popen_uci("stockfish")
    engine.configure({"UCI_LimitStrength": True, "UCI_Elo": ELO})

    try:
        while not board.is_game_over():
            print()
            print(board)
            print()

            if board.turn == chess.WHITE:
                move = get_player_move(board)
                if move is None:
                    print("game canceled")
                    break
            else:
                result = engine.play(board, chess.engine.Limit(time=0.5))
                move = result.move
                print(f"engine plays {board.san(move)}")

            board.push(move)

            if board.is_check() and not board.is_game_over():
                print("Check")

        if board.is_game_over():
            print()
            print(board)
            print()
            print(f"Result: {board.result()}")
            outcome = board.outcome()
            print(f"Reason: {outcome.termination.name}")

    finally:
        engine.quit()


if __name__ == "__main__":
    main()
