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

class ServerInfo:
	URL = 'https://line-python-test.mybluemix.net/'
	IMAGEURL = URL + 'static/icons/'
	COFFEE = {
		'176': {
			'title': '日本橋ブレンドカプセル(8個入)' ,
			'price': '￥590' ,
			'image': IMAGEURL + '176.png',
			#'message': '「日本橋ブレンド(8個入)」が欲しい' 
			'message': '「日本橋ブレンド ーカプセル (8個入り)」が欲しい' 
			#'message': '「日本橋ブレンド」が欲しい' 
		},
		'182': {
			'title': 'One more THINKブレンド' ,
			'price': '￥600' ,
			'image': IMAGEURL + '182.png', 
			'message': '「One more THINKブレンド」が欲しい'
		},
		'184': {
			'title': 'リラックスアロマ' ,
			'price': '￥800' ,
			'image': IMAGEURL + '184.png', 
			'message': '「リラックスアロマ」が欲しい'
		},
		'185': {
			'title': 'カプリスモカカプセル(8個入)' ,
			'price': '￥750' ,
			'image': IMAGEURL + '185.png', 
			#'message': '「カプリスモカ(8個入)」が欲しい'
			#'message': '「カプリスモカ」が欲しい'
			'message': '「カプリスモカ ーカプセル (8個入り)」が欲しい'
		},
		'186': {
			'title': 'マンデリンロースト' ,
			'price': '￥800' ,
			'image': IMAGEURL + '186.png',
			'message': '「マンデリンロースト」が欲しい'
		},
		'187': {
			'title': 'ブラウンサウンドカプセル(8個入)' ,
			'price': '￥600' ,
			'image': IMAGEURL + '187.png' ,
			#'message': '「ブラウンサウンド(8個入)」が欲しい'
			#'message': '「ブラウンサウンド」が欲しい'
			'message': '「ブラウンサウンド ーカプセル (8個入り)」が欲しい'
		},
		'188': {
			'title': 'コーヒークリーマー' ,
			'price': ' ' ,
			'image': IMAGEURL + '188.png', 
			'message': '「コーヒークリーマー」が欲しい'
		},
		'189': {
			'title': '日本橋ドリップペーパー' ,
			'price': ' ' ,
			'image': IMAGEURL + '189.png', 
			'message': '「日本橋ドリップペーパー」が欲しい'
		},
		'201': {
			'title': 'Other' ,
			'price': ' ' ,
			'image': IMAGEURL + '201.png',
			'message': '「Other」が欲しい'
		}
	}

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
	print(ServerInfo.COFFEE['185']['image'])

	label=u'購入する'
	text=ServerInfo.COFFEE['184']['title'] + u'が欲しい'
	print(label)
	print(text)
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
		execution(event)
	return 'OK'

def execution(event):
	output = callWatson(event)
	userId = event.source.user_id
	if userDic[userId]['nextFrontAction'] == 'firstAction':
		firstAction(event, output)
	elif userDic[userId]['nextFrontAction'] == 'showYesNo':
		showYesNo(event, output)
	elif userDic[userId]['nextFrontAction'] == 'resendMessage':
		resendMessage(event, output)
	elif userDic[userId]['nextFrontAction'] == 'showIcon':
		showIcon(event, output)
	elif userDic[userId]['nextFrontAction'] == 'showCrossCellOption':
		showCrossCellOption(event, output)
	elif userDic[userId]['nextFrontAction'] == 'showConfirmButton':
		showConfirmButton(event, output)
	else:
		replyAction(event, output)

def callWatson(event):
	global userDic
	print('start call watson')
	#Watson Authentications
	s = requests.Session()
	s.auth = (WatsonInfo.WATSONUSERID, WatsonInfo.WATSONPASSWORD)
	headers = { 'Content-Type': 'application/json'}
	# set login data to dictionary
	userId = event.source.user_id
	if userId not in userDic or event.message.text == WatsonInfo.RESETWORD:
		print('Reset user')
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
	text = text[1:].replace('<br>','\n')
	type_string = '人気のドリップ'

	carousel_template = CarouselTemplate(columns=[
		CarouselColumn(
			thumbnail_image_url=ServerInfo.COFFEE['185']['image'],
			text=ServerInfo.COFFEE['185']['price'], 
			title=ServerInfo.COFFEE['185']['title'], 
			actions=[
			MessageTemplateAction(label=u'購入する', text=type_string + ServerInfo.COFFEE['185']['message'])
		]),
		CarouselColumn(
			thumbnail_image_url=ServerInfo.COFFEE['187']['image'],
			text=ServerInfo.COFFEE['187']['price'], 
			title=ServerInfo.COFFEE['187']['title'], 
			actions=[
			MessageTemplateAction(label=u'購入する', text=type_string + ServerInfo.COFFEE['187']['message'])
		]),
		CarouselColumn(
			thumbnail_image_url=ServerInfo.COFFEE['176']['image'],
			text=ServerInfo.COFFEE['176']['price'], 
			title=ServerInfo.COFFEE['176']['title'], 
			actions=[
			MessageTemplateAction(label=u'購入する', text=type_string + ServerInfo.COFFEE['176']['message'])
		])
	])
	template_message = TemplateSendMessage(
		alt_text='Buttons alt text', template=carousel_template)
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=text)
	)
	line_bot_api.push_message(
		userId,
		TextSendMessage(text=u'日本橋珈琲 人気のドリップ')
	)

	line_bot_api.push_message(
		userId,
		template_message
	)

def resendMessage(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	line_bot_api.push_message(
		userId,
		TextSendMessage(text=text)
	)
	event.message.text = 'resend'
	execution(event)

def showYesNo(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	confirm_template_message = TemplateSendMessage(
		alt_text='Confirm template',
		template=ConfirmTemplate(
			text=text,
			actions=[
				MessageTemplateAction(
					label='はい',
					text='はい'
				),
				MessageTemplateAction(
					label='いいえ',
					text='いいえ'
				)
			]
		)
	)
	line_bot_api.push_message(
		userId,
		confirm_template_message
	)
	
def showIcon(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=text)
	)
	partNumber = userDic[userId]['order']['item0']['partNumber']
	buttons_template_message = TemplateSendMessage(
		alt_text='Buttons template',
		template=ButtonsTemplate(
			thumbnail_image_url=ServerInfo.COFFEE[partNumber]['image'],
			text=ServerInfo.COFFEE[partNumber]['price'], 
			title=ServerInfo.COFFEE[partNumber]['title'], 
			actions=[
				MessageTemplateAction(
					label='1.在庫分のみお届け',
					text='1.在庫分のみお届け'
				),
				MessageTemplateAction(
					label='2.2回に分けてお届け',
					text='2.2回に分けてお届け'
				),
				MessageTemplateAction(
					label='3.類似商品含め配達可能数をお届け',
					text='3.類似商品含め配達可能数をお届け'
				)
			]
		)
	)
	line_bot_api.push_message(
		userId,
		buttons_template_message
	)
def showConfirmButton(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	confirm_template_message = TemplateSendMessage(
		alt_text='Confirm template',
		template=ConfirmTemplate(
			text=text,
			actions=[
				MessageTemplateAction(
					label='確定',
					text='finalorder'
				),
				MessageTemplateAction(
					label='キャンセル',
					text='キャンセル'
				)
			]
		)
	)
	line_bot_api.reply_message(
		event.reply_token,
		confirm_template_message
	)

def showCrossCellOption(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	confirm_template_message = TemplateSendMessage(
		alt_text='Confirm template',
		template=ConfirmTemplate(
			text=text,
			actions=[
				MessageTemplateAction(
					label='購入する',
					text='購入する'
				),
				MessageTemplateAction(
					label='今回はやめておく',
					text='今回はやめておく'
				)
			]
		)
	)
	line_bot_api.reply_message(
		event.reply_token,
		confirm_template_message
	)
def replyAction(event, output):
	global userDic
	userId = event.source.user_id
	text = ''
	print(output)
	if 'text' in output:
		for x in output['text']:
			text = text + '\n' + x
	text = text[1:].replace('<br>','\n')
	line_bot_api.reply_message(
		event.reply_token,
		TextSendMessage(text=text)
	)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)
