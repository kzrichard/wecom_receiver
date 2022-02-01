#!/bin/env python
# -*- coding:utf-8 -*-
# _auth:kaliarch

# 定义微信公众号信息
[common]
# 企业微信企业ID
corpid = wwfd8639daf72557fa


# 接收消息服务器配置
[recmsg]

Token = EwCvOX2lel2s01D0ps4ICVA2qpFc4Z
EncodingAESKey = tCWLSnlOtDDWXpOTaBapLiHEEY5eiwDu6tSX6rrOdOF

[netsuiteconfig]
clientkey = 6b2f33f05fa906c1a26892d24d59447308f1856669f1d7f2b4fa3a08ba85d88e
client_secret = f81fad7103454e281301cbcb53dfc40e5dc486fa21db09a8343110617500ef5f
resource_owner_key = 815523cd4bf66ba22d69ecdb4d901a7719a42ff4377bb0a3df556a4d83b47386
resource_owner_secret = 9ec9653e342817478019f9e91f4f61ef77274c5266e6a1c407f2bfbda4005a86
realm = 4695594

[netsuiteappconfig]
# 自建应用agentid
agentid = 1000015
# 自建应用secret
secret = aOtpkH2u48HXC5DwNPwS5dwc1gk9pkAiloBdphXy1OY

Token = j8pZGya
EncodingAESKey = wi2VjHNsfvpYmk4o3tnQ74iqlZR8PNAM41ydD5dVirr

[itappconfig]
# 自建应用agentid
agentid = 1000012
# 自建应用secret
secret = XpM7Cp_oU4D5s-qSk0P2PGvYTiPGCjrc1p7k-s6q6JA

Token = fRkurOWyKBb81Xje4yLoTl6Qd
EncodingAESKey = i6PPueBXhth3NFbVzbRrse1uDU7dCF2u0NZFDbQsAHR

[trelloappconfig]
# 自建应用agentid
agentid = 1000011
# 自建应用secret
secret = WelM7ceD2v1BBN3na3bqOeZRHjT_tn5Ik0RLGsrlKAM

Token = 2PBlC2b2RdI1Bnluy33pdz
EncodingAESKey = uUHksquWXbfEWlQE2McBK4VL2ZJAWYzhv2WEMbxxyix


# 自建应用信息  
[appconfig]
# 自建应用agentid
agentid = 1000010
# 自建应用secret
secret = 8gE9_Sy18W-2bTLCL6yHkh1csMS5Uup9j9EjCLaHtL0

contact_secret = e027iwS5YQu90RZOIGGpiiJct2mbvvBnizvLobhVhvg


[trello]
trello_api_key = 154af6614777c2fc5a50f4d5d57e9aa1
trello_api_secret = 22e85f9bf3185242314f767e196cd76903aff6d751c80261461c23a9b1414bb9
trello_token = 930a190bc175d2140f60f922515c9a1df7ba0a3d10c395fe8684c5827c74554c



[urlconfig]
# 获取应用token的api接口
get_access_token_url = https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={}&corpsecret={}
# 发送消息api接口
send_msg_url = https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={}
# 上传媒体api接口,获取mediaid
upload_media_url = https://qyapi.weixin.qq.com/cgi-bin/media/upload?access_token={}&type=image
# 上传高清语音接口
upload_video_url = https://qyapi.weixin.qq.com/cgi-bin/media/get/jssdk?access_token={}&media_id={}
# 获取成员信息
get_all_users_url = https://qyapi.weixin.qq.com/cgi-bin/user/list?access_token={}&department_id={}&fetch_child={}

[loginfo]
#日志目录
logdir_name = logdir
#日志文件名称
logfile_name = wechat_server.log
