import os, json, requests
from flask import Flask, request, abort, session

from linebot import (
	LineBotApi, WebhookParser
)
from linebot.exceptions import (
	InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage,
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
userURL = {}

class ServerInfo:
	URL = 'https://line-python-test.mybluemix.net/'
	IMAGEURL = URL + 'static/icons/'
	LOGOURL = URL + 'static/images/NHcoffee1-logoJs_brown.png'
	RESETWORD_STUB = u'こんにちは'
	RESETWORD_ERP = u'こんにちはERP'
	EXCEPTIONWORDS = ['確定']
	COFFEE = {
		'176': {
			'title': '日本橋ブレンドーカプセル(8個入り)' ,
			'price': '￥590' ,
			'image': IMAGEURL + '176.png',
			#'message': '「日本橋ブレンド(8個入)」が欲しい' 
			#'message': '「日本橋ブレンド ーカプセル (8個入り)」が欲しい' 
			'message': '「日本橋ブレンド」が欲しい' 
		},
		'182': {
			'title': 'One more THINKブレンドーカプセル(8個入り)' ,
			'price': '￥600' ,
			'image': IMAGEURL + '182.png', 
			'message': '「One more THINKブレンド」が欲しい'
		},
		'184': {
			'title': 'リラックスアロマーカプセル(8個入り)' ,
			'price': '￥800' ,
			'image': IMAGEURL + '184.png', 
			'message': '「リラックスアロマ」が欲しい'
		},
		'185': {
			'title': 'カプリスモカーカプセル(8個入り)' ,
			'price': '￥750' ,
			'image': IMAGEURL + '185.png', 
			#'message': '「カプリスモカ(8個入)」が欲しい'
			'message': '「カプリスモカ」が欲しい'
			#'message': '「カプリスモカ ーカプセル (8個入り)」が欲しい'
		},
		'186': {
			'title': 'マンデリンローストーカプセル(8個入り)' ,
			'price': '￥800' ,
			'image': IMAGEURL + '186.png',
			'message': '「マンデリンロースト」が欲しい'
		},
		'187': {
			'title': 'ブラウンサウンドーカプセル(8個入り)' ,
			'price': '￥600' ,
			'image': IMAGEURL + '187.png' ,
			#'message': '「ブラウンサウンド(8個入)」が欲しい'
			'message': '「ブラウンサウンド」が欲しい'
			#'message': '「ブラウンサウンド ーカプセル (8個入り)」が欲しい'
		},
		'188': {
			'title': 'コーヒークリーマー(40個入り)' ,
			'price': ' ' ,
			'image': IMAGEURL + '188.png', 
			'message': '「コーヒークリーマー」が欲しい'
		},
		'189': {
			'title': '日本橋ドリップペーパー(50枚入り)' ,
			'price': ' ' ,
			'image': IMAGEURL + '189.png', 
			'message': '「日本橋ドリップペーパー」が欲しい'
		},
		'201': {
			'title': '幕張ブレンドーカプセル(8個入り)' ,
			'price': ' ' ,
			'image': IMAGEURL + '201.png',
			'message': '「幕張ブレンドーカプセル」が欲しい'
		}
	}

#Parameters to get Watson Data
class WatsonInfo_ERP:
	URL = 'http://watson-erp-coffee.mybluemix.net/'
	LOGINURL = URL + 'api/login'
	MESSAGEURL = URL + 'api/message' 
	WATSONUSERID = 'coguser' 
	WATSONPASSWORD = 'watson!'
	COFFEEUSERID = 'C00011'
	COFFEEPASSWORD = 'XXXXXXXX'
class WatsonInfo_STUB:
	URL = 'http://erp-coffee-concierge.mybluemix.net/'
	LOGINURL = URL + 'api/login'
	MESSAGEURL = URL + 'api/message' 
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
	global userDic, userURL
	# set login data to dictionary
	output = ''
	for k in userDic.keys():
		output = '<br>' + k + ': ' + userURL[k].URL + output  
	return 'You are logged in:' + output
	
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
		if isinstance(event, MessageEvent):
			if isinstance(event.message, TextMessage):
				if event.message.text not in ServerInfo.EXCEPTIONWORDS: 
					execution(event, event.message.text)
			else:
				continue
		elif isinstance(event, PostbackEvent): 
			execution(event, event.postback.data)
		else:
			continue
	return 'OK'

def execution(event, text):
	output = callWatson(event, text)
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
	elif userDic[userId]['nextFrontAction'] == 'showYesNo_showIcon':
		showYesNo_showIcon(event, output)
	else:
		replyAction(event, output)

def callWatson(event, text):
	global userDic, userURL
	# set login data to dictionary
	userId = event.source.user_id
	print('start call watson')
	if text == ServerInfo.RESETWORD_STUB:
		userURL[userId] = WatsonInfo_STUB
	elif text == ServerInfo.RESETWORD_ERP:
		userURL[userId] = WatsonInfo_ERP
	elif userId not in userURL:
		userURL[userId] = WatsonInfo_STUB
	#Watson Authentications
	s = requests.Session()
	s.auth = (userURL[userId].WATSONUSERID, userURL[userId].WATSONPASSWORD)
	headers = { 'Content-Type': 'application/json'}
	if userId not in userDic or text == ServerInfo.RESETWORD_STUB or text == ServerInfo.RESETWORD_ERP:
		print('Reset user')
		userDic[userId] = {}
		body = {"userId": userURL[userId].COFFEEUSERID,"password": userURL[userId].COFFEEPASSWORD}
		r = s.post(userURL[userId].LOGINURL,data=json.dumps(body),headers=headers)
		result = json.loads(r.text)
		userDic[userId] = result['context']
	body = { 'context' : userDic[userId], 'input' : { 'text' : text }}
	r = s.post(userURL[userId].MESSAGEURL,data=json.dumps(body),headers=headers)
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
	#type_string = '人気のドリップ'
	type_string = ''

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
		alt_text='こんにちは',
		template=carousel_template)
	line_bot_api.reply_message(
		event.reply_token,
		ImageSendMessage(
			original_content_url=ServerInfo.LOGOURL,
			preview_image_url=ServerInfo.LOGOURL
		)
	)
	line_bot_api.push_message(
		userId,
		TextSendMessage(text=text)
	)
	line_bot_api.push_message(
		userId,
		TextSendMessage(text=u'日本橋珈琲 人気のドリップをご紹介します。')
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
	execution(event, 'resend')

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
		alt_text='確認',
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
	partNumber = userDic[userId]['proposeAlternative']['partNumber']
	buttons_template_message = TemplateSendMessage(
		alt_text='代替商品',
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
					label='3.類似商品含めてお届け',
					text='3.類似商品含めてお届け'
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
		alt_text='確定',
		template=ConfirmTemplate(
			text=text,
			actions=[
				PostbackTemplateAction(
					label='確定',
					text='確定',
					data='finalorder'
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
		alt_text='購入',
		template=ConfirmTemplate(
			text=text,
			actions=[
				MessageTemplateAction(
					label='購入する',
					text='購入する'
				),
				MessageTemplateAction(
					label='今回はやめる',
					text='今回はやめておく'
				)
			]
		)
	)
	line_bot_api.reply_message(
		event.reply_token,
		confirm_template_message
	)
def showYesNo_showIcon(event, output):
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
	if(partNumber):
		line_bot_api.push_message(
			userId,
			ImageSendMessage(
				original_content_url=ServerInfo.COFFEE[partNumber]['image'],
				preview_image_url=ServerInfo.COFFEE[partNumber]['image']
			)
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
