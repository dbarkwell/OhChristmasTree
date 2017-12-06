import pyaudio
import threading
import os
import sys
import time
from random import randrange
from random import choice
from pocketsphinx import Decoder
from gpiozero import LEDBoard
from gpiozero.tools import random_values
from datetime import date

waiting = False
waiting_timer = None
light_timer = None
tree = LEDBoard(*range(2, 28), pwm=True)
star = tree[0]


def set_waiting_false():
    global waiting
    print('timeout')
    star.off()
    waiting = False
    complete_action()


def complete_command():
    global waiting
    global waiting_timer
    print('reset')
    light_down()
    waiting = False
    if waiting_timer is not None and waiting_timer.is_alive():
        waiting_timer.cancel()


def complete_action():
    light_up()


def wake_up():
    global waiting, waiting_timer
    stop_rock_around()
    waiting = True
    light_down()
    star.on()
    print("waiting")
    waiting_timer = threading.Timer(5.0, set_waiting_false)
    waiting_timer.start()


def good_bad():
    complete_command()
    behaviour = choice(['good', 'bad'])
    if behaviour == 'bad':
        print('bad')
        light_down()
    else:
        print('good')
        light_up()

    time.sleep(5)
    complete_action()


def how_many_presents():
    complete_command()
    present_count = randrange(1, 26)
    print(present_count)
    flash(present_count)
    complete_action()


def stop_rock_around():
    global tree
    for led in tree:
        led.source_delay = 0
        led.source = None


def rock_around():
    global waiting, tree
    complete_command()
    for led in tree:
        led.source_delay = 0.1
        led.source = random_values()


def light_down():
    tree.off()


def light_up():
    tree.on()


def flash(count):
    for p in range(0, count):
        light_up()
        time.sleep(0.75)
        light_down()
        time.sleep(0.75)
    time.sleep(3)


def how_many_days():
    complete_command()
    now = date.today()
    day = 25 - now.day
    if day < 0:
        day = 0

    print("%s %s", now.day, day)
    flash(day)
    complete_action()


def main():
    model_dir = "./"
    config = Decoder.default_config()
    config.set_string('-hmm', os.path.join(model_dir, 'en-us/en-us'))
    config.set_string('-dict', os.path.join(model_dir, '0912.dic'))
    config.set_string('-kws', os.path.join(model_dir, 'keyphrase.list'))
    config.set_float('-kws_threshold', 1e-40)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024, output=False)
    stream.start_stream()

    decoder = Decoder(config)
    decoder.start_utt()

    light_up()

    try:
        while True:
            buf = stream.read(1024, exception_on_overflow=False)
            decoder.process_raw(buf, False, False)

            if decoder.hyp() is not None:
                phrase = decoder.hyp().hypstr.strip()
                if waiting is False:
                    if phrase == 'OH CHRISTMAS TREE':
                        decoder.end_utt()
                        wake_up()
                        decoder.start_utt()
                    else:
                        decoder.end_utt()
                        light_up()
                        decoder.start_utt()
                elif waiting is True:
                    if phrase == 'LIGHT UP':
                        decoder.end_utt()
                        light_up()
                        decoder.start_utt()
                    elif phrase == 'ROCK AROUND':
                        decoder.end_utt()
                        rock_around()
                        decoder.start_utt()
                    elif phrase == 'BAD OR GOOD' or phrase == 'GOOD OR BAD'\
                            or phrase == 'NAUGHTY OR NICE' or phrase == 'NICE OR NAUGHTY':
                        decoder.end_utt()
                        good_bad()
                        decoder.start_utt()
                    elif phrase == 'HOW MANY PRESENTS':
                        decoder.end_utt()
                        how_many_presents()
                        decoder.start_utt()
                    elif phrase == 'HOW MANY DAYS UNTIL':
                        decoder.end_utt()
                        how_many_days()
                        decoder.start_utt()
                    else:
                        decoder.end_utt()
                        light_up()
                        decoder.start_utt()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()


if __name__ == '__main__':
    main()
