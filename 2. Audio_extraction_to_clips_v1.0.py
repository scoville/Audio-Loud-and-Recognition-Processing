###################################################################  AUDIO and VIDEO CLIPs extraction (one by one) based on live analysis (Metadata skipe points) version 1
##### Read Metadata timestamp file for all spike points, and extract AUDIO and VIDEO clips individually based on metadata, concatenate both into multiple clip mp4 file
##### Audio_clip_extraction
##### Author: Raymond Wu
##### Date: 2019.10.15
##### This code extract both Audio and Video against 'spike' points, based on parameters definition
##### Step 1: Read Metadata timestamp txt file  
##### Step 2: Extract Audio clip from Audio wav file based on metadata
##### Step 3: Extract Video clip from Video mp4 file based on metadata
##### Step 4: Integrate both wav and mp4 clip into mp4 video+audio file
##### There are 4 parameters to set and 3 path to define  
##### Date: 2019.10.15
################################################################### Parameters setup
pading=0.3							### If the gap (between current and next) < foreward_gap, both will be merged. 
foreward_gap=0.5						### If the gap (between current and next) < foreward_gap, both will be merged. 
pre_pading=0.5							### Output clips will automatically deduct pre-pading from starting_time (to shift starting point earlier)
post_pading=2							### Output clips will automatically add post-pading to end_time (to shift ending point later)
path='C:/Scoville/Source'					### Root of source input files
output_path='C:/Scoville/Output'				### Root of output files
video_path='C:/Scoville/Video'					Root of video files
################################################################### Library Import
import os.path
import os
import glob
import datetime
import shutil
from scipy import signal
from scipy.io import wavfile
import numpy as np   
import argparse
import math
import time
from datetime import datetime
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
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)v 
from keyboard import press
from statistics import mean 
from pynput.keyboard import Key, Controller
################################################################### Declaration
str_EOF='EOF'
timestamp_file = max(glob.iglob(path+'/*timestamp.txt'), key=os.path.getctime)	### Get the most recent audio file
timestamp_file = timestamp_file.replace(path+'\\', '')
output_file=output_path+'/'+timestamp_file.replace(path+'/'+timestamp_file.replace(path+'\\', ''), "_Output.mp4")
output_file=output_file.replace("timestamp.txt","Output.mp4")
audio_output_file=output_path+'/'+timestamp_file.replace(path+'/'+timestamp_file.replace(path+'\\', ''), ".wav")
audio_output_file_0=audio_output_file.replace("_timestamp.txt",".wav")
video_output_file=output_path+'/'+timestamp_file.replace(path+'/'+timestamp_file.replace(path+'\\', ''), ".mp4")
video_output_file_0=video_output_file.replace("_timestamp.txt",".mp4")
timestamp_file = path+'/'+timestamp_file.replace(path+'\\', '')
print ('timestamp_file=',timestamp_file)
audio_file= timestamp_file.replace("_timestamp.txt", ".wav")
audio_current_file=path+'/current.wav'
audio_temp_file=path+'/temp.wav'
video_file=timestamp_file.replace("_timestamp.txt", ".mp4")
video_current_file=path+'/current.mp4'
video_temp_file=path+'/temp.mp4'
################################################################### Extract clips from Audio raw data based on Metadata timestamp (spike points)
with open(timestamp_file) as file: 
    line = file.readlines()
    line = [x.strip() for x in line] 
    print(line)
    line[0]=line[0].replace("@", "")							### Make sure "@" is read as header, to start a new clip (to reselt starting time to 0)
    file_time = line[0]									### Followed by "@", starting time is read
    file_time = time.strftime('%Y-%m-%d_%H.%M.%S', time.gmtime(float(file_time)))	### Then transform timestamp into '2019-10-15_07.11.55' file_title format

ts=line[1:len(line)-1]
start=[round(float(x),3)   for x in ts]	
end=[round(float(x),3) + pading for x in ts]	

################################################################### Merge all neighbor Audio clips that gap < foreward_gap, extend end point make sure duration >= foreward_gap
# end[0]=start[0]									### Make sure the 1st ending time = starting time initially
k=0											### 'k' is final count (after merge), and 'i' is the initial total clip count 
j=len(ts)

for i in range(0, len(ts)):								### Now work on merge case. If the gap (between current and next) < foreward_gap, both will be merged. 
    if end[i] - end[k] < foreward_gap:							### check ending time gap (between next clip and current merged clip) 					
        end[k]=end[i]									###     If gap < foreward_gap, then shift ending time of current (new clip) to a new pointer
    else:										### If this is not merge case
        if end[k]-start[k] < foreward_gap:						###     and If gap < foreward_gap
            end[k]=round(start[k]+foreward_gap,3)					###         then set ending time = starting time + foreward_gap 
        k=k+1										###     then increase final clip count (k) by 1
        j=i-1										###     then set pointer to previous one
        start[k]=round(start[i],3)  # round(end[i],3)					###     then set new starting time (start[k]) to where the current clip ended
        end[k]=round(end[i],3)								###     then set initial ending time to where the current clip ended

if end[k]-start[k] < foreward_gap:							### Make sure the last clip elapsed for a minimum of foreward_gap
    end[k]=round(start[k]+foreward_gap,3)

################################################################### Extract clips from Audio and Video raw data based on Metadata timestamp (spike points)
start = start[0:k+1]									### Setup spike_rec_start array by assigning k records starting values (k is the count of merged clip)
end = end[0:k+1] 									### Setup spike_rec_end array by assigning k records ending values (k is the count of merged clip)

for i in range(0, len(ts)):
    if line[i].find(str_EOF) == -1:
        start[i] = start[i] - pre_pading						### Do pre_pading 
        end[i] = end[i] + post_pading							### Do post_pading 
        duration = end[i] - start[i]
        print(i,start,duration,end)
        if start[i] < 0:								### Make sure 1st clip start from "0"
            start[i]=0
        if duration <= 0:								### Make sure each clip comes with a positive duration
            duration=0.1
        audio_output_file=audio_output_file_0.replace(".wav" ,"-"+str(i)+".wav")
        video_output_file=video_output_file_0.replace(".mp4" ,"-"+str(i)+".mp4")     	### Below Extract AUDIO
        cmd1="os.system('"+video_path+'/ffmpeg -y -v quiet -ss '+str(start[i]) + ' -t '+str(duration) + ' -i ' + audio_file + '  ' +audio_output_file+"')"  
        print(cmd1)
        exec(cmd1)									### Below Extract VIDEO
        cmd1_B="os.system('cd  "+video_path+ ' & ' +video_path+'/ffmpeg -y -i '+video_file+ ' -ss ' +str(start[i]) + '  -t '+str(duration) + ' -c:v libx264 -c:a copy  ' + video_output_file+"')"
        exec(cmd1_B)						### Execute above
        output_file=output_path+'/'+file_time+'-'+str(i)+'.mp4'				### Below integrate video + audio into new clip
        cmd_final="os.system('"+video_path+'/ffmpeg -y -i '+video_output_file+' -i   '+audio_output_file+'  -vcodec copy  '+output_file+"')"
        exec(cmd_final)	
################################################################### End of script



