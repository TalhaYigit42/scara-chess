# Chess Robot

A chess robot with a 2-link SCARA arm that plays against you on a real wooden board. A camera watches the board, the program decides on a move, and the arm picks up and places the pieces.

> **Status: work in progress.** The chess logic, camera calibration and arm kinematics work. The mechanical parts are designed and being printed. The ESP32 firmware is not in this repo yet.

## How it works

```
camera ──> move detection ──> chess logic ──> kinematics ──> servos
(OpenCV)   (compare squares)   (python-chess)  (IK, angles)   (ESP32 + PCA9685)
```

1. The camera is calibrated once on the empty board and once on the starting position.
2. After every move it checks which squares changed and works out the move.
3. The chess logic validates the move, and Stockfish (limited to 1500 Elo) picks a reply.
4. The kinematics turn the target square into shoulder and elbow angles.
5. A Z axis (rack and pinion) lifts the arm, and the gripper grabs the piece.

Special moves are broken into simple pick-and-place actions:

- **Capture:** move the captured piece to the box first, then make the move.
- **Castling:** king first, then rook.
- **En passant:** remove the pawn next to the target square.
- **Promotion:** pawn to the box, queen from the reserve.

## Design decisions

### The board

Everything starts from the real board (measured from a CAD drawing, in mm):

| | Value |
|---|---|
| Board outside | 364.3 × 364.3 |
| Border (outer edge → grid) | 19.5 |
| Square | 38.3 |
| Line between squares | 2.1 |
| **Square centre → square centre** | **40.4** |
| Board thickness | 61.3 |
| Tallest piece (king) | 69 |

### Where the arm stands

The shoulder sits **30 mm in front of both board edges, diagonally off the a1 corner**. The centre of a1 is 19.5 + 2.1 + 19.15 = 40.75 mm from the board edge, plus 30 mm gives 70.75 mm. So every square centre is at

```
x = 7.075 + 4.04 · file     y = 7.075 + 4.04 · rank     (cm, file/rank = 0…7)
```

That puts a1 at **10.01 cm** and h8 at **50.0 cm** from the shoulder.

### Why 26 cm per link

- A straight arm reaches `L1 + L2`. The farthest square is h8 at 50 cm, and I added **2 cm reserve** so the arm never has to be fully stretched: `L1 + L2 = 52 cm`.
- I made both links **the same length**, so **L1 = L2 = 26 cm**. That makes the triangle shoulder–elbow–gripper isosceles, which keeps the math simple (see [MATH.md](MATH.md)). It also lets the arm fold up completely, because `|L1 − L2| = 0`.

### Why link 2 runs above link 1

The nearest square is the problem, not the farthest one. With the links side by side, the elbow can only bend to about 150°. That gives a minimum reach of `2 · 26 · sin(15°) ≈ 13.46 cm`, so **a1, a2 and b1 would be unreachable**.

Solving `2 · 26 · sin(x/2) = 10.01` gives an inner angle of 22.2°, so the elbow has to bend to **θ2 ≈ 158°**. That only works if **link 2 runs one level above link 1** and can swing over it, like real SCARA robots do. The elbow servo points up and link 2 sits on its horn, with a 608ZZ bearing to take the load off the servo.

### Which of the two IK solutions

Every point can be reached with the elbow on either side. I use the solution where `θ1 = β + α`. Over all 64 squares it keeps the shoulder between **57.4° and 136.6°**, so it fits a 0–180° servo without any offset. The elbow then needs a range of 126°.

### The Z axis

The whole arm moves up and down on a carriage: two 8 mm rods with LM8UU bearings, and an MG996R with a gear that climbs a fixed rack.

- **How high:** the gripper takes a piece about 1 cm above the board. While carrying it, the bottom of the piece should be 1.5 cm above the king (6.9 cm). So the carriage has to lift **about 8.4 cm**.
- **Gear:** module 1, 64 teeth, pitch radius 32 mm. The height is `Δz = r · Δθ`, so **1° ≈ 0.56 mm** and the 84 mm need **about 150°** of servo travel. A full 180° would give 100 mm.
- **Load:** torque = weight × radius. With a 32 mm radius, the MG996R (about 10 kg·cm) has plenty of reserve for the arm.
- The board is 6.13 cm thick, so the column stands on the table and the gripper starts working above that height.

### Seeing the board

Black pieces on dark squares are hard to tell apart, so the camera does not try to recognise every piece. It is calibrated on the empty board and on the starting position, then only checks **which squares changed** after a move. Since the program always knows the current position, this is enough to work out the move. Coloured dots on the pieces are plan B, if this turns out to be unreliable.

### Sound

The menu and moves get sound through a DFPlayer Mini. I connected my power supply the wrong way round once and burned its built-in amplifier. The DAC output still worked, so I built my own **single-transistor amplifier** (2N2222A, voltage divider bias, emitter resistor with bypass capacitor, potentiometer for volume) on a perfboard.

### Parts sourcing

Since July 2026 the EU charges an extra import fee on every item in small parcels from China. For a cart full of cheap parts, the fees were higher than the parts themselves, so I bought from EU shops and Amazon.de instead.

## Hardware

| Part | Use |
|---|---|
| ESP32 DevKit | controller |
| PCA9685 | 16-channel servo driver |
| 3× MG996R | shoulder, elbow, Z axis |
| SG90 | gripper |
| 2× 8 mm rods, 4× LM8UU, 4× SK8 | Z axis guide |
| 608ZZ bearings | shoulder and elbow |
| DFPlayer Mini + transistor amp | sound |
| OLED 0.96" + buttons | menu |
| USB webcam | board recognition |
| 3D-printed parts (PETG / PLA) | column, carriage, arm, gripper, electronics box |

### Measured MG996R (calipers)

| | mm |
|---|---|
| Body | 40.35 × 19.75 × 39.3 |
| Mounting flange | 54.35 long, 2.85 thick, underside 28.6 above the bottom |
| Flange holes | Ø4.2, spaced 49.5 × 9.7 |
| Shaft | Ø5.75 × 5.8, 8.6 from the body edge |
| Round horn | Ø20.9, 2.3 thick, hub Ø8.7 × 3.2, 4 holes Ø1.5 on Ø14.3 |

## Project structure

| File | What it does |
|---|---|
| `src/chessbot.py` | main program (work in progress) |
| `src/camera.py` | camera calibration and move detection |
| `src/kinematics.py` | square → coordinates, inverse and forward kinematics, self test |
| `src/play_in_terminal.py` | play against the bot in the terminal, without hardware |
| `src/servo_settings.py` | joint angles → servo angles → PCA9685 ticks, limit checks |
| `firmware/` | ESP32 sketches (servo bridge) |
| `hardware/pcb/` | KiCad PCB design (not started yet) |
| `docs/` | notes, sketches, photos |

## Math

The full derivation (square coordinates, distance formula, inverse and forward kinematics, worked examples) is in **[MATH.md](MATH.md)**, together with photos of my hand-written notes. `kinematics.py` checks IK → FK on all 64 squares: **64/64 ok**.

## Getting started

```bash
git clone https://github.com/tkafka42/scara-chess.git
cd scara-chess
sudo pacman -S stockfish   # or the stockfish package of your distro
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python src/kinematics.py        # self test, should print 64/64 ok
python src/play_in_terminal.py  # play without the robot
```

## Roadmap

- [x] Chess logic with python-chess
- [x] Camera calibration
- [x] Inverse and forward kinematics, tested on all 64 squares
- [x] Sound output (DFPlayer + self-built transistor amplifier)
- [x] Z axis designed (column, carriage, rack, gear)
- [ ] Servo control: angle → PWM, calibration per servo
- [ ] Positions for the capture box, reserve and park position
- [ ] Shoulder boom, arm links and gripper
- [ ] ESP32 firmware: menu, sound, servo commands
- [ ] Smooth motion (interpolation between start and target)
- [ ] Later: Raspberry Pi 5 instead of laptop + ESP32, with a custom HAT PCB in KiCad

## CAD files

The CAD files for the robot (column, carriage, arm, gripper, electronics box) will be published here once everything is modelled and tested.

## How I use AI in this project

I write the code for this project myself. I use AI (Claude) as a tutor and reviewer:

- **Review and debugging:** checking my code and math, explaining error messages
- **Optimization:** suggestions for cleaner structure and naming
- **Research:** datasheets, wiring, libraries, concepts

I did the calculations in `MATH.md` myself (see the photos of my notes); AI checked them and pointed out mistakes. Some design ideas came out of those discussions, for example stacking the links, the transistor amplifier circuit and the gear/rack geometry for the Z axis.

Exceptions, so this stays honest:
- The self-test loop at the bottom of `kinematics.py` was written with AI help.
- `servo_settings.py`s self-test written with AI help.

## License

MIT, see [LICENSE](LICENSE).
