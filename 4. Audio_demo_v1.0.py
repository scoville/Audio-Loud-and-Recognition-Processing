###################################################################  AUDIO RECOGNITION version 1
##### Video and Audio Processing to read mp4 file, extract loud sound and output them to mp4 files at each spike
##### Author: Raymond Wu
##### Date: 2019.10.15
##### This code extract both Audio and Video against 'spike' points, based on parameters definition
##### Step 1: Read souurce file - mp4 Video file with sound (or mute mp4 Video + wav Audio) to identify spike points 
##### Step 2: Extract audio + video into clips, then merge audio + video clips to output them into mp4 files 
##### There are 4 parameters to set and 5 path to define (as first step) 
###################################################################  Parameters setup
threshold=11					### Sound is defined as "spike" once exceeding threshold
foreward_gap=0.5				### If the gap (between current and next) < foreward_gap, both will be merged. 
                                                ### If current duration < foreward_gap, current duration = foreward_gap
pre_pading=0.5					### Output clips will automatically deduct pre-pading from starting_time (to shift starting point earlier)
post_pading=2					### Output clips will automatically add post-pading to end_time (to shift ending point later)
audio_path='C:/Scoville/Audio'			### Audio root path
audio_file=audio_path+'/Sample640.wav'		### This is the Audio source file to read
video_path='C:/Scoville/Video'			### Video root path
video_file=video_path+'/Sample640.mp4'		### This is the Video source file to read
output_path='C:/Scoville/Output'		### Output root path. All the output files will be produced under this folder
###################################################################  Library Import
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import numpy as np   
import os.path
import os
import glob
import datetime
import shutil
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
###################################################################  Declaration
wav_file = audio_file
audio_current_file=audio_path+'/current.wav'
audio_temp_file=audio_path+'/temp.wav'
audio_output_file=audio_file.replace(".wav", "_output.wav")
video_output_file=video_file.replace(".mp4", "_output.mp4")
video_current_file=video_path+'/current.mp4'
video_temp_file=video_path+'/temp.mp4'
video_current_file_mpg=video_current_file.replace(".mp4", ".mpg")
video_temp_file_mpg=video_temp_file.replace(".mp4", ".mpg")
video_output_file_mpg=video_output_file.replace(".mp4", ".mpg")
video_current_file_ts=video_current_file.replace(".mp4", ".ts")
video_temp_file_ts=video_temp_file.replace(".mp4", ".ts")
audio_video_file=video_path+'/Audio_Video_Final.mp4'
audio_video_backup=audio_video_file.replace(".mp4", "_backup.mp4")
start_time=int(round(time.time(),0))
timestamp_file=open(output_path+str(start_time)+'_timestamp.mp4',"w+")
###################################################################  Read Audio and get Spike
sample_rate, samples = wavfile.read(wav_file)   				### Read Audio source file and get wave form data and sampling rate
print('sample_rate, samples =', sample_rate, samples)
frequencies, times, spectrogram = signal.spectrogram(samples,sample_rate,nfft=1024)	### Use signal.spectrogram to transform spectrum into Frequency dimension
plt.pcolormesh(times, frequencies, 10*np.log10(spectrogram))			### Plot spectrum in different color
plt.ylabel('Frequency [Hz]')							### Set Frequency as 'y'
plt.xlabel('Time [sec]')							### Set Time as 'x'
plt.show()									### Show spectrum plot. Close plot to continue
rec_size=len(times)								### Get records size				
rec_len=len(spectrogram[:])							### Get records length
temp_rec= [ [ 0,0,0 ] for i in range(rec_size) ]
j=0
for i in range(0,rec_size):							### Calculate averaged spectrum at each time slote
    s=round(sum(10*np.log10(spectrogram[0:rec_len,i]))/rec_len,3) + threshold   ### Adjust the calculation by a configurable threshold
    t=round(times[i],3)								### Get timestamp at that time slot
    # print(s)
    if s> 0:									### 'j' will be the count of clips whose loudness > threshold
        print('time, spectrum=', t,s)						### 
        temp_rec[j] = [t,0,s]							### Record timestamp and spectrum at each slot whose spectrum exceed threshold
        j=j+1									### Add 1 to time-spectrum array counter (total record size = j, before merge)

spike_rec = temp_rec[0:j] 							### Extract 0:j (j records) from temp_rec and assign to spike_rec to limit range of array
temp_rec = spike_rec								### Copy spike_rec back to temp_rec, so array size will be limited to 'j' (last record)
rec_size = len(temp_rec )							### Get record size
start=[round(x[0],3) for x in temp_rec]						### Setup array of starting time of each clip by assigning starting values of temp_rec
end=[round(x[0],3) for x in temp_rec]						### Initially set array of ending time to the same (of starting time)
mag=[round(x[2],3) for x in temp_rec] 						### Set up array of magnitude by assigning magnitude values of temp_rec
end[0]=start[0]									### Make sure the 1st ending time = starting time initially
k=0										### 'k' is final count (after merge), and 'i' is the initial total clip count 
for i in range(0, rec_size):							### Now work on merge case. If the gap (between current and next) < foreward_gap, both will be merged. 
    if end[i] - end[k] < foreward_gap:						### check ending time gap (between next clip and current merged clip) 					
        end[k]=end[i]								###     If gap < foreward_gap, then shift ending time of current (new clip) to a new pointer
        if i==k:								###     This should happens to 1st clip. In case this is not shift case, let magnitude stays as it was  
            mag[k]=round(mag[k],3)						### 
        if i>j:									###     If this is merge of few clips
            mag[k]=round(max(mag[j:i+1]),3)					###     then find max.magnitude to represent this (merged) clip
    else:									### If this is not merge case
        if end[k]-start[k] < foreward_gap:					###     and If gap < foreward_gap
            end[k]=round(start[k]+foreward_gap,3)				###         then set ending time = starting time + foreward_gap 
        k=k+1									###     then increase final clip count (k) by 1
        j=i-1									###     then set pointer to previous one
        start[k]=round(end[i],3)						###     then set new starting time (start[k]) to where the current clip ended
        end[k]=round(end[i],3)							###     then set initial ending time to where the current clip ended

if end[k]-start[k] < foreward_gap:						### Make sure the last clip elapsed for a minimum of foreward_gap
    end[k]=round(start[k]+foreward_gap,3)

spike_rec_start = start[0:k+1]							### Setup spike_rec_start array by assigning k records starting values (k is the count of merged clip)
spike_rec_end = end[0:k+1] 							### Setup spike_rec_end array by assigning k records ending values (k is the count of merged clip)
spike_rec_mag = mag[0:k+1]							### Setup spike_rec_mag array by assigning k records nagbitude values (k is the count of merged clip)
############################################################ Define Input, Processing and Output files
audio_output= open(audio_output_file,"wb")
audio_current= open(audio_current_file,"wb")
audio_temp= open(audio_temp_file,"wb")
video_current= open(video_current_file,"wb")
video_output= open(video_output_file,"wb")
video_temp= open(video_temp_file,"wb")
video_current_mpg= open(video_current_file_mpg,"wb")
video_output_mpg= open(video_output_file_mpg,"wb")
video_temp_mpg= open(video_temp_file_mpg,"wb")
video_current_ts= open(video_current_file_ts,"wb")
video_temp_ts= open(video_temp_file_ts,"wb")
audio_video= open(audio_video_file,"wb")
############################################################# Do pading to all clips' timeframe. Extract clips from Audio and Video source, and Integrate them for each clip
for i in range(0, len(spike_rec_start)):
    spike_rec_start[i] = spike_rec_start[i] - pre_pading			### Do pre_pading 
    spike_rec_end[i] = spike_rec_end[i] + post_pading				### Do post_pading 
    if spike_rec_start[i] < 0:							### Make sure 1st starting_time >= 0		
        spike_rec_start[i] = 0
    duration = str(round(spike_rec_end[i] - spike_rec_start[i],3)) 		### Calculate duration (end - start) for ffmpeg
    print('start=',spike_rec_start[i], 'end=',spike_rec_end[i])			### Following line extract AUDIO clip (based on starting_time and duration) from source, and write to Current_file								
    cmd1_A="os.system('cd  "+audio_path+ ' & ' +video_path+'/ffmpeg -y -v quiet -ss '+str(spike_rec_start[i]) + ' -t '+ duration + ' -i '+ audio_file+'   '+audio_current_file+"')"
    exec(cmd1_A)								### Execute above. Following line extract VIDEO clip (based on starting_time and duration) from source, and write to Current_file								
    cmd1_B="os.system('cd  "+video_path+ ' & ' +video_path+'/ffmpeg -y -i '+video_file+ ' -ss ' +str(spike_rec_start[i]) + '  -t '+str(duration) + ' -c:v libx264 -c:a copy  ' + video_current_file+"')"
    exec(cmd1_B)								### Execute above
    ### date_time = str(datetime.now()).replace(" ","_").replace(":","-") 	### Temporarily de-activate it (Transform date_time format to: '2019-10-20_14-30-52.637013')
    if i==0:
        file_time_I = str(round(os.path.getctime(audio_file),2))		### The 1st clip get timestamp from audio source file
    else:
        file_time_I = str(round(float(file_time_I) + float(duration),2))	### The succeeding clip get timestamp from previous timestamp + duration
    file_time_S = time.strftime('%Y-%m-%d_%H.%M.%S', time.gmtime(float(file_time_I)))	### Then transform timestamp into '2019-10-15_07.11.55' file_title format
    Int_part,Dot_part,Float_part= str(file_time_I).partition('.')		### Get floating part (2 digits after '.') of timestamp
    file_time_S = file_time_S + '.'+ str(round(int(Float_part),2))+'.mp4' 	### Add floating part to file_title format to be unique. New format: '2019-10-15_07.11.55.87.mp4'
    audio_video_file=output_path+'/'+file_time_S				### Define file_name of output. Folloing line integrate Audio + Video clip into Output file
    cmd_final="os.system('"+video_path+'/ffmpeg -y -i '+video_current_file+' -i   '+audio_current_file+'  -vcodec copy  '+audio_video_file+"')"
    exec(cmd_final)								### Execute it
############################################################# END OF SCRIPT
############################################################# Neglect following part (temporarily retain for future development)
    # if i==0:
    #    shutil.copy(audio_current_file, audio_output_file)
    #    shutil.copy(video_current_file, video_output_file)
    # else:
    #     shutil.copy(audio_output_file, audio_temp_file)
    #     cmd2_A="os.system('"+video_path+'/sox-14-4-2\sox ' +audio_current_file+'  '+audio_temp_file +'  '+audio_output_file+"')"  
    #     exec(cmd2_A)
    #     shutil.copy(video_output_file, video_temp_file)
    #     cmd3_B="os.system('"+video_path+'/ffmpeg -y -i ' +video_current_file+' -c copy -bsf:v h264_mp4toannexb -f mpegts   '+video_current_file_ts+"')"
    #     cmd4_B="os.system('"+video_path+'/ffmpeg -y -i ' +video_temp_file+' -c copy -bsf:v h264_mp4toannexb -f mpegts   '+video_temp_file_ts+"')"
    #     cmd5_B="os.system('"+video_path+'/ffmpeg -y -i "concat:' +video_temp_file_ts+'|'+video_current_file_ts+'"  -c copy -bsf:a aac_adtstoasc  '+video_output_file+"')"
    #     exec(cmd3_B)
    #     exec(cmd4_B)
    #     exec(cmd5_B)
    #     cmd_final="os.system('"+video_path+'/ffmpeg -y -i '+video_output_file+' -i   '+audio_output_file+'  -vcodec copy  '+audio_video_file+"')"
    #     exec(cmd_final)
 



