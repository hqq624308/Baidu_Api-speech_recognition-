# -*- coding: utf-8 -*-
import json
import flask
from flask import Flask
from flask import request
from flask import redirect
from flask import jsonify
import urllib.request
import urllib
import json
import base64
import os
import datetime
from pyaudio import PyAudio, paInt16
import numpy as np 
import pyaudio
import baiduASR
import time
import wave
import webrtcvad
import copy
from numba import jit
import contextlib
import sys
import wave
import random

SAMPLING_RATE=44100      #原始音频采样率
TargetFrameRate=16000    #降采样之后的采样率
framesz=30               #设置每帧的时间长度，可选择10ms,20ms,30ms

vad = webrtcvad.Vad(1)   #vad模式，等级从0,1,2,3选择，数字越大，对语音越敏感

app = Flask(__name__)

#此处设置百度的登入账号    #此处填写自己的百度申请的账号
api_key = "***********************"  
api_secert = "***************************"
bdr =  baiduASR.BaiduRest("test_python", api_key, api_secert)

@jit
def Resample(input_signal,src_fs,tar_fs): 
    '''
    :param input_signal:输入信号
    :param src_fs:输入信号采样率
    :param tar_fs:输出信号采样率
    :return:输出信号
    ''' 
    dtype = input_signal.dtype 
    audio_len = len(input_signal) 
    audio_time_max = 1.0*(audio_len-1) / src_fs 
    src_time = 1.0 * np.linspace(0,audio_len,audio_len) / src_fs 
    tar_time = 1.0 * np.linspace(0,np.int(audio_time_max*tar_fs),np.int(audio_time_max*tar_fs)) / tar_fs 
    output_signal = np.interp(tar_time,src_time,input_signal).astype(dtype) 
    return output_signal

class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

def frame_generator(frame_duration_ms, audio, sample_rate):
    """
    Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n

#主程序入口
##改进之后的功能：可以按照200ms一段的形式进行接收，后端来拼接进行识别，这一改动会比之前的识别速度更快
mergeAudio=[]
@app.route('/audio' , methods=['GET', 'POST'])
def audio():
    dict2={}
    global mergeAudio
    if request.method == 'POST':
        binAudio = request.files['audioData'].read()    
        waveData = np.fromstring(binAudio,dtype=np.int16)                             #将字符串转化为int
        outputAudio = Resample(waveData,SAMPLING_RATE,TargetFrameRate)
        outputAudio=outputAudio.tostring()   
        mergeAudio.extend(outputAudio)
        print('[2] the length of mergeAudio :: ',len(mergeAudio))
        frames = frame_generator(framesz, outputAudio, TargetFrameRate)    #采样率只能设置8k,16k,32k,而44.1k行不通      
        frames = list(frames)
        num_voiced = [1 if vad.is_speech(f.bytes, TargetFrameRate) else 0 for f in frames]

        start1 = time.time()
        text = bdr.getText(bytes(mergeAudio[:]))
        print("Baidu cost start1 :: ",time.time()-start1)
        dict2["result"] = text
        if text!='' and sum(num_voiced) == 0:     #此处判断音频是否停止，将原来的[-20:]即判断末尾的连续几帧之和是否为0，改为只判断传过来的那一段的语音是否说话
            dict2["isStop"] = 1
            print("First dict2::",dict2)
            return json.dumps(dict2)
        else:
            dict2["isStop"] = 0
            print("second dict2:: ",dict2)
            return json.dumps(dict2)
          
    else:
        return '<h1>只接受post请求！</h1>'

@app.route('/')
def Hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run("0.0.0.0",port=5051,debug=True)