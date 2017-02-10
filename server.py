import os, json, requests
from flask import Flask, request, abort, session

from linebot import (
	LineBotApi, WebhookHandler
)
from linebot.exceptions import (
	InvalidSignatureError
)
from linebot.models import (
	MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)
port = int(os.getenv('PORT', 8080))
app.secret_key = os.urandom(24)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "x"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET", "x"))

userDic = {}

#Parameters to get Watson Data
url = 'http://watson-erp-coffee.mybluemix.net/'
loginUrl = 'api/login'
messageUrl = 'api/login'
watsonUserId = 'conguser'
watsonPassword = 'watson!'

@app.before_request
def session_management():
	# make the session last indefinitely until it is cleared
	session.permanent = True

@app.route('/')
def hello_world():
	global userDic
	output = ''
	for k in userDic.keys():
		output = output + k + '\n'
	return 'You are not logged in' + output
	
@app.route("/callback", methods=['POST'])
def callback():
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)
	print("Request body: " + body)

	# handle webhook body
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)

	return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	# set login data to dictionary
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=callWatson(event)))

def callWatson(event):
	global userDic
	userId = event.source.userId
	if userId not in userDic or event.message.text != u'こんにちは':
		userId[userDic] = 'firstState'
	s = requests.Session()
	s.auth = (watsonUserId, watsonPassword)
	body = {"userId": "C00001","password": "xxxx"}
	r = s.post(url + loginUrl,data=body)
	
	return r.text


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
