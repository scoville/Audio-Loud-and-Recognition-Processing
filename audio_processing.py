##### Audio Raw Data Recording and Spike points identification
##### Author: Raymond Wu
##### Date: 2019.10.02
##### This code takes live audio data into analisys, all the sound will be recorded and there are 2 output files will be generated, and stored in 'path' Directory being set
##### File 1: The first file holds raw audio data - the timestamp of starting point will be used for file name (i.e.; 1570066386.wav)
##### File 2: The second file holds the spike records, the duration from starting point to spike (i.e.; 1570066386_timestamp.txt)
##### File 1 and File 2 are pair which come with identical timestamp, File 2 provides all spikes in File 1, which exceed threshold (max_magnitude)  
##### There are 3 parameters need to set - max_magnitude and max_duration
##### Para 1: (Max_duration) In testing period, it was set to 20 (seconds). In future, this is possible need be reset to 1200 (20 minutes)
##### Para 2: (Max_magnitude) Currently it is set to 0.01, tunning may be required based on situation
##### Para 3: (path) This is the directory the files are stored. By default, this is set to "C:/Scoville/Audio"
#####
##### Parameter Area Start ##### =>
max_magnitude = 0.02
max_duration = 1200
path='C:/Scoville/Audio/'
##### Parameter Area End <= #####
#####
import argparse
import math
import time
import numpy as np
import shutil
import tempfile
import queue
import sys
import numpy as np
import csv
import logging
import ctypes
from keyboard import press
from statistics import mean 
from pynput.keyboard import Key, Controller
usage_line = ' press <enter> to quit, +<enter> or -<enter> to change scaling '
start_time=int(round(time.time(),0))
timestamp_file=open(path+str(start_time)+'_timestamp.txt',"w+")
# timestamp_file = open("audio_timestamp.txt","w+")
usage_line = ' press <enter> to quit, +<enter> or -<enter> to change scaling '
try:
    columns, _ = shutil.get_terminal_size()
except AttributeError:
    columns = 80

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

# print('flag1')
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('-l', '--list-devices', action='store_true',help='list audio devices and exit')
parser.add_argument('-b', '--block-duration', type=float,metavar='DURATION', default=50, help='block size (default %(default)s milliseconds)')
parser.add_argument('-c', '--columns', type=int, default=columns, help='width of spectrogram')
parser.add_argument('-d', '--device', type=int_or_str,help='input device (numeric ID or substring)')
parser.add_argument('-g', '--gain', type=float, default=10,help='initial gain factor (default %(default)s)')
parser.add_argument('-r', '--range', type=float, nargs=2,metavar=('LOW', 'HIGH'), default=[100, 2000],help='frequency range (default %(default)s Hz)')
parser.add_argument('-s', '--samplerate', type=int, help='sampling rate')
parser.add_argument('-t', '--subtype', type=str, help='sound file subtype (e.g. "PCM_24")')
parser.add_argument('filename', nargs='?', metavar='FILENAME', help='audio file to store recording to')
args = parser.parse_args()
low, high = args.range
if high <= low:
    parser.error("HIGH must be greater than LOW")

# print('flag2')
# Create a nice output gradient using ANSI escape sequences.
# Stolen from https://gist.github.com/maurisvh/df919538bcef391bc89f
colors = 30, 34, 35, 91, 93, 97
chars = ' :%#\t#%:'
gradient = []
for bg, fg in zip(colors, colors[1:]):
    for char in chars:
        if char == '\t':
            bg, fg = fg, bg
        else:
            gradient.append('\x1b[{};{}m{}'.format(fg, bg + 10, char))
timestamp_string = '@'+str(round(start_time,1))
print(timestamp_string, file=timestamp_file)

try:
    import sounddevice as sd
    import soundfile as sf
    from ctypes import *
    import numpy  # Make sure NumPy is loaded before it is used in the callback
    assert numpy  # avoid "imported but unused" message (W0611)
    print('Start Recording')
    if args.list_devices:
        sd.print_devices()
        parser.exit()
    if args.device is None:
        args.device = sd.default.device['input']
    samplerate = sd.query_devices(args.device)['default_samplerate']
    if args.filename is None:
        # args.filename = tempfile.mktemp(prefix='audio_', suffix='.wav', dir='')
        args.filename =path+'/'+str(start_time)+'.wav'
    q = queue.Queue()
    m = queue.Queue()
    delta_f = (high - low) / (args.columns - 1)
    fftsize = np.ceil(samplerate / delta_f).astype(int)
    low_bin = np.floor(low / delta_f)
    statuses = sd.CallbackFlags()
    # print('flag3')

    SendInput = ctypes.windll.user32.SendInput
    # C struct redefinitions
    PUL = ctypes.POINTER(ctypes.c_ulong)
    class KeyBdInput(ctypes.Structure):
        _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong),  ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]

    class HardwareInput(ctypes.Structure):
        _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]

    class MouseInput(ctypes.Structure):
        _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time",ctypes.c_ulong),("dwExtraInfo", PUL)]

    class Input_I(ctypes.Union):
        _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]

    class Input(ctypes.Structure):
        _fields_ = [("type", ctypes.c_ulong),   ("ii", Input_I)]

    def PressKey(hexKeyCode):
        print('a')
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( hexKeyCode, 0x48, 0, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def ReleaseKey(hexKeyCode):
        print('b')
        extra = ctypes.c_ulong(0)
        ii_ = Input_I()
        ii_.ki = KeyBdInput( hexKeyCode, 0x48, 0x0002, 0, ctypes.pointer(extra) )
        x = Input( ctypes.c_ulong(1), ii_ )
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

    def PressEnter():
        print('Running: Press Enter')
        PressKey(0x0D)      # 0x0D = Enter
        ReleaseKey(0x0D)

    def mean_of_array(index):
        return sum(index[0:len(index)])/len(index)

    # test_mean=[1,2,3,4,5]
    # print('test_mean=', mean_of_array(test_mean))
    count_high_magnitute = 0
    sequence_count = 0

    def duration_cal():
        time_now = time.time()
        return time_now

    def file_write(time_now, duration):
        file.write(str(duration)) 

    def high_magnitute_handling():
        global count_high_magnitute
        count_high_magnitute += 1
        return count_high_magnitute

    def sequence_stamp():
        global sequence_count
        sequence_count += 1
        return sequence_count

    def time_stamp(timestamp_string):
        # global timestamp_string
        timestamp_string=timestamp_string+':'+str(round(duration,3))
        return timestamp_string

    def callback(indata, frames, time, status):
        # print('flag4')
        if status:
            print(status, file=sys.stderr)
            text = ' ' + str(status) + ' '
            # print('\x1b[34;40m', text.center(args.columns, '#'),'\x1b[0m', sep='')
        # duration_cal()
        global statuses
        statuses |= status
        if any(indata):
            sequence_stamp
            # print('flag5')
            keyboard = Controller()
            # keyboard.press('0x0D')
            # keyboard.release('0x0D')
            # print('keyboard=',keyboard)
            magnitude = np.abs(np.fft.rfft(indata[:, 0], n=fftsize))
            magnitude *= args.gain / fftsize
            in_data = indata.copy()
            mean_of_magnitude = mean_of_array(magnitude)
            time_now = duration_cal()
            duration = time_now - start_time
            sequence_count = sequence_stamp()
            time_now = round(duration_cal(),4)
            # print('time_now=', time_now)
            q.put(in_data)
            file.write(q.get())
            if sequence_count == 1:
                timestamp_string = '@'+str(round(start_time,1))
            # print('time_now, duration=', time_now, duration)
            if duration > max_duration:  ### Check whether max_duration is reached, break once reached
                # timestamp_string=timestamp_string+'$'+str(round(time_now,1))
                # print(duration, file=timestamp_file)
                print('EOF' + str(round(time_now,0)), file=timestamp_file)
                # print('count_high_magnitute=',count_high_magnitute)
                q.put(in_data)
                file.write(q.get())
                # print('time_now, duration=', time_now, duration)
                print('=>  Time=', round(time_now,1), '   Duration=', round(duration,5), '   (This is the end of Audio processing)')
                file.close()
                press('return')
                # press('enter')
                # duration_cal()
                # exit()
                # raise ValueError("Time Due")
            if mean_of_magnitude > max_magnitude:  ### Check whether a loud sound is detected. If yes, then the duration (since process started) will be computed and stored
                if duration > 0:
                    # timestamp_string=timestamp_string+':'+str(round(duration,3))
                    # time_stamp(timestamp_string)
                    print(duration, file=timestamp_file)
                    time_now = round(duration_cal(),4)
                    print('{:10s} {:11.3f} {:10s} {:6.5f}  {:10s} {:6.5f}'.format('=>  Time=', round(time_now,3), '   Duration=', round(duration,5), '   Magnitude=', round(mean_of_magnitude,5)))
                    # print('{:10s} {:10.3f} {:10.3f}'.format('=>  Time=', round(time_now,3), '   Duration=', round(duration,5), '   Magnitude=', round(mean_of_magnitude,5), '   Count_high_magnitute=',high_magnitute_handling()))
                    # file.write(str(duration)) 
                    # print('MAGNNITUDE_mean=', mean_of_magnitude)
                    # print('count_high_magnitute=',high_magnitute_handling())
                    q.put(in_data)
                    file.write(q.get())
                    # raise ValueError("Time Due")
                # line = (gradient[int(np.clip(x, 0, 1) * (len(gradient) - 1))] for x in magnitude[low_bin:low_bin + args.columns])
                # print(*line, sep='', end='\x1b[0m\n', flush=True)
                return duration
        else:
            print('no input', flush=True)

    with sf.SoundFile(args.filename, mode='x', samplerate=44100, channels=1, subtype=args.subtype) as file:
        # print('flag6')
        with sd.InputStream(device=args.device, channels=1, callback=callback, blocksize=int(samplerate * args.block_duration / 1000), samplerate=samplerate):
            # print('flag7')
    # with sd.InputStream(device=args.device, channels=1, callback=callback, blocksize=int(samplerate * args.block_duration / 1000), samplerate=samplerate):
            while True:
                # print('flag8')
                # duration=callback(indata, frames, time, status)
                # print('duration=',duration)
                response = input()
                response = ''
                if response in ('', 'q', 'Q'):
                    time_now = duration_cal()
                    print('EOF' + str(round(time_now,0)), file=timestamp_file)
                    # print('flag9')
                    break
                for ch in response:
                    # print('flag10')
                    if ch == '+':
                        args.gain *= 2
                    elif ch == '-':
                        args.gain /= 2
                    else:
                        print('\x1b[31;40m', usage_line.center(args.columns, '#'),
                              '\x1b[0m', sep='')
                        break
    # if statuses:
        # logging.warning(str(statuses))

except KeyboardInterrupt:
    # print('flag11')
    parser.exit('Interrupted by user')
except Exception:
    pass
except Exception as e:
    # print('flag12')
    parser.exit(str(e))
except ValueError as ve:
    parser.exit('Time Due')
except:
    print(sys.exc_info()[0])
