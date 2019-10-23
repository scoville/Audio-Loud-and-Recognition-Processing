###################################################################  AUDIO LIVE (LOUD) SOUND identification version 1
##### Audio_processing
##### Spike points identification, Record Audio Raw Data, and producing Spike metadata file outputs
##### Author: Raymond Wu
##### Date: 2019.10.17
##### This code takes live audio data into analisys, all the sound will be recorded and there are 2 output files will be generated, and stored in 'path' Directory being set
##### File 1: The first file holds raw audio data - the timestamp of starting point will be used for file name (i.e.; 1570066386.wav)
##### File 2: The second file holds the spike records, the duration from starting point to spike (i.e.; 1570066386_timestamp.txt)
##### The output files (File 1 and File 2) are pair which come with identical timestamp, File 2 provides all spikes in File 1, which exceed threshold (max_magnitude)  
##### There are 3 parameters need to set - max_magnitude and max_duration
##### Para 1: (Max_magnitude) Currently it is set to 0.01, tunning may be required based on situation
##### Para 2: (Max_single_duration) Period to output files (file 1 & 2). In testing period, it was set to 5 (seconds). In future, this is possible need be reset to 1200 (20 minutes)
##### Para 3: (Max_multiple_duration) Period to complete the whole process. In testing period, it was set to 20 (seconds). In future, this is possible need be reset to 86400 (24 hours)
##### Para 4: (path) This is the directory the output files are stored.  
#####
###################################################################  Parameters setup
max_magnitude = 0.005						### Sound is defined as "spike" once the sound exceed this threshold
max_single_duration = 5 					### Set the max. duration that system will produce output file (timestamp metadata + audio raw data)  20 minutes is the default 
max_multiple_duration = 20   					### Set the max. duration of the process. Better to be multiples of max_single_duration (24 hours as default)
path='C:/Scoville/Output/'					### This is the root of Audio output (timestamp metadata + audio raw data)
###################################################################  Library Import
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
import sounddevice as sd
import soundfile as sf
from ctypes import *
import numpy  
from keyboard import press
from statistics import mean 
from pynput.keyboard import Key, Controller
usage_line = ' press <enter> to quit, +<enter>'			### Helper function if user want to press <enter> to exit 
###################################################################  Program start
try:								### Try and raise exception if fail						
    columns, _ = shutil.get_terminal_size()			### Get terminal screen size
except AttributeError:						### If error, assign a value
    columns = 80

def int_or_str(text):						### Helper function for argument parsing text value
    try:							### Test text's integer value, if fail show text
        return int(text)
    except ValueError:
        return text

res = max_multiple_duration % max_single_duration		### Calculate for how many run of the loop 'max_single_duration' in the process 'max_muptiple_duration'
loop = int((max_multiple_duration - res)/max_single_duration)  
if res > 0:							### If max_multiple_duration is not exact multiples of max_single_duration 
    loop = loop+1						### then add 1 to loop count
    max_single_duration_last=res				### and use residue as max_single_duration for the last loop
else:
    max_single_duration_last=max_single_duration

###################################################################  POINT A. For_loop start => (call POINT B.)
###################################################################  any incomming audio stream will be processed by callback procedure until time due, or user <exit> 
break_code=0
import sys
for cycle in range(1,loop+1):
    if break_code == 1:						### If user press <enter> or <quit>, then exit	
	# timestamp_file.close()
	# file.close()	
        break
    if cycle==loop:
        max_single_duration=max_single_duration_last		### Assign exact value to max_single_duration of last loop
    # print('flag1')
    
    class NullWriter(object):
        def write(self, arg):
            pass
    nullwrite = NullWriter()
    oldstdout = sys.stdout
    sys.stdout = nullwrite 					### disable output => supress screen output for add_argument message
    parser = argparse.ArgumentParser(description=__doc__)	### Add argements to argparse, to quickly develop simple function (particularly - d and -filename)
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
    sys.stdout = oldstdout 					### enable screen output => back to normal
    if high <= low:
        parser.error("HIGH must be greater than LOW")
    # print('flag2')
    colors = 30, 34, 35, 91, 93, 97
    chars = ' :%#\t#%:'
    gradient = []
    for bg, fg in zip(colors, colors[1:]):
        for char in chars:
            if char == '\t':
                bg, fg = fg, bg
            else:
                gradient.append('\x1b[{};{}m{}'.format(fg, bg + 10, char))
    try:
        start_time=int(round(time.time(),0))
        timestamp_file=open(path+str(start_time)+'_timestamp.txt',"w+")
        timestamp_string = '@'+str(round(start_time,1))
        print(timestamp_string, file=timestamp_file)
        print('Start Recording ... press <enter> to quit')
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
        # C struct redefinitions				### Following ctype classese are temporarily not used, just leave them for future development
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
        def PressKey(hexKeyCode):				### Temporary this is not used
            print('a')
            extra = ctypes.c_ulong(0)
            ii_ = Input_I()
            ii_.ki = KeyBdInput( hexKeyCode, 0x48, 0, 0, ctypes.pointer(extra) )
            x = Input( ctypes.c_ulong(1), ii_ )
            SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        def ReleaseKey(hexKeyCode):				### Temporary this is not used
            print('b')
            extra = ctypes.c_ulong(0)
            ii_ = Input_I()
            ii_.ki = KeyBdInput( hexKeyCode, 0x48, 0x0002, 0, ctypes.pointer(extra) )
            x = Input( ctypes.c_ulong(1), ii_ )
            SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        def PressEnter():					### Generate special code once <enter> is pressed
            print('Running: Press Enter')
            PressKey(0x0D)      # 0x0D = Enter
            ReleaseKey(0x0D)
        def mean_of_array(index):				### This cmpute magnitude, take the sum of an array and devide it by array length
            return sum(index[0:len(index)])/len(index)
        # test_mean=[1,2,3,4,5]
        # print('test_mean=', mean_of_array(test_mean))
        count_high_magnitute = 0
        sequence_count = 0
        def duration_cal():					### Temporary this is not used
            time_now = time.time()
            return time_now
        def file_write(time_now, duration):			### Compute the duration of current point-in-time (by comparing to starting time)
            file.write(str(duration)) 
        def high_magnitute_handling():				### This calculate for count of loud sound being detected
            global count_high_magnitute
            count_high_magnitute += 1
            return count_high_magnitute
        def sequence_stamp():					### Temporary this is not used
            global sequence_count
            sequence_count += 1
            return sequence_count
        def time_stamp(timestamp_string):			### This calculate the timestamp of current point-in-time
            # global timestamp_string
            timestamp_string=timestamp_string+':'+str(round(duration,3))
            return timestamp_string
 	###########################################################  POINT C. callback loop start
        def callback(indata, frames, time, status):		### This is a recursive loop to handle Audio stream
            # print('flag4')
            if status:
                print(status, file=sys.stderr)
                text = ' ' + str(status) + ' '
                # print('\x1b[34;40m', text.center(args.columns, '#'),'\x1b[0m', sep='')
            # duration_cal()
            global statuses
            statuses |= status
            if any(indata):					### If Audio stream is detected 
                sequence_stamp
                # print('flag5')
                keyboard = Controller()
                # keyboard.press('0x0D')			### Keyboard method was not working properly, so break_code method was applied for manual exit. (temporarily keep)
                # keyboard.release('0x0D')
                # print('keyboard=',keyboard)
                magnitude = np.abs(np.fft.rfft(indata[:, 0], n=fftsize))   ### Apply numpy 'np.fft.rfft' to compute DFT in frequency dimension
                # print('magnitude =',magnitude, fftsize)
                magnitude *= args.gain / fftsize		### Get avarged magnitude (array) size by dividing it by fftsize (4086)
                # print('magnitude * =',magnitude)
                in_data = indata.copy()
                mean_of_magnitude = mean_of_array(magnitude)	### Get averated magnitude (value) by dividing it by array length (2044)
                # print('length of magnitude * =',len(magnitude))
                # print('mean_of_array=',mean_of_array,' magnitude=',magnitude,' fftsize=',fftsize)
                time_now = duration_cal()
                duration = time_now - start_time		### Each incoming audio signal is calculated for duration, to check whether max_single_duration is reached
                sequence_count = sequence_stamp()
                time_now = round(duration_cal(),4)
                # print('time_now=', time_now)
                q.put(in_data)					### Keep on writing audio to File 1 (raw audio data)
                file.write(q.get())
                if sequence_count == 1:				### Add the initial line (of timestamp metadata file) by '@' as header + timestamp
                    timestamp_string = '@'+str(round(start_time,1))
                # print('time_now, duration=', time_now, duration)
                if duration > max_single_duration:  		### Check whether max_single_duration is reached, output 2 files once reached
                    print('EOF' + str(round(time_now,1)), file=timestamp_file)   ### Finally write 'EOF' trailer to File 2
                    timestamp_file.close()
                    # print('count_high_magnitute=',count_high_magnitute)
                    q.put(in_data)				### Write last data to File 1
                    file.write(q.get())
                    # print('time_now, duration=', time_now, duration)
                    print('{:9s} {:11.3f} {:12s} {:6.5f} {:11s} {:0d} {:12s} {:0d} {:8s}'.format('=>  Time=', round(time_now,3), '   Duration=', round(duration,5), '    (End of ', cycle,"'th round of ", loop, ' rounds)'))
                    # print('=>  Time=', round(time_now,1), '   Duration=', round(duration,5), ' (End of ', cycle,"'th round of ", loop, ' rounds)')
                    file.close()
                    press('return')
                if mean_of_magnitude > max_magnitude:		### Check whether a loud sound is detected. If yes, then the duration (since process started) will be computed and stored
                    if duration > 0:
                        # timestamp_string=timestamp_string+':'+str(round(duration,3))
                        # time_stamp(timestamp_string)
                        print(duration, file=timestamp_file)	### Write to File 2, put timestamp
                        time_now = round(duration_cal(),4)
                        print('{:9s} {:11.3f} {:10s} {:6.5f}  {:10s} {:6.5f}'.format('=>  Time=', round(time_now,3), '   Duration=', round(duration,5), '   Magnitude=', round(mean_of_magnitude,5)))
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
 	###########################################################  callback loop end
	###########################################################  POINT B. MAIN Sub_loop started (incurred by for_loop)
								### Audio file setup by using sampling rate of 44100
        with sf.SoundFile(args.filename, mode='x', samplerate=44100, channels=1, subtype=args.subtype) as file:
            # print('flag6')
 								####  Incurring point of recursive 'callback' by using args.device => call POINT C.
            with sd.InputStream(device=args.device, channels=1, callback=callback, blocksize=int(samplerate * args.block_duration / 1000), samplerate=samplerate):
                # print('flag7')
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
                        cycle=loop+1
                        break_code=1
                        break
                    for ch in response:
                        # print('flag10')
                        if ch == '+':
                            args.gain *= 2
                        elif ch == '-':
                            args.gain /= 2
                        else:
                            # print('\x1b[31;40m', usage_line.center(args.columns, '#'), '\x1b[0m', sep='')
                            break
	##########################################################  Sub_loop ended. Followings are exception handlings
    except KeyboardInterrupt:					### keyboard interrupt
        # print('flag11')
        parser.exit('Interrupted by user')
    except Exception:
        # print('flag12')					### smooth exit
        pass
    except Exception as e:
        # print('flag13')
        parser.exit(str(e))
    except:
        # print('flag15')
        print(sys.exc_info()[0])