#!/usr/bin/env python3

import serial, sys, time, pygame

MSG_START = 0x7f
MSG_LEN = 9

def checksum(msg):
    cs = sum(msg[:MSG_LEN-1]) - 1
    return cs & 0x7f == msg[-1]

def decode(b):
    try:
        return int(f"{b:02x}")
    except ValueError:
        print("\nErr, cant convert", hex(b))
        return int(b)

try:
    #ser = serial.Serial("/dev/ttyUSB1", 2400, 7)
    ser = open("countdown.dump", 'rb')
except FileNotFoundError as e:
    sys.exit("Seriele poort niet gevonden, USB kabel ingeplugged?, {e}")
except serial.serialutil.SerialException as e:
    sys.exit(f"Kan seriele poort niet openen: {e}")

WHITE = (255,255,255)
BLACK = (0,0,0)
RED   = (255,0,0)
GREEN = (0,255,0)
BLUE  = (0,0,255)
CHROMA_KEY  = (96,144,144)

WINDOW_SIZE = (640, 480)

pygame.init()
font = pygame.font.SysFont("Roboto-Bold.ttf", 48)

screen = pygame.display.set_mode( WINDOW_SIZE )
extra_bit = 0x8
last_sec = 0
while True:
    ## handle user close window event
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(0)

    try: #get in sync until end of file
        if ser.read(1)[0] != MSG_START: continue
    except IndexError: break

    rawmsg = ser.read(MSG_LEN)
    if len(rawmsg) != MSG_LEN: continue ## go for resync

    print("RAW:", " ".join([f"{x:02x}" for x in rawmsg[:-1]]), "        ")

    if not checksum(rawmsg):
        print("CHECKSUM ERROR")
        continue

    green = decode(rawmsg[0])
    red   = decode(rawmsg[1])
    if rawmsg[2]&0xF != 0xF:
        msec = 0
        sec = decode(rawmsg[2])
        min = decode(rawmsg[3])
        last_sec = sec
    else:
        if rawmsg[2]>>4 == 7: extra_bit = 0x0
        if rawmsg[3] != last_sec: extra_bit = 0x8
        msec = (decode(rawmsg[2]>>4) | extra_bit) * 100
        sec  = decode(rawmsg[3])
        min  = 0
        last_sec = sec
    gled = (rawmsg[4]>>3) & 1
    rled = (rawmsg[4]>>2) & 1
    assert(rawmsg[4]&3 == 0) ## if any of these bits ever get set I want to know!
    match   = decode(rawmsg[5])
    tim     = decode(rawmsg[6])
    penalty = decode(rawmsg[7])

    print(f"{green:2d} [{gled}] <{min:02d}:{sec:02d}:{msec:03d}> [{rled}] {red:2d} -- {tim:2d} {penalty:2d} {match:2d}", end="\r")

    lab_time = font.render(f" {min:02d}:{sec:02d}:{msec:03d} ", False, WHITE, BLACK)
    lab_gscore = font.render(f" {green:2d} [{gled}] ", False, WHITE, GREEN)
    lab_rscore = font.render(f" [{rled}] {red:2d} ", False, WHITE, RED)

    Wt, Ht = font.size(f" {min:02d}:{sec:02d}:{msec:03d} ")
    Wg, Hg = font.size(f" {green:2d} [{gled}] ")
    Y = WINDOW_SIZE[1] - 1.5 * Ht

    screen.fill( CHROMA_KEY )
    screen.blit(lab_time, ((WINDOW_SIZE[0] - Wt)//2, Y) )
    screen.blit(lab_gscore, ((WINDOW_SIZE[0] - Wt)//2 - Wg, Y) )
    screen.blit(lab_rscore, ((WINDOW_SIZE[0] + Wt)//2, Y) )
    pygame.display.flip()

    time.sleep(.015)
print()

