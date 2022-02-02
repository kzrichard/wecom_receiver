#!/bin/env python
# -*- coding:utf-8 -*-
# _auth:kaliarch

from flask import Flask,request
from WXBizMsgCrypt import WXBizMsgCrypt
import xml.etree.cElementTree as ET
import sys
import requests
import json
from configparser import ConfigParser
import logger
from threading import Thread
from trello import TrelloClient
from requests_oauthlib import OAuth1Session
from waitress import serve

class WeChatMsg():
    def __init__(self,logger,host='0.0.0.0',port=8080):

        config = ConfigParser()
        config.read('config.py', encoding='utf-8')
        self.host = host
        self.port = port

        # config information for phone lookup agent
        self.agent_id = config['appconfig']['agentid']
        self.agent_secret = config['appconfig']['secret']
        self.sToken = config['recmsg']['Token']
        self.sEncodingAESKey = config['recmsg']['EncodingAESKey']
        self.sCorpID = config['common']['corpid']

        # config information for netsuite agent lookup
        self.netsuite_agent_id = config['netsuiteappconfig']['agentid']
        self.netsuite_agent_secret = config['netsuiteappconfig']['secret']
        self.netsuite_sToken = config['netsuiteappconfig']['Token']
        self.netsuite_sEncodingAESKey = config['netsuiteappconfig']['EncodingAESKey']

        # netsuite api config
        self.netsuite_clientkey = config['netsuiteconfig']['clientkey']
        self.netsuite_client_secret = config['netsuiteconfig']['client_secret']
        self.netsuite_resource_owner_key = config['netsuiteconfig']['resource_owner_key']
        self.netsuite_resource_owner_secret = config['netsuiteconfig']['resource_owner_secret']
        self.netsuite_realm = config['netsuiteconfig']['realm']

        # config information for trello card agent lookup
        self.trello_agent_id = config['trelloappconfig']['agentid']
        self.trello_agent_secret = config['trelloappconfig']['secret']
        self.trello_sToken = config['trelloappconfig']['Token']
        self.trello_sEncodingAESKey = config['trelloappconfig']['EncodingAESKey']

        # trello api config
        self.trello_api_key = config['trello']['trello_api_key']
        self.trello_api_secret = config['trello']['trello_api_secret']
        self.trello_token = config['trello']['trello_token']

        # config information for IT agent lookup
        self.it_agent_id = config['itappconfig']['agentid']
        self.it_agent_secret = config['itappconfig']['secret']
        self.it_sToken = config['itappconfig']['Token']
        self.it_sEncodingAESKey = config['itappconfig']['EncodingAESKey']

        # config information for performance review agent lookup
        self.performance_review_agent_id = config['performancereviewconfig']['agentid']
        self.performance_review_agent_secret = config['performancereviewconfig']['secret']
        self.performance_review_sToken = config['performancereviewconfig']['Token']
        self.performance_review_sEncodingAESKey = config['performancereviewconfig']['EncodingAESKey']

        # contact secret that can access the contacts on WeCom
        self.contact_secret = config['appconfig']['contact_secret']

        # api service urls
        self.send_msg_url = config['urlconfig']['send_msg_url']
        self.get_all_users_url = config['urlconfig']['get_all_users_url']
        self.get_access_token_url = config['urlconfig']['get_access_token_url']

        # log on the logging file
        logger = logger.LogHelper()
        logname = logger.create_dir()
        self.logoper = logger.create_logger(logname)

    # default searching message to indicate users
    # that the searching is on the way
    def _send_searching_text_msg(self, search_object, sent_user_id, sent_agent_id, access_token):
            try: 
                # compose sent message with required parameters
                data = {
                    "touser": sent_user_id,
                    "msgtype": "text",
                    "agentid": sent_agent_id,
                    "text": {
                        "content": "正在寻找与" + search_object + "相关资讯..."
                    },
                    "safe": 0,
                }

                # send searching message
                res = requests.post(self.send_msg_url.format(access_token), json.dumps(data))
            except Exception as e:
                self.logoper.info(e)

    def _send_trello_text_msg(self, card_name, sent_user_id, access_token):
        try:
            self._send_searching_text_msg("Trello", sent_user_id, self.trello_agent_id, access_token)

            # create trello client and locate
            # KZ Project Portal and visible cards on the board
            trello_client = TrelloClient(
                api_key=self.trello_api_key,
                api_secret=self.trello_api_secret,
                token=self.trello_token,
            )

            kz_project_portal = trello_client.list_boards()[5]
            kz_project_portal_cards = kz_project_portal.visible_cards()

            card_found = False
            card_info = "以下为Trello搜寻结果: \n"

            counter = 0
            RESULT_LIMIT = 6

            # go through the card
            # to see if there are names matching the given title
            for card in kz_project_portal_cards:
                label = ""
                if card.labels is not None:
                    label = card.labels[0].name
                    if card_name.lower() in card.name.lower() and counter < RESULT_LIMIT:
                        card_found = True
                        counter += 1 
                        card_info += label + " - <a href=" + "\"" + card.url + "\">" + card.name + "</a>\n"
            
            # show not found message when there are no matching card
            if not card_found:
                card_info = "查无此资料。\n请确认搜寻内容并重试。"
            card_info += "\n请参考<a href=" + "\"" + kz_project_portal.url + "\">" + kz_project_portal.name + "</a>得到更多资讯。\n" 
            
            # send the message
            result_msg = self._send_text_msg(card_info, self.trello_agent_id, sent_user_id, access_token)
            return result_msg
        except Exception as e:
            self.logoper.info(e)

    def _send_phone_text_msg(self, user_name, sent_user_id, access_token):
        try:
            self._send_searching_text_msg("Phone", sent_user_id, self.agent_id, access_token)
            # create an access token that can retreive information
            # from contact list on WeCom
            contact_access_token = json.loads(requests.get(self.get_access_token_url.format(self.sCorpID,self.contact_secret)).content)['access_token']
            FETCH_CHILD = 1
            ALL_DEPARTMENT_ID = 1

            # retrieve current user list on WeCom
            user_list = json.loads(requests.get(self.get_all_users_url.format(contact_access_token, ALL_DEPARTMENT_ID, FETCH_CHILD)).content)["userlist"]

            user_found = False
            phone_info = "以下为电话搜寻结果: \n"

            counter = 0
            RESULT_LIMIT = 6

            contact_list_url = "https://docs.google.com/spreadsheets/d/1ZztYcKmeIJY6bOM6qLdPAEyte-2puibbe8_kmaItzqU/edit?usp=sharing"

            # go through the user list 
            # and see if there are employee's names with given word
            for user in user_list:
                if user_name.lower() in user["name"].lower() and counter < RESULT_LIMIT:
                    user_found = True
                    counter += 1
                    phone_number = user["extattr"]["attrs"][0]["value"]
                    extension = user["telephone"]

                    # show availablity of the phone and extension
                    if len(phone_number) == 0:
                        phone_info += str(user["name"] + ": " + "暂无电话资讯\n")
                    else: 
                        phone_info += str(user["name"]) + ": " + str(phone_number + "x " + extension + "\n")
            
            # show no users found if there is no employee's name with given word
            if not user_found:
                phone_info = "查无此用户。\n请确认搜寻内容并重试。"
            phone_info += "\n请参考<a href=" + "\"" + contact_list_url + "\">长实内部通讯录</a>得到更多资讯。\n" 

            result_msg = self._send_text_msg(phone_info, self.agent_id, sent_user_id, access_token)
            return result_msg
        except Exception as e:
            self.logoper.info(e)

    def _send_anydesk_text_msg(self, user_name, sent_user_id, access_token):
        try:
            self._send_searching_text_msg("AnyDesk", sent_user_id, self.it_agent_id, access_token)
            
            # authentication information in order to access
            # restlet on NetSuite
            url = "https://4695594.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=407&deploy=1&user=" + user_name

            oauth = OAuth1Session(
                client_key=self.netsuite_clientkey,
                client_secret=self.netsuite_client_secret,
                resource_owner_key=self.netsuite_resource_owner_key,
                resource_owner_secret=self.netsuite_resource_owner_secret,
                realm=self.netsuite_realm)

            resp = oauth.get(
                url,
                headers={'Content-Type': 'application/json'},
            )

            # equipment list with given user returned
            # from restlet on NetSuite
            equipment_list = json.loads(json.loads(resp.text))

            anydesk_found = False
            anydesk_info = "以下为设备搜寻结果: \n"

            # go through the list and compose the message
            for equipment in equipment_list:
                anydesk_found = True
                equip_name = equipment["name"]
                equip_anydeskId = equipment["anydeskId"]
                equip_assign_to = equipment["assignTo"]
                equip_department = equipment["department"]
                anydesk_info += equip_assign_to + " at " + equip_department + " with " + equip_name + ": " + equip_anydeskId + "\n\n"

            if not anydesk_found:
                anydesk_info = "查无此设备。\n请确认搜寻内容并重试。"
            
            result_msg = self._send_text_msg(anydesk_info, self.it_agent_id, sent_user_id, access_token)
            return result_msg
            
        # check the type error when equipment list is received from NetSuite reslet
        # there might be an error with searching term if it gets to this exception
        except TypeError as type_err:
            anydesk_info = "查无此设备。\n请确认搜寻内容并重试。"
            result_msg = self._send_text_msg(anydesk_info, self.it_agent_id, sent_user_id, access_token)
            return result_msg
        except Exception as e:
            self.logoper.info(e)

    def _send_netsuite_text_msg(self, term, sent_user_id, access_token):
        try:
            self._send_searching_text_msg("NetSuite", sent_user_id, self.netsuite_agent_id, access_token)
            GLOBAL_SEARCH_URL = "https://4695594.app.netsuite.com/app/common/search/ubersearchresults.nl?quicksearch=T&searchtype=Uber&frame=be&Uber_NAMEtype=KEYWORDSTARTSWITH&Uber_NAME="
            
            # authentication information in order to access
            # restlet on NetSuite
            url = "https://4695594.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=415&deploy=1&term=" + term
            oauth = OAuth1Session(
                client_key=self.netsuite_clientkey,
                client_secret=self.netsuite_client_secret,
                resource_owner_key=self.netsuite_resource_owner_key,
                resource_owner_secret=self.netsuite_resource_owner_secret,
                realm=self.netsuite_realm)

            resp = oauth.get(
                url,
                headers={'Content-Type': 'application/json'},
            )

            # equipment list with given user returned
            # from restlet on NetSuite
            record_list = json.loads(json.loads(resp.text))

            record_info = "以下为单号搜寻结果: \n"

            counter = 0
            RESULT_LIMIT = 6
            record_found = False

            for key in record_list:
                if counter >= RESULT_LIMIT:
                    break
                record_found = True
                record_name = key
                record_url = record_list[key]
                record_info += "<a href=" + "\"" + record_url + "\">" + record_name + "</a>\n"
                counter += 1
            if not record_found:
                record_info = "查无此单号。\n请确认搜寻内容并重试。"

            global_search_more_result = GLOBAL_SEARCH_URL + term
            record_info += "\n如无查询结果请点击<a href=" + "\"" + global_search_more_result + "\">更多结果</a>查询。"

            result_msg = self._send_text_msg(record_info, self.netsuite_agent_id, sent_user_id, access_token)
            return result_msg

        # check the type error when equipment list is received from NetSuite reslet
        # there might be an error with searching term if it gets to this exception
        except TypeError as type_err:
            record_info = "查无此单号。\n请确认搜寻内容并重试。"
            result_msg = self._send_text_msg(record_info, self.netsuite_agent_id, sent_user_id, access_token)
            return result_msg
        except Exception as e:
            self.logoper.info(e)

    def _send_performace_review_text_msg(self, email, sent_user_id, access_token):
        try:
            self._send_searching_text_msg("Performance Review", sent_user_id, self.performance_review_agent_id, access_token)
            
            # authentication information in order to access
            # restlet on NetSuite
            url = "https://4695594.restlets.api.netsuite.com/app/site/hosting/restlet.nl?script=1580&deploy=1&email=" + email

            oauth = OAuth1Session(
                client_key=self.netsuite_clientkey,
                client_secret=self.netsuite_client_secret,
                resource_owner_key=self.netsuite_resource_owner_key,
                resource_owner_secret=self.netsuite_resource_owner_secret,
                realm=self.netsuite_realm)

            resp = oauth.get(
                url,
                headers={'Content-Type': 'application/json'},
            )

            # equipment list with given user returned
            # from restlet on NetSuite
            performance_review_result = json.loads(resp.text)

            # anydesk_found = False
            performance_review_info = "以下为考评分数搜寻结果: \n"
            performance_review_info += "工作能力：" + performance_review_result["productivityScore"] + "\n"
            performance_review_info += "细心程度：" + performance_review_result["complianceScore"] + "\n"
            performance_review_info += "工作态度：" + performance_review_result["attitudeScore"] + "\n"
            performance_review_info += "遵守纪律制度：" + performance_review_result["disciplineScore"] + "\n"
            performance_review_info += "团队配合度：" + performance_review_result["teamworkScore"] + "\n"
            performance_review_info += "最终总成绩：" + performance_review_result["finalScore"] + "\n"

            # # go through the list and compose the message
            # for equipment in equipment_list:
            #     anydesk_found = True
            #     equip_name = equipment["name"]
            #     equip_anydeskId = equipment["anydeskId"]
            #     equip_assign_to = equipment["assignTo"]
            #     equip_department = equipment["department"]
            #     anydesk_info += equip_assign_to + " at " + equip_department + " with " + equip_name + ": " + equip_anydeskId + "\n\n"

            # if not anydesk_found:
            #     anydesk_info = "查无此设备。\n请确认搜寻内容并重试。"
            
            result_msg = self._send_text_msg(performance_review_info, self.performance_review_agent_id, sent_user_id, access_token)
            return result_msg
            
        # check the type error when equipment list is received from NetSuite reslet
        # there might be an error with searching term if it gets to this exception
        except TypeError as type_err:
            performance_review_info = "考评记录无出现与此用户相关的记录。\n请确认搜寻内容或此用户尚未达到考评资格。"
            result_msg = self._send_text_msg(performance_review_info, self.performance_review_agent_id, sent_user_id, access_token)
            return result_msg
        except Exception as e:
            self.logoper.info(e)

    # send text message with given content to the given user id
    def _send_text_msg(self, content, agenet_id, sent_user_id, access_token):
        try:
            # send data with introductory message
            data = {
                "touser": sent_user_id,
                "msgtype": "text",
                "agentid": agenet_id,
                "text": {
                    "content": content
                },
                "safe": 0,
            }
            response = requests.post(self.send_msg_url.format(access_token), json.dumps(data))
            self.logoper.info(response.text)
            result_msg = json.loads(response.content)['errmsg']
            return result_msg
        except Exception as e:
            self.logoper.info(e)

# def server_run(self):
# wechatserver = WeChatMsg(logger)
app = Flask(__name__)
@app.route('/index', methods=['GET', 'POST'])
def index():
    wechatserver = WeChatMsg(logger)
    wxcpt = WXBizMsgCrypt(wechatserver.sToken, wechatserver.sEncodingAESKey, wechatserver.sCorpID)

    # get paramaters for authentication from WeCom
    sVerifyMsgSig = request.args.get('msg_signature')
    sVerifyTimeStamp = request.args.get('timestamp')
    sVerifyNonce = request.args.get('nonce')
    sVerifyEchoStr = request.args.get('echostr')

    # authenticate url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        if (ret != 0):
            print("ERR: VerifyURL ret:" + str(ret))
            sys.exit(1)
        return sEchoStr

    # get the message from clients
    if request.method == 'POST':
        access_token = json.loads(requests.get(wechatserver.get_access_token_url.format(wechatserver.sCorpID,wechatserver.agent_secret)).content)['access_token']
        sReqMsgSig = sVerifyMsgSig
        sReqTimeStamp = sVerifyTimeStamp
        sReqNonce = sVerifyNonce
        sReqData = request.data

        ret, sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print("ERR: DecryptMsg ret: " + str(ret))
            sys.exit(1)
        
        # retrieve message contens
        xml_tree = ET.fromstring(sMsg)
        content_type = xml_tree.find("MsgType").text

        # process if the content type is text
        if content_type == "text":
            content = xml_tree.find("Content").text
            from_user_id = xml_tree.find("FromUserName").text
            
            # use thread to save response time before timeout
            Thread(target=wechatserver._send_phone_text_msg, args=(content, from_user_id, access_token)).start()
            return '',200
        else:
            return

@app.route('/trello', methods=['GET', 'POST'])

def trello():
    wechatserver = WeChatMsg(logger)
    wxcpt = WXBizMsgCrypt(wechatserver.trello_sToken, wechatserver.trello_sEncodingAESKey, wechatserver.sCorpID)

    # get paramaters for authentication from WeCom
    sVerifyMsgSig = request.args.get('msg_signature')
    sVerifyTimeStamp = request.args.get('timestamp')
    sVerifyNonce = request.args.get('nonce')
    sVerifyEchoStr = request.args.get('echostr')

    # authenticate url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)

        if (ret != 0):
            print("ERR: VerifyURL ret:" + str(ret))
            sys.exit(1)
        return sEchoStr

    # get the message from clients
    if request.method == 'POST':
        access_token = json.loads(requests.get(wechatserver.get_access_token_url.format(wechatserver.sCorpID,wechatserver.trello_agent_secret)).content)['access_token']
        sReqMsgSig = sVerifyMsgSig
        sReqTimeStamp = sVerifyTimeStamp
        sReqNonce = sVerifyNonce
        sReqData = request.data

        ret, sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print("ERR: DecryptMsg ret: " + str(ret))
            sys.exit(1)
        
        # retrieve message contens
        xml_tree = ET.fromstring(sMsg)
        content_type = xml_tree.find("MsgType").text

        # process if the content type is text
        if content_type == "text":
            content = xml_tree.find("Content").text
            from_user_id = xml_tree.find("FromUserName").text
            
            # use thread to save response time before timeout
            Thread(target=wechatserver._send_trello_text_msg, args=(content, from_user_id, access_token)).start()
            return '',200
        else:
            return

@app.route('/it', methods=['GET', 'POST'])
def it():
    wechatserver = WeChatMsg(logger)
    wxcpt = WXBizMsgCrypt(wechatserver.it_sToken, wechatserver.it_sEncodingAESKey, wechatserver.sCorpID)

    # get paramaters for authentication from WeCom
    sVerifyMsgSig = request.args.get('msg_signature')
    sVerifyTimeStamp = request.args.get('timestamp')
    sVerifyNonce = request.args.get('nonce')
    sVerifyEchoStr = request.args.get('echostr')

    # authenticate url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        
        if (ret != 0):
            print("ERR: VerifyURL ret:" + str(ret))
            sys.exit(1)
        return sEchoStr

    # get the message from clients
    if request.method == 'POST':
        access_token = json.loads(requests.get(wechatserver.get_access_token_url.format(wechatserver.sCorpID,wechatserver.it_agent_secret)).content)['access_token']
        sReqMsgSig = sVerifyMsgSig
        sReqTimeStamp = sVerifyTimeStamp
        sReqNonce = sVerifyNonce
        sReqData = request.data

        ret, sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print("ERR: DecryptMsg ret: " + str(ret))
            sys.exit(1)
        
        # retrieve message contens
        xml_tree = ET.fromstring(sMsg)
        content_type = xml_tree.find("MsgType").text

        # process if the content type is text
        if content_type == "text":
            content = xml_tree.find("Content").text
            from_user_id = xml_tree.find("FromUserName").text
            
            # use thread to save response time before timeout
            Thread(target=wechatserver._send_anydesk_text_msg, args=(content, from_user_id, access_token)).start()
            return '',200
        else:
            return

@app.route('/netsuite', methods=['GET', 'POST'])
def netsuite():
    wechatserver = WeChatMsg(logger)
    wxcpt = WXBizMsgCrypt(wechatserver.netsuite_sToken, wechatserver.netsuite_sEncodingAESKey, wechatserver.sCorpID)

    # get paramaters for authentication from WeCom
    sVerifyMsgSig = request.args.get('msg_signature')
    sVerifyTimeStamp = request.args.get('timestamp')
    sVerifyNonce = request.args.get('nonce')
    sVerifyEchoStr = request.args.get('echostr')

    # authenticate url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)

        if (ret != 0):
            print("ERR: VerifyURL ret:" + str(ret))
            sys.exit(1)
        return sEchoStr

    # get the message from clients
    if request.method == 'POST':
        access_token = json.loads(requests.get(wechatserver.get_access_token_url.format(wechatserver.sCorpID,wechatserver.netsuite_agent_secret)).content)['access_token']
        sReqMsgSig = sVerifyMsgSig
        sReqTimeStamp = sVerifyTimeStamp
        sReqNonce = sVerifyNonce
        sReqData = request.data

        ret, sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print("ERR: DecryptMsg ret: " + str(ret))
            sys.exit(1)
        
        # retrieve message contens
        xml_tree = ET.fromstring(sMsg)
        content_type = xml_tree.find("MsgType").text

        # process if the content type is text
        if content_type == "text":
            content = xml_tree.find("Content").text
            from_user_id = xml_tree.find("FromUserName").text
            
            # use thread to save response time before timeout
            Thread(target=wechatserver._send_netsuite_text_msg, args=(content, from_user_id, access_token)).start()
            return '',200
        else:
            return

@app.route('/performance_review', methods=['GET', 'POST'])
def performance_review():
    wechatserver = WeChatMsg(logger)
    wxcpt = WXBizMsgCrypt(wechatserver.performance_review_sToken, wechatserver.performance_review_sEncodingAESKey, wechatserver.sCorpID)

    # get paramaters for authentication from WeCom
    sVerifyMsgSig = request.args.get('msg_signature')
    sVerifyTimeStamp = request.args.get('timestamp')
    sVerifyNonce = request.args.get('nonce')
    sVerifyEchoStr = request.args.get('echostr')

    # authenticate url
    if request.method == 'GET':
        ret, sEchoStr = wxcpt.VerifyURL(sVerifyMsgSig, sVerifyTimeStamp, sVerifyNonce, sVerifyEchoStr)
        
        if (ret != 0):
            print("ERR: VerifyURL ret:" + str(ret))
            sys.exit(1)
        return sEchoStr

    # get the message from clients
    if request.method == 'POST':
        access_token = json.loads(requests.get(wechatserver.get_access_token_url.format(wechatserver.sCorpID,wechatserver.performance_review_agent_secret)).content)['access_token']
        sReqMsgSig = sVerifyMsgSig
        sReqTimeStamp = sVerifyTimeStamp
        sReqNonce = sVerifyNonce
        sReqData = request.data

        ret, sMsg = wxcpt.DecryptMsg(sReqData, sReqMsgSig, sReqTimeStamp, sReqNonce)
        if (ret != 0):
            print("ERR: DecryptMsg ret: " + str(ret))
            sys.exit(1)
        
        # retrieve message contens
        xml_tree = ET.fromstring(sMsg)
        content_type = xml_tree.find("MsgType").text

        # process if the content type is text
        if content_type == "text":
            content = xml_tree.find("Content").text
            from_user_id = xml_tree.find("FromUserName").text
            
            # use thread to save response time before timeout
            Thread(target=wechatserver._send_performace_review_text_msg, args=(content, from_user_id, access_token)).start()
            return '',200
        else:
            return

# app.run(host="96.74.99.243", port=5000, debug=True)

def create_app():
    # wechatserver = WeChatMsg(logger)
    # app = wechatserver.server_run()

    serve(app,host="0.0.0.0", port=5000)

    return app


# if __name__ == '__main__':
    # wechatserver = WeChatMsg(logger)
    # wechatserver.server_run()
    # serve(app,host="96.74.99.243", port=5000)
    