Binance General API Information

General API Information
The following base endpoints are available. Please use whichever works best for your setup:
https://api.binance.com
https://api-gcp.binance.com
https://api1.binance.com
https://api2.binance.com
https://api3.binance.com
https://api4.binance.com
The last 4 endpoints in the point above (api1-api4) should give better performance but have less stability.
Responses are in JSON by default. To receive responses in SBE, refer to the SBE FAQ page.
Data is returned in chronological order, unless noted otherwise.
Without startTime or endTime, returns the most recent items up to the limit.
With startTime, returns oldest items from startTime up to the limit.
With endTime, returns most recent items up to endTime and the limit.
With both, behaves like startTime but does not exceed endTime.
All time and timestamp related fields in the JSON responses are in milliseconds by default. To receive the information in microseconds, please add the header X-MBX-TIME-UNIT:MICROSECOND or X-MBX-TIME-UNIT:microsecond.
We support HMAC, RSA, and Ed25519 keys. For more information, please see API Key types.
Timestamp parameters (e.g. startTime, endTime, timestamp) can be passed in milliseconds or microseconds.
For APIs that only send public market data, please use the base endpoint https://data-api.binance.vision. Please refer to Market Data Only page.
If there are enums or terms you want clarification on, please see the SPOT Glossary for more information.
APIs have a timeout of 10 seconds when processing a request. If a response from the Matching Engine takes longer than this, the API responds with "Timeout waiting for response from backend server. Send status unknown; execution status unknown." (-1007 TIMEOUT)
This does not always mean that the request failed in the Matching Engine.
If the status of the request has not appeared in User Data Stream, please perform an API query for its status.


HTTP Return Codes
HTTP 4XX return codes are used for malformed requests; the issue is on the sender's side.
HTTP 403 return code is used when the WAF Limit (Web Application Firewall) has been violated.
HTTP 409 return code is used when a cancelReplace order partially succeeds. (i.e. if the cancellation of the order fails but the new order placement succeeds.)
HTTP 429 return code is used when breaking a request rate limit.
HTTP 418 return code is used when an IP has been auto-banned for continuing to send requests after receiving 429 codes.
HTTP 5XX return codes are used for internal errors; the issue is on Binance's side. It is important to NOT treat this as a failure operation; the execution status is UNKNOWN and could have been a success.


General Information on Endpoints
For GET endpoints, parameters must be sent as a query string.
For POST, PUT, and DELETE endpoints, the parameters may be sent as a query string or in the request body with content type application/x-www-form-urlencoded. You may mix parameters between both the query string and request body if you wish to do so.
Parameters may be sent in any order.
If a parameter sent in both the query string and request body, the query string parameter will be used.


LIMITS
General Info on Limits​
The following intervalLetter values for headers:
SECOND => S
MINUTE => M
HOUR => H
DAY => D
intervalNum describes the amount of the interval. For example, intervalNum 5 with intervalLetter M means "Every 5 minutes".
The /api/v3/exchangeInfo rateLimits array contains objects related to the exchange's RAW_REQUESTS, REQUEST_WEIGHT, and ORDERS rate limits. These are further defined in the ENUM definitions section under Rate limiters (rateLimitType).
Requests fail with HTTP status code 429 when you exceed the request rate limit.
IP Limits​
Every request will contain X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter) in the response headers which has the current used weight for the IP for all request rate limiters defined.
Each route has a weight which determines for the number of requests each endpoint counts for. Heavier endpoints and endpoints that do operations on multiple symbols will have a heavier weight.
When a 429 is received, it's your obligation as an API to back off and not spam the API.
Repeatedly violating rate limits and/or failing to back off after receiving 429s will result in an automated IP ban (HTTP status 418).
IP bans are tracked and scale in duration for repeat offenders, from 2 minutes to 3 days.
A Retry-After header is sent with a 418 or 429 responses and will give the number of seconds required to wait, in the case of a 429, to prevent a ban, or, in the case of a 418, until the ban is over.
The limits on the API are based on the IPs, not the API keys.
Unfilled Order Count​
Every successful order response will contain a X-MBX-ORDER-COUNT-(intervalNum)(intervalLetter) header indicating how many orders you have placed for that interval.

To monitor this, refer to GET api/v3/rateLimit/order.
Rejected/unsuccessful orders are not guaranteed to have X-MBX-ORDER-COUNT-** headers in the response.
If you have exceeded this, you will receive a 429 error without the Retry-After header.
Please note that if your orders are consistently filled by trades, you can continuously place orders on the API. For more information, please see Spot Unfilled Order Count Rules.
The number of unfilled orders is tracked for each account.


Data Sources
The API system is asynchronous, so some delay in the response is normal and expected.
Each endpoint has a data source indicating where the data is being retrieved, and thus which endpoints have the most up-to-date response.
These are the three sources, ordered by least to most potential for delays in data updates.

Matching Engine - the data is from the Matching Engine
Memory - the data is from a server's local or external memory
Database - the data is taken directly from a database
Some endpoints can have more than 1 data source. (e.g. Memory => Database) This means that the endpoint will check the first Data Source, and if it cannot find the value it's looking for it will check the next one.


Request Security
Each method has a security type indicating required API key permissions, shown next to the method name (e.g., New order (TRADE)).
If unspecified, the security type is NONE.
Methods with a security type other than NONE are considered SIGNED requests (i.e. requires parameter signature). A few legacy listenKey management endpoints are an exception to this rule.
Secure methods require a valid API key to be specified and authenticated.
API keys can be created on the API Management page of your Binance account.
Both API key and secret key are sensitive. Never share them with anyone. If you notice unusual activity in your account, immediately revoke all the keys and contact Binance support.
API keys can be configured to allow access only to certain types of secure methods.
For example, you can have an API key with TRADE permission for trading, while using a separate API key with USER_DATA permission to monitor your order status.
By default, an API key cannot TRADE. You need to enable trading in API Management first.
Security type	Description
NONE	Public market data
TRADE	Trading on the exchange, placing and canceling orders
USER_DATA	Private account information, such as order status and your trading history
USER_STREAM	Managing User Data Stream subscriptions
SIGNED Endpoint security​
SIGNED endpoints require an additional parameter, signature, to be sent in the query string or request body.
The signature is not case sensitive.
Please consult the examples below on how to compute signature, depending on which API key type you are using.

Timing security​
SIGNED requests also require a timestamp parameter which should be the current timestamp either in milliseconds or microseconds. (See General API Information)
An additional optional parameter, recvWindow, specifies for how long the request stays valid and may only be specified in milliseconds.
recvWindow supports up to three decimal places of precision (e.g., 6000.346) so that microseconds may be specified.
If recvWindow is not sent, it defaults to 5000 milliseconds.
Maximum recvWindow is 60000 milliseconds.
Request processing logic is as follows:
serverTime = getCurrentTime()
if (timestamp < (serverTime + 1 second) && (serverTime - timestamp) <= recvWindow) {
  // begin processing request
  serverTime = getCurrentTime()
  if (serverTime - timestamp) <= recvWindow {
    // forward request to Matching Engine
  } else {
    // reject request
  }
  // finish processing request
} else {
  // reject request
}

Serious trading is about timing. Networks can be unstable and unreliable, which can lead to requests taking varying amounts of time to reach the servers. With recvWindow, you can specify that the request must be processed within a certain number of milliseconds or be rejected by the server.

It is recommended to use a small recvWindow of 5000 or less! The max cannot go beyond 60,000!

SIGNED Endpoint Examples for POST /api/v3/order​
HMAC Keys​
Here is a step-by-step example of how to send a valid signed payload from the Linux command line using echo, openssl, and curl.

Key	Value
apiKey	vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A
secretKey	NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j
Parameter	Value
symbol	LTCBTC
side	BUY
type	LIMIT
timeInForce	GTC
quantity	1
price	0.1
recvWindow	5000
timestamp	1499827319559
Example 1: As a request body

requestBody: symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559

HMAC SHA256 signature:

[linux]$ echo -n "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559" | openssl dgst -sha256 -hmac "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
(stdin)= c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71


curl command:

(HMAC SHA256)
[linux]$ curl -H "X-MBX-APIKEY: vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A" -X POST 'https://api.binance.com/api/v3/order' -d 'symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559&signature=c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71'


Example 2: As a query string

queryString: symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559

HMAC SHA256 signature:

[linux]$ echo -n "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559" | openssl dgst -sha256 -hmac "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
(stdin)= c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71


curl command:

(HMAC SHA256)
[linux]$ curl -H "X-MBX-APIKEY: vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A" -X POST 'https://api.binance.com/api/v3/order?symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559&signature=c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71'


Example 3: Mixed query string and request body

queryString: symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC

requestBody: quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559

HMAC SHA256 signature:

[linux]$ echo -n "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTCquantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559" | openssl dgst -sha256 -hmac "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
(stdin)= 0fd168b8ddb4876a0358a8d14d0c9f3da0e9b20c5d52b2a00fcf7d1c602f9a77


curl command:

(HMAC SHA256)
[linux]$ curl -H "X-MBX-APIKEY: vmPUZE6mv9SD5VNHk4HlWFsOr6aKE2zvsw0MuIgwCIPy6utIco14y7Ju91duEh8A" -X POST 'https://api.binance.com/api/v3/order?symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC' -d 'quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559&signature=0fd168b8ddb4876a0358a8d14d0c9f3da0e9b20c5d52b2a00fcf7d1c602f9a77'


Note that the signature is different in example 3. There is no & between "GTC" and "quantity=1".

RSA Keys​
This will be a step by step process how to create the signature payload to send a valid signed payload.

We support PKCS#8 currently.

To get your API key, you need to upload your RSA Public Key to your account and a corresponding API key will be provided for you.

For this example, the private key will be referenced as ./test-prv-key.pem

Key	Value
apiKey	CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ
Parameter	Value
symbol	BTCUSDT
side	SELL
type	LIMIT
timeInForce	GTC
quantity	1
price	0.2
timestamp	1668481559918
recvWindow	5000
Step 1: Construct the payload

Arrange the list of parameters into a string. Separate each parameter with a &.

For the parameters above, the signature payload would look like this:

symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2&timestamp=1668481559918&recvWindow=5000


Step 2: Compute the signature:

Encode signature payload as ASCII data.
Sign payload using RSASSA-PKCS1-v1_5 algorithm with SHA-256 hash function.
$ echo -n 'symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2&timestamp=1668481559918&recvWindow=5000' | openssl dgst -sha256 -sign ./test-prv-key.pem


Encode output as base64 string.
$  echo -n 'symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2&timestamp=1668481559918&recvWindow=5000' | openssl dgst -sha256 -sign ./test-prv-key.pem | openssl enc -base64 -A
HZ8HOjiJ1s/igS9JA+n7+7Ti/ihtkRF5BIWcPIEluJP6tlbFM/Bf44LfZka/iemtahZAZzcO9TnI5uaXh3++lrqtNonCwp6/245UFWkiW1elpgtVAmJPbogcAv6rSlokztAfWk296ZJXzRDYAtzGH0gq7CgSJKfH+XxaCmR0WcvlKjNQnp12/eKXJYO4tDap8UCBLuyxDnR7oJKLHQHJLP0r0EAVOOSIbrFang/1WOq+Jaq4Efc4XpnTgnwlBbWTmhWDR1pvS9iVEzcSYLHT/fNnMRxFc7u+j3qI//5yuGuu14KR0MuQKKCSpViieD+fIti46sxPTsjSemoUKp0oXA==


Since the signature may contain / and =, this could cause issues with sending the request. So the signature has to be URL encoded.
HZ8HOjiJ1s%2FigS9JA%2Bn7%2B7Ti%2FihtkRF5BIWcPIEluJP6tlbFM%2FBf44LfZka%2FiemtahZAZzcO9TnI5uaXh3%2B%2BlrqtNonCwp6%2F245UFWkiW1elpgtVAmJPbogcAv6rSlokztAfWk296ZJXzRDYAtzGH0gq7CgSJKfH%2BXxaCmR0WcvlKjNQnp12%2FeKXJYO4tDap8UCBLuyxDnR7oJKLHQHJLP0r0EAVOOSIbrFang%2F1WOq%2BJaq4Efc4XpnTgnwlBbWTmhWDR1pvS9iVEzcSYLHT%2FfNnMRxFc7u%2Bj3qI%2F%2F5yuGuu14KR0MuQKKCSpViieD%2BfIti46sxPTsjSemoUKp0oXA%3D%3D


The curl command:
curl -H "X-MBX-APIKEY: CAvIjXy3F44yW6Pou5k8Dy1swsYDWJZLeoK2r8G4cFDnE9nosRppc2eKc1T8TRTQ" -X POST 'https://api.binance.com/api/v3/order?symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2&timestamp=1668481559918&recvWindow=5000&signature=HZ8HOjiJ1s%2FigS9JA%2Bn7%2B7Ti%2FihtkRF5BIWcPIEluJP6tlbFM%2FBf44LfZka%2FiemtahZAZzcO9TnI5uaXh3%2B%2BlrqtNonCwp6%2F245UFWkiW1elpgtVAmJPbogcAv6rSlokztAfWk296ZJXzRDYAtzGH0gq7CgSJKfH%2BXxaCmR0WcvlKjNQnp12%2FeKXJYO4tDap8UCBLuyxDnR7oJKLHQHJLP0r0EAVOOSIbrFang%2F1WOq%2BJaq4Efc4XpnTgnwlBbWTmhWDR1pvS9iVEzcSYLHT%2FfNnMRxFc7u%2Bj3qI%2F%2F5yuGuu14KR0MuQKKCSpViieD%2BfIti46sxPTsjSemoUKp0oXA%3D%3D'


A sample Bash script below does the similar steps said above.

API_KEY="put your own API Key here"
PRIVATE_KEY_PATH="test-prv-key.pem"
# Set up the request:
API_METHOD="POST"
API_CALL="api/v3/order"
API_PARAMS="symbol=BTCUSDT&side=SELL&type=LIMIT&timeInForce=GTC&quantity=1&price=0.2"
# Sign the request:
timestamp=$(date +%s000)
api_params_with_timestamp="$API_PARAMS&timestamp=$timestamp"
signature=$(echo -n "$api_params_with_timestamp" \
            | openssl dgst -sha256 -sign "$PRIVATE_KEY_PATH" \
            | openssl enc -base64 -A)
# Send the request:
curl -H "X-MBX-APIKEY: $API_KEY" -X "$API_METHOD" \
    "https://api.binance.com/$API_CALL?$api_params_with_timestamp" \
    --data-urlencode "signature=$signature"

Ed25519 Keys​
Note: It is highly recommended to use Ed25519 API keys as it should provide the best performance and security out of all supported key types.

Parameter	Value
symbol	BTCUSDT
side	SELL
type	LIMIT
timeInForce	GTC
quantity	1
price	0.2
timestamp	1668481559918
This is a sample code in Python to show how to sign the payload with an Ed25519 key.

#!/usr/bin/env python3

import base64
import requests
import time
from cryptography.hazmat.primitives.serialization import load_pem_private_key

# Set up authentication
API_KEY='put your own API Key here'
PRIVATE_KEY_PATH='test-prv-key.pem'

# Load the private key.
# In this example the key is expected to be stored without encryption,
# but we recommend using a strong password for improved security.
with open(PRIVATE_KEY_PATH, 'rb') as f:
    private_key = load_pem_private_key(data=f.read(),
                                       password=None)

# Set up the request parameters
params = {
    'symbol':       'BTCUSDT',
    'side':         'SELL',
    'type':         'LIMIT',
    'timeInForce':  'GTC',
    'quantity':     '1.0000000',
    'price':        '0.20',
}

# Timestamp the request
timestamp = int(time.time() * 1000) # UNIX timestamp in milliseconds
params['timestamp'] = timestamp

# Sign the request
payload = '&'.join([f'{param}={value}' for param, value in params.items()])
signature = base64.b64encode(private_key.sign(payload.encode('ASCII')))
params['signature'] = signature

# Send the request
headers = {
    'X-MBX-APIKEY': API_KEY,
}
response = requests.post(
    'https://api.binance.com/api/v3/order',
    headers=headers,
    data=params,
)
print(response.json())




General endpoints
Test connectivity​
GET /api/v3/ping

Test connectivity to the Rest API.

Weight: 1

Parameters: NONE

Data Source: Memory

Response:

{}

Check server time​
GET /api/v3/time

Test connectivity to the Rest API and get the current server time.

Weight: 1

Parameters: NONE

Data Source: Memory

Response:

{
  "serverTime": 1499827319559
}


Exchange information​
GET /api/v3/exchangeInfo

Current exchange trading rules and symbol information

Weight: 20

Parameters:

Name	Type	Mandatory	Description
symbol	STRING	No	Example: curl -X GET "https://api.binance.com/api/v3/exchangeInfo?symbol=BNBBTC"
symbols	ARRAY OF STRING	No	Examples: curl -X GET "https://api.binance.com/api/v3/exchangeInfo?symbols=%5B%22BNBBTC%22,%22BTCUSDT%22%5D"
or
curl -g -X GET 'https://api.binance.com/api/v3/exchangeInfo?symbols=["BTCUSDT","BNBBTC"]'
permissions	ENUM	No	Examples: curl -X GET "https://api.binance.com/api/v3/exchangeInfo?permissions=SPOT"
or
curl -X GET "https://api.binance.com/api/v3/exchangeInfo?permissions=%5B%22MARGIN%22%2C%22LEVERAGED%22%5D"
or
curl -g -X GET 'https://api.binance.com/api/v3/exchangeInfo?permissions=["MARGIN","LEVERAGED"]'
showPermissionSets	BOOLEAN	No	Controls whether the content of the permissionSets field is populated or not. Defaults to true
symbolStatus	ENUM	No	Filters for symbols that have this tradingStatus. Valid values: TRADING, HALT, BREAK
Cannot be used in combination with symbols or symbol.
Notes:

If the value provided to symbol or symbols do not exist, the endpoint will throw an error saying the symbol is invalid.
All parameters are optional.
permissions can support single or multiple values (e.g. SPOT, ["MARGIN","LEVERAGED"]). This cannot be used in combination with symbol or symbols.
If permissions parameter not provided, all symbols that have either SPOT, MARGIN, or LEVERAGED permission will be exposed.
To display symbols with any permission you need to specify them explicitly in permissions: (e.g. ["SPOT","MARGIN",...].). See Account and Symbol Permissions for the full list.

Examples of Symbol Permissions Interpretation from the Response:

[["A","B"]] means you may place an order if your account has either permission "A" or permission "B".
[["A"],["B"]] means you can place an order if your account has permission "A" and permission "B".
[["A"],["B","C"]] means you can place an order if your account has permission "A" and permission "B" or permission "C". (Inclusive or is applied here, not exclusive or, so your account may have both permission "B" and permission "C".)
Data Source: Memory

Response:

{
  "timezone": "UTC",
  "serverTime": 1565246363776,
  "rateLimits": [
    {
      // These are defined in the `ENUM definitions` section under `Rate Limiters (rateLimitType)`.
      // All limits are optional
    }
  ],
  "exchangeFilters": [
    // These are the defined filters in the `Filters` section.
    // All filters are optional.
  ],
  "symbols": [
    {
      "symbol": "ETHBTC",
      "status": "TRADING",
      "baseAsset": "ETH",
      "baseAssetPrecision": 8,
      "quoteAsset": "BTC",
      "quotePrecision": 8, // will be removed in future api versions (v4+)
      "quoteAssetPrecision": 8,
      "baseCommissionPrecision": 8,
      "quoteCommissionPrecision": 8,
      "orderTypes": [
        "LIMIT",
        "LIMIT_MAKER",
        "MARKET",
        "STOP_LOSS",
        "STOP_LOSS_LIMIT",
        "TAKE_PROFIT",
        "TAKE_PROFIT_LIMIT"
      ],
      "icebergAllowed": true,
      "ocoAllowed": true,
      "otoAllowed": true,
      "quoteOrderQtyMarketAllowed": true,
      "allowTrailingStop": false,
      "cancelReplaceAllowed":false,
      "amendAllowed":false,
      "pegInstructionsAllowed": true,
      "isSpotTradingAllowed": true,
      "isMarginTradingAllowed": true,
      "filters": [
        // These are defined in the Filters section.
        // All filters are optional
      ],
      "permissions": [],
      "permissionSets": [
        [
          "SPOT",
          "MARGIN"
        ]
      ],
      "defaultSelfTradePreventionMode": "NONE",
      "allowedSelfTradePreventionModes": [
        "NONE"
      ]
    }
  ],
  // Optional field. Present only when SOR is available.
  // https://github.com/binance/binance-spot-api-docs/blob/master/faqs/sor_faq.md
  "sors": [
    {
      "baseAsset": "BTC",
      "symbols": [
        "BTCUSDT",
        "BTCUSDC"
      ]
    }
  ]
}




