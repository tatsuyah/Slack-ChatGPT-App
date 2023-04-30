import openai
import json
import re
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import functions_framework


HEADERS = {'Content-Type': 'application/json'}
SLACK_OAUTH_TOKEN = ""
SLACK_CHANNEL_ID = ""
OPENAI_API_KEY = ""
MODEL_NAME = "gpt-3.5-turbo-0301"
TEMPARATURE = 0.7
TOP_P = 1.0

client = WebClient(token=SLACK_OAUTH_TOKEN)  # Set OAuth Tokens for Your Workspace. Found in https://api.slack.com/apps/<slack-app-id>/oauth?
openai.api_key = OPENAI_API_KEY  

def postChatGPT(input_text):
  response = openai.ChatCompletion.create(
    model=MODEL_NAME,
    messages=input_text,
    temperature=TEMPARATURE,
    top_p=TOP_P)
  reply = response["choices"][0]["message"]["content"]
  return reply, "OK"
  
@functions_framework.http
def verify(param):
  if 'X-Slack-Retry-Num' in param.headers:
    return "", 200
  body = param.get_json()
  r = client.conversations_replies(
          channel=SLACK_CHANNEL_ID,
          latest=body['event']['ts'],
          ts=body['event']['ts'],
  )
  ts = body['event']['ts']
  if "thread_ts" in r["messages"][0]:  
    ts = r["messages"][0]["thread_ts"]
  
  replies = client.conversations_replies(
          channel=SLACK_CHANNEL_ID,
          ts=ts,
  )
  elms = create_formatted_history(replies)
  answer = postChatGPT(elms)
  try: 
    response = client.chat_postMessage(
        channel=SLACK_CHANNEL_ID, 
        text=answer[0],
        thread_ts=body['event']['ts']
    )
    return "", 200
  except SlackApiError as e:
    assert e.response["error"] 

def create_formatted_history(replies):
  messages = replies['messages']
  elms = []
  for msg in messages:
    elm = {}
    if 'client_msg_id' in msg:
      elm['role'] = 'user'
      msg_text = re.sub(r'^<@[^>]*>', '', msg['text'])
      elm['content'] = msg_text
    elif 'bot_id' in msg:
      elm['role'] = 'assistant'
      elm['content'] = msg['text']

    elms.append(elm)
  return elms
