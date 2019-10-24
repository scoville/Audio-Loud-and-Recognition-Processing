################################################################### AUDIO and VIDEO CLIPs extraction based on live analysis (Metadata skipe points) 
################################################################### all the extracted video and ausio will be integrated into one file  
##### Read Metadata timestamp file for all spike points, and extract AUDIO and VIDEO clips individually based on metadata, concatenate both into one clip mp4 file
##### Author: Raymond Wu
##### Date: 2019.10.02
##### This code extract both Audio and Video against 'spike' points, based on timestamp file produced in audio processing.
##### Step 1: Read timestamp file from audio, to identify spike points, Extract all spike points and integrate
##### Step 2: Extract video into clips, based on the timestamp of spike from Audio metadata. It then merge all clips, and consoidate with Audio
##### File: There are a few temporary files during the processing. The processing results will be written to output file which include both Audio and Video at spike 
##### There are 4 parameters need to set - backward_delta, forward_delta, audio_path, and video_path
##### Para 1: (backward_delta) During audio and video final at spike points, the extracted data of each spike may started from (timestamp - backward_delta) 
##### Para 2: (forward_delta) During audio and video final at spike points, the extracted data of each spike may ended with (timestamp + forward_delta) 
##### Para 3: (audio_path) This is the directory the audio files are stored. By default, this is set to "C:/Scoville/Audio"
##### Para 4: (video_path) This is the directory the video files are stored. By default, this is set to "C:/Scoville/Video"
###################################################################  Parameters setup
delta=15
backward_gap=0
foreward_gap=0.3
###################################################################  Declaration
audio_path='C:/Scoville/Audio'
audio_file=audio_path+'/Sample640.wav'
video_path='C:/Scoville/Video'
video_file=video_path+'/Sample640.mg4'
wav_file = "C:/Scoville/Audio/Sample640.wav"
video_path='C:/Scoville/Video'
video_file=video_path+'/Sample640_mute.mp4'
audio_path='C:/Scoville/Audio'
audio_file=audio_path+'/Sample640.wav'
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
###################################################################  Library import
import matplotlib.pyplot as plt
from scipy import signal
from scipy.io import wavfile
import numpy as np   
import os.path
import os
import glob
import datetime
import shutil
###################################################################  Read Audio (offline) and get Spike
sample_rate, samples = wavfile.read(wav_file)   
print('sample_rate, samples =', sample_rate, samples)
frequencies, times, spectrogram = signal.spectrogram(samples,sample_rate,nfft=1024)	### Use signal.spectrogram to transform spectrum into Frequency dimension	
plt.pcolormesh(times, frequencies, 10*np.log10(spectrogram))				### Plot spectrum in different color
plt.ylabel('Frequency [Hz]')								### Set Frequency as 'y'
plt.xlabel('Time [sec]')								### Set Time as 'x'
plt.show()										### Show spectrum plot. Close plot to continue
rec_size=len(times)									### Get records size	
rec_len=len(spectrogram[:])								### Get records length
temp_rec= [ [ 0,0,0 ] for i in range(rec_size) ]
j=0
for i in range(0,rec_size):								### Calculate averaged spectrum at each time slote
    s=round(sum(10*np.log10(spectrogram[0:rec_len,i]))/rec_len,3) +delta 		### Adjust the calculation by a configurable threshold		
    t=round(times[i],3)									### Get timestamp at that time slot
    # print(s)
    if s> 0:										### 'j' will be the count of clips whose loudness > threshold
        print('time, spectrum=', t,s)
        temp_rec[j] = [t,0,s]								### Record timestamp and spectrum at each slot whose spectrum exceed threshold
        j=j+1										### Add 1 to time-spectrum array counter (total record size = j, before merge)

spike_rec = temp_rec[0:j] 								### Extract 0:j (j records) from temp_rec and assign to spike_rec to limit range of array
temp_rec = spike_rec									### Copy spike_rec back to temp_rec, so array size will be limited to 'j' (last record)
rec_size = len(temp_rec )								### Get record size
start=[round(x[0],3) for x in temp_rec]							### Setup array of starting time of each clip by assigning starting values of temp_rec
end=[round(x[0],3) for x in temp_rec]							### Initially set array of ending time to the same (of starting time)
mag=[round(x[2],3) for x in temp_rec] 							### Set up array of magnitude by assigning magnitude values of temp_rec
end[0]=start[0]										### Make sure the 1st ending time = starting time initially
k=0											### 'k' is final count (after merge), and 'i' is the initial total clip count 
for i in range(0, rec_size):								### Now work on merge case. If the gap (between current and next) < foreward_gap, both will be merged. 
    if end[i] - end[k] < foreward_gap:							### check ending time gap (between next clip and current merged clip) 					
        end[k]=end[i]									###     If gap < foreward_gap, then shift ending time of current (new clip) to a new pointer
        if i==k:									###     This should happens to 1st clip. In case this is not shift case, let magnitude stays as it was  
            mag[k]=round(mag[k],3)							### 
        if i>j:										###     If this is merge of few clips
            mag[k]=round(max(mag[j:i+1]),3)						###     then find max.magnitude to represent this (merged) clip
    else:										### If this is not merge case
        if end[k]-start[k] < foreward_gap:						###     and If gap < foreward_gap
            end[k]=round(start[k]+foreward_gap,3)					###         then set ending time = starting time + foreward_gap 
        k=k+1										###     then increase final clip count (k) by 1
        j=i-1										###     then set pointer to previous one
        start[k]=round(end[i],3)							###     then set new starting time (start[k]) to where the current clip ended
        end[k]=round(end[i],3)								###     then set initial ending time to where the current clip ended

if end[k]-start[k] < foreward_gap:
    end[k]=round(start[k]+foreward_gap,3)

spike_rec_start = start[0:k+1]
spike_rec_end = end[0:k+1] 
spike_rec_mag = mag[0:k+1]
###################################################################  Integrate Audio and Video
# os.remove(audio_current_file)
# os.remove(audio_temp_file)
# os.remove(audio_output_file)
# os.remove(video_current_file)
# os.remove(video_temp_file)
# os.remove(video_output_file)
# os.remove(video_current_file_mpg)
# os.remove(video_temp_file_mpg)
# os.remove(video_current_file_mpg)
# os.remove(video_temp_file_ts)
# os.remove(video_current_file_ts)
# shutil.copy(audio_video_file, audio_video_backup)
# os.remove(audio_video_file)
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
################################################################### Extract and Integrate Audio and Video as ONE video + audio file
for i in range(0, len(spike_rec_start)):
    duration = str(round(spike_rec_end[i] - spike_rec_start[i],3)) 
    print('start=',spike_rec_start[i], 'end=',spike_rec_end[i])			### Below extract audio data for current timestamp
    cmd1_A="os.system('cd  "+audio_path+ ' & ' +video_path+'/ffmpeg -y -v quiet -ss '+str(spike_rec_start[i]) + ' -t '+ duration + ' -i '+ audio_file+'   '+audio_current_file+"')"
    exec(cmd1_A)								### Below extract video data for current timestamp
    cmd1_B="os.system('cd  "+video_path+ ' & ' +video_path+'/ffmpeg -y -i '+video_file+ ' -ss ' +str(spike_rec_start[i]) + '  -t '+str(duration) + ' -c:v libx264 -c:a copy  ' + video_current_file+"')"
    exec(cmd1_B)
    if i==0:									### Generate 1st video and audio outputs (without appending from previous ones)
        shutil.copy(audio_current_file, audio_output_file)
        shutil.copy(video_current_file, video_output_file)
    else:									
        shutil.copy(audio_output_file, audio_temp_file)				### below Generate succedding audio (current), append it to cummulative (temp) and produce 1 audio output
        cmd2_A="os.system('"+video_path+'/sox-14-4-2\sox ' +audio_current_file+'  '+audio_temp_file +'  '+audio_output_file+"')"  
        exec(cmd2_A)
        shutil.copy(video_output_file, video_temp_file)				### below Generate succedding video (current), append it to cummulative (temp) and produce 1 video output
	########################################################################### Due to nature of mp4, file need be converted to ts format for appending
        cmd3_B="os.system('"+video_path+'/ffmpeg -y -i ' +video_current_file+' -c copy -bsf:v h264_mp4toannexb -f mpegts   '+video_current_file_ts+"')"
        cmd4_B="os.system('"+video_path+'/ffmpeg -y -i ' +video_temp_file+' -c copy -bsf:v h264_mp4toannexb -f mpegts   '+video_temp_file_ts+"')"
        cmd5_B="os.system('"+video_path+'/ffmpeg -y -i "concat:' +video_temp_file_ts+'|'+video_current_file_ts+'"  -c copy -bsf:a aac_adtstoasc  '+video_output_file+"')"
        exec(cmd3_B)
        exec(cmd4_B)
        exec(cmd5_B)								### Below, the single audio and video output files are concatenated into one video + audio output file
        cmd_final="os.system('"+video_path+'/ffmpeg -y -i '+video_output_file+' -i   '+audio_output_file+'  -vcodec copy  '+audio_video_file+"')"
        exec(cmd_final)

################################################################### Temporarily leave lines below until finding resolution. Without this next run will get fail
audio_current.close()
audio_output.close()
audio_temp.close()
video_temp.close()
video_current.close()
video_output.close()
video_output_mpg.close()
video_temp_mpg.close()
video_temp_ts.close()
video_current_ts.close()
video_current_mpg.close()
audio_video.close()
################################################################### End of script




