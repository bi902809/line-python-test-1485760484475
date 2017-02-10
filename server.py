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
	RESETWORD = u'こんにちは'

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
		callWatson(event)
		userId = event.source.user_id
		if userDic[userId]['nextFrontAction'] == 'firstAction':
			firstAction(event)
	return 'OK'

def callWatson(event):
	global userDic
	print('start call watson')
	#Watson Authentications
	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	# set login data to dictionary
	userId = event.source.user_id
	if userId not in userDic or event.message.text != WatsonInfo.RESETWORD:
		userDic[userId] = {}
		body = {"userId": WatsonInfo.COFFEEUSERID,"password": WatsonInfo.COFFEEPASSWORD}
		r = s.post(WatsonInfo.LOGINURL,data=body)
		result = json.loads(r.text)
		userDic[userId] = result['context']
		userDic[userId]['nextFrontAction'] = 'firstAction'

def firstAction(event):
	global userDic
	userId = event.source.user_id
	output = u'こんにちは、' + userDic[userId]['customerNameJa'] + u'様。香りでコーヒーを選んでみるのも良いですね。どのようなご用件でしょうか？'
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=output)
	)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
