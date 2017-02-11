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
    SourceUser, SourceGroup, SourceRoom,
    TemplateSendMessage, ConfirmTemplate, MessageTemplateAction,
    ButtonsTemplate, URITemplateAction, PostbackTemplateAction,
    CarouselTemplate, CarouselColumn, PostbackEvent,
    StickerMessage, StickerSendMessage, LocationMessage, LocationSendMessage,
    ImageMessage, VideoMessage, AudioMessage,
    UnfollowEvent, FollowEvent, JoinEvent, LeaveEvent, BeaconEvent
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
	MESSAGEURL = URL + 'api/message' 
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

	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	#body = {"userId": WatsonInfo.COFFEEUSERID,"password": WatsonInfo.COFFEEPASSWORD}
	headers = { 'Content-Type': 'application/json'}
	config = { "customerId": "C00011", "customerNameJa": "箱崎太郎"}
	input = { "text": ""}
	body = {"context": config, "input": input}
	r = s.post(WatsonInfo.MESSAGEURL,data=json.dumps(body),headers = headers)

	# set login data to dictionary
	output = ''
	for k in userDic.keys():
		output = output + k + '\n'
	return 'You are not logged in' + r.text
	
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
		userId = event.source.user_id
		if userDic[userId]['nextFrontAction'] == 'firstAction':
			firstAction(event, output)
	return 'OK'

def callWatson(event):
	global userDic
	print('start call watson')
	#Watson Authentications
	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	headers = { 'Content-Type': 'application/json'}
	# set login data to dictionary
	userId = event.source.user_id
	if userId not in userDic or event.message.text != WatsonInfo.RESETWORD:
		userDic[userId] = {}
		body = {"userId": WatsonInfo.COFFEEUSERID,"password": WatsonInfo.COFFEEPASSWORD}
		r = s.post(WatsonInfo.LOGINURL,data=json.dumps(body),headers=headers)
		result = json.loads(r.text)
		userDic[userId] = result['context']
	body = { 'context' : userDic[userId], 'input' : { 'text' : event.message.text }}
	r = s.post(WatsonInfo.MESSAGEURL,data=json.dumps(body),headers=headers)
	result = json.loads(r.text)
	print(result)
	userDic[userId] = result['context']
	try:
		output = result['output']
	except:
		output = {}
		print('no output')
	return output


def firstAction(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=text[1:])
	)




if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
