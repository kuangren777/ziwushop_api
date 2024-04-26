# -*- coding: utf-8 -*-
# @Time    : 2024/4/26 20:38
# @Author  : KuangRen777
# @File    : email_sender.py
# @Tags    :
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from PASSWORD import *


def send_verification_email(email: str, code: str):
    # 创建邮件对象
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = email
    message["Subject"] = "Your Verification Code From 子午商城"

    # 邮件正文内容
    body = f"Here is your verification code: {code}. It will expire in 10 minutes."
    message.attach(MIMEText(body, "plain"))

    # 使用SMTP服务发送邮件
    server = smtplib.SMTP('smtp.163.com', 25)  # 服务器地址和端口
    server.starttls()  # 启用安全传输模式
    server.login(sender_email, sender_password)
    text = message.as_string()
    server.sendmail(sender_email, email, text)
    server.quit()
