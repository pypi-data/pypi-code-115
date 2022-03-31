#!/usr/bin/env python3
# coding = utf8
from dingtalkchatbot.chatbot import DingtalkChatbot
from urllib import parse
import hashlib
import base64
import time
import hmac
environment_now = env_reader.Default('notifier_dingding')
webhook_default = environment_now.webhook
secret_default = environment_now.secret
at_ids_default = environment_now.at_ids
"""
文档：https://developers.dingtalk.com/document/app/document-upgrade-notice
https://developers.dingtalk.com/document/app/overview-of-group-robots?spm=ding_open_doc.document.0.0.ac7828e1477wnC#topic-2026024
自定义机器人接入：https://developers.dingtalk.com/document/app/custom-robot-access?spm=ding_open_doc.document.0.0.37f37b4b2asVMv#topic-1914047
"""


class Basics:
    def __init__(
            self,
            webhook=None,
            secret=None
    ):
        if webhook is None:
            self.webhook = webhook_default
        else:
            self.webhook = webhook
        if secret is None:
            self.secret = secret_default
        else:
            self.secret = secret
        self.ding = self.make_bot()

    def make_bot(
            self
    ):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = parse.quote_plus(base64.b64encode(hmac_code))
        webhook_new = '%s&timestamp=%s&sign=%s' % (self.webhook, timestamp, sign)
        ding = DingtalkChatbot(webhook_new)
        return ding

    def send_text(
            self,
            msg,
            is_at_all=False,
            at_ids=None
    ):
        if at_ids is not None:
            return self.ding.send_text(msg=msg,
                                       is_at_all=is_at_all,
                                       at_dingtalk_ids=at_ids)
        else:
            return self.ding.send_text(msg=msg,
                                       is_at_all=is_at_all)


def send_text(
        msg,
        is_at=False,
        at_ids=at_ids_default
):
    ding_bot = Basics()
    try:
        if is_at is True:
            ding_bot.send_text(msg=msg, at_ids=at_ids)
        else:
            ding_bot.send_text(msg=msg)

        return True
    except:

        return False
