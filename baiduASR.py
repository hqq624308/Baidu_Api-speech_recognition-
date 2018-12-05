import urllib.request
import urllib
import json
import base64
import os
import subprocess
import datetime
from pyaudio import PyAudio, paInt16
import numpy as np 
import wave
import pyaudio

class BaiduRest:
    def __init__(self, cu_id, api_key, api_secert):
        # token认证的url
        self.token_url = "https://openapi.baidu.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s"
        # 语音合成的resturl
        self.getvoice_url = "http://tsn.baidu.com/text2audio?tex=%s&lan=zh&cuid=%s&ctp=1&tok=%s"
        # 语音识别的resturl
        self.upvoice_url = 'http://vop.baidu.com/server_api'
        self.cu_id = cu_id
        self.getToken(api_key, api_secert)

    def getToken(self, api_key, api_secert):
        # 1.获取token
        token_url = self.token_url % (api_key,api_secert)
        r_str = urllib.request.urlopen(token_url).read()
        token_data = json.loads(r_str.decode('utf-8'))
        self.token_str = token_data['access_token']
        
    def getText(self, voice_data):
        data = {}
        # 语音的一些参数
        data['format'] = 'wav'
        data['rate'] = 16000
        data['channel'] = 1
        data['cuid'] = self.cu_id
        data['token'] = self.token_str
        data['len'] = len(voice_data)
        data['dev_pid'] = 1536
        data['speech'] = base64.b64encode(voice_data).decode('utf-8')
        post_data = json.dumps(data)
        r_data = urllib.request.urlopen(self.upvoice_url,data=bytes(post_data,encoding="utf-8")).read()
        # 3.处理返回数据
        try:
            result = json.loads(r_data.decode('utf-8'))['result'][0]
        except BaseException as e:
            result = ""
        return result