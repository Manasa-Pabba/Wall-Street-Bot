import urllib
import json
import os

from flask import Flask
from flask import request
from flask import make_response
from predictStocks import predictStocks
from twitter_analyze import twitter_analyze

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    print r
    return r

def processRequest(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if req.get("result").get("action") == "CurrentPrice.price":   
        # data = json.loads(getStockCurrentPrice(req))
        res = makeWebhookResult(getStockCurrentPrice(req), req.get("result").get("action"), stock_symbol)
        return res
    elif req.get("result").get("action") == "Prediction.stockForecast":
        # data = json.loads(getStockPrediction(req))
        res = makeWebhookResult(getStockPrediction(req), req.get("result").get("action"), stock_symbol)
        return res 
    elif req.get("result").get("action") == "Feelings.analyze":
        # data = json.loads(getTwitterFeelings(req))
        res = makeWebhookResult(getTwitterFeelings(req), req.get("result").get("action"), stock_symbol)
        return res
    else:
        return {}

# analyze feelings intent
def getTwitterFeelings(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    twitter_analyzer = twitter_analyze()
    twitter_data = twitter_analyzer.analyze_feelings(stock_symbol)
    print 'Twitter data:'
    print twitter_data

    data = {}
    data['positive'] = twitter_data[0]
    data['negative'] = twitter_data[1]
    data['neutral'] = twitter_data[2]

    total = data['positive'] + data['negative'] + data['neutral']

    positive_percent = percentage(data['positive'], total)
    negative_percent = percentage(data['negative'], total)
    neutral_percent = percentage(data['neutral'], total)

    data_string = 'positive: ' + str(positive_percent) + '% negative: ' + str(negative_percent) + '% neutral: ' + str(neutral_percent) + '%'

    return data_string

# make percentage and round
def percentage(part, whole):
    return round(100 * float(part)/float(whole), 2)

# for intent prediction
def getStockPrediction(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    prediction = predictStocks()
    num_of_days = 3
    predicted_values = prediction.stocksRegression(stock_symbol, int(num_of_days))
    predicted_list = predicted_values.tolist()
    return ''.join(str(v) for v in predicted_list)

# intent current price
def getStockCurrentPrice(req):
    result = req.get("result")
    parameters = result.get("parameters")
    stock_symbol = parameters.get("stock_symbol")
    if stock_symbol is None:
        return None

    prediction = predictStocks()
    current_price = prediction.getCurrentPrice(stock_symbol)
    return str(current_price)

# return to API.AI
def makeWebhookResult(data, action, stock_symbol):
    if action == "CurrentPrice.price":
        speech = "Current Price for the stock is $" + str(data)
        next_speech = "Predict price for " + stock_symbol
        news_speech = "News for " + stock_symbol
        news_url = "http://finance.yahoo.com/quote/" + stock_symbol
        return {
            "speech": speech,
            "displayText": speech,
            "source": "apiai-wallstreetbot-webhook", 
            "data": {
                "facebook": {
                  "attachment": {
                    "type": "template",
                    "payload": {
                            "template_type":"button",
                            "text":speech,
                            "buttons":[
                              {
                                "type":"web_url",
                                "url":news_url,
                                "title":news_speech
                              },
                              {
                                "type":"postback",
                                "title":next_speech,
                                "payload":"USER_DEFINED_PAYLOAD"
                              }
                            ]
                        }
                     }
                }
            }
        }
         # "message":{
         #    "attachment":{
         #      "type":"template",
         #      "payload":{
         #        "template_type":"button",
         #        "text":"What do you want to do next?",
         #        "buttons":[
         #          {
         #            "type":"web_url",
         #            "url":"https://petersapparel.parseapp.com",
         #            "title":"Show Website"
         #          },
         #          {
         #            "type":"postback",
         #            "title":"Start Chatting",
         #            "payload":"USER_DEFINED_PAYLOAD"
         #          }
         #        ]
         #      }
         #    }
         #  }

    elif action == "Prediction.stockForecast":
        speech = "Predicted price for next few days: " + str(data)
    elif action == "Feelings.analyze":
        speech = "Feelings about stock: " + str(data)
    else:
        return {}

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        "source": "apiai-wallstreetbot-webhook"
    }

    # Image example
    # "data": {
    #     "facebook": {
    #       "attachment": {
    #         "type": "image",
    #         "payload": {
    #         "url": "https://www.testclan.com/images/testbot/siege/weapons/assault-rifles.jpg"
    #          }
    #         }
    #       }
    #     }

    

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
