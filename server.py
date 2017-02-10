import os, json, requests
from flask import Flask, request, abort, session

from linebot import (
	LineBotApi, WebhookParser
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
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET", "x"))

userDic = {}

#Parameters to get Watson Data
class WatsonInfo:
	URL = 'http://watson-erp-coffee.mybluemix.net/'
	LOGINURL = URL + 'api/login'
	MESSAGEURL = URL + 'api/login' 
	WATSONUSERID = 'coguser' 
	WATSONPASSWORD = 'watson!'
	COFFEEUSERID = 'C00011'
	COFFEEPASSWORD = 'XXXXXXXX'

@app.before_request
def session_management():
	# make the session last indefinitely until it is cleared
	session.permanent = True

@app.route('/')
def hello_world():
	global userDic
	inputUserId = 'xxx'
	inputText = 'XXXX'
	output = callWatsonTest(inputUserId,inputText)
	for k in userDic.keys():
		output = output + k + '\n'
	return 'You are not logged in' + output
	
@app.route("/callback", methods=['POST'])
def callback():
	global userDic
	# get X-Line-Signature header value
	signature = request.headers['X-Line-Signature']

	# get request body as text
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)
	print("Request body: " + body)

	# parse webhook body
	try:
		events = parser.parse(body, signature)
	except InvalidSignatureError:
		abort(400)
	# if event is MessageEvent and message is TextMessage, then echo text
	for event in events:
		if not isinstance(event, MessageEvent):
			continue
		if not isinstance(event.message, TextMessage):
			continue
		output = callWatson(event)

		line_bot_api.reply_message(
			event.reply_token,
			TextSendMessage(text=output)
		)
	return 'OK'

def callWatsonTest(inputUserId, inputText):
	global userDic
	print('start call watson')
	# set login data to dictionary
	userId = inputUserId
	if userId not in userDic or inputText != u'こんにちは':
		userDic[userId] = 'firstState'
	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	body = {"userId": "C00001","password": "xxxx"}
	r = s.post(WatsonInfo.LOGINURL,data=body)
	print(r.status_code)
	print(r.text)
	return r.text

def callWatson(event):
	global userDic
	print('start call watson')
	# set login data to dictionary
	userId = event.source.user_id
	if userId not in userDic or event.message.text != u'こんにちは':
		userDic[userId] = 'firstState'
	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	body = {"userId": WatsonInfo.COFFEEUSERID,"password": WatsonInfo.COFFEEPASSWORD}
	r = s.post(WatsonInfo.LOGINURL,data=body)
	print(r.status_code)
	print(r.text)
	return r.text


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
