##### Audio Raw Data Recording and Spike points identification
##### Author: Raymond Wu
##### Date: 2019.10.02
backward_delta = 0.3
forward_delta = 1.7
audio_path='C:/Scoville/Audio'
output_path='C:/Scoville/Audio/sample'
video_path='C:/Scoville/Video'
#####
##### Parameter Area Start ##### =>
import os.path
import os
import glob
import datetime
import shutil
str_EOF='EOF'
##### Parameter Area End <= #####
#####
# timestamp_file = max(glob.iglob('C:/Scoville/Audio_temporary/*timestamp.txt'), key=os.path.getctime)
timestamp_file = max(glob.iglob(audio_path+'/*timestamp.txt'), key=os.path.getctime)
timestamp_file = timestamp_file.replace(audio_path+'\\', '')
audio_timestamp_file = audio_path+'/'+timestamp_file
video_timestamp_file = video_path+'/'+timestamp_file
# timestamp_file = timestamp_file.replace('/', '\')
print ('timestamp_file=',timestamp_file)
audio_file=audio_timestamp_file.replace("_timestamp.txt", ".wav")
audio_current_file=audio_path+'/current.wav'
audio_temp_file=audio_path+'/temp.wav'
audio_output_file=audio_file.replace(".wav", "_output.wav")
video_file=video_timestamp_file.replace("_timestamp.txt", ".mp4")
video_current_file=video_path+'/current.mp4'
video_temp_file=video_path+'/temp.mp4'
video_current_file_mpg=video_current_file.replace(".mp4", ".mpg")
video_temp_file_mpg=video_temp_file.replace(".mp4", ".mpg")
video_output_file=video_file.replace(".mp4", "_output.mp4")
video_output_file_mpg=video_output_file.replace(".mp4", ".mpg")
############# Extract clip based on Audio raw data + Metadata (spike points)
with open(audio_timestamp_file) as file: 
    line = file.readlines()
    line = [x.strip() for x in line] 
    print(line)
    line[0]=line[0].replace("@", "")

for i in range(1, len(line)-1):
# for i in range(1, 50):
    if line[i].find(str_EOF) == -1:
        start = float(line[i]) - backward_delta
        end = float(line[i]) + forward_delta
        duration = end - start
        print(i,start,duration,end)
        if start < 0:
            start=0
        if duration <= 0:
            duration=0.1
        output_file=output_path+'/breaking_glass_'+str(i)+'.wav'
        cmd1="os.system('"+video_path+'/ffmpeg -y -v quiet -ss '+str(start) + ' -t '+str(duration) + ' -i ' + audio_file + '  ' +output_file+"')"
        # cmd1="os.system('"+video_path+'/ffmpeg -y -v quiet -ss '+str(start) + ' -t '+str(duration) + ' -i ' + audio_file + '  ' +audio_current_file+"')"
        print(cmd1)
        exec(cmd1)
        # output_file=output_path+'/breaking_glass_'+str(i)+'.wav'
        # audio_current_file=audio_current_file.replace(audio_path+'/',"")
        # cmd2="os.system('cd "+audio_path+' & type '+audio_current_file+' > '+output_file+"')"
        # exec(cmd2)


