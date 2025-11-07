Alternative API doc

Free Crypto API - Documentation
We are happy to announce that we are going to provide a new public API for coin and token prices after CoinMarketCap decided to discontinue their public API. If you were using the v1 or v2 endpoints until now, you can just switch to our endpoints without changing any other code. If you're interested in where the data of our data is coming from, check out our list of supported exchanges.

If you are looking for the Fear and Greed Index API, it can be found here.

Crypto API v2 End Points
Listings
Endpoint: /listings/
Method: GET
Description: Overview of all available crypto currencies, use the returned id to retrieve more data on a specific crypto currency on the ticker endpoint.
Example URL: https://api.alternative.me/v2/listings/
Example Response: /listings/
{
   "data": [
      {
         "id": "1",
         "name": "Bitcoin",
         "symbol": "BTC",
         "website_slug": "bitcoin"
      },
      {
         "id": "2",
         "name": "Litecoin",
         "symbol": "LTC",
         "website_slug": "litecoin"
      },
      ...
   ],
   "metadata": {
      "timestamp": 1537430627,
      "num_cryptocurrencies": 935,
      "error": null
   }
}
Ticker
Endpoint: /ticker/
Method: GET
Description: Coin and token prices updated every 5 minutes.
Optional Parameters:
limit, [int]: Limit the number of returned results. The default value is 100, use '0' for all available data.
start, [int]: Sets the first element to be fetched, all requests are ordered by the Marketcap. That means the order of the returned elements can change over time.
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
structure, [string]: sets the structure of the data field as either array or name-value pair style. Possible values are 'dictionary' for name-value pair style and 'array' for array style.
sort, [string]: returned results can be sorted by: 'id', 'rank' (means marketcap), 'volume_24h', 'percent_change_24h' default sorting is by rank. In addition it can be sorted by: 'price', 'percent_change_1h', 'percent_change_7d', 'circulating_supply' and 'name'.
Example URL: https://api.alternative.me/v2/ticker/
Example URL: https://api.alternative.me/v2/ticker/?limit=10
Example URL: https://api.alternative.me/v2/ticker/?start=5
Example URL: https://api.alternative.me/v2/ticker/?convert=EUR
Example URL: https://api.alternative.me/v2/ticker/?structure=array
Example URL: https://api.alternative.me/v2/ticker/?sort=percent_change_24h
Example Response: /ticker/?convert=EUR
{
   "data": [
      {
         "id": 1,
         "name": "Bitcoin",
         "symbol": "BTC",
         "website_slug": "bitcoin",
         "rank": 1,
         "circulating_supply": 17277612,
         "total_supply": 17277612,
         "max_supply": 21000000,
         "quotes": {
            "USD": {
               "price": 6418.85820382,
               "volume_24h": 4263700490.8,
               "market_cap": 110902541529,
               "percentage_change_1h": 0.1,
               "percentage_change_24h": 0.84,
               "percentage_change_7d": -0.23
            },
            "EUR": {
               "price": 5490.04942172725,
               "volume_24h": 3646743029.78124,
               "market_cap": 94854943769.7537,
               "percentage_change_1h": 0.1,
               "percentage_change_24h": 0.84,
               "percentage_change_7d": -0.23
            }
         },
         "last_updated": 1537428143
      },
      ...
   ],
   "metadata": {
      "timestamp": 1537428090,
      "num_cryptocurrencies": 935,
      "error": null
   }
}
Ticker for specific currency
Endpoint: /ticker/(id,name)
Method: GET
Description: Get ticker data of a specified coin by providing the 'id' or the 'website_slug' of the coin as can be found by calling listings endpoint.
Optional Parameters:
id, [int, string]: Identifier of a coin which can either be its 'id' or its 'website_slug'.
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
structure, [string]: sets the structure of the data field as either array or name-value pair style. Possible values are 'dictionary' for name-value pair style and 'array' for array style.
Example URL: https://api.alternative.me/v2/ticker/1/
Example URL: https://api.alternative.me/v2/ticker/bitcoin/
Example Response: /ticker/bitcoin/
{
   "data": {
      "1": {
         "id": 1,
         "name": "Bitcoin",
         "symbol": "BTC",
         "website_slug": "bitcoin",
         "rank": 1,
         "circulating_supply": 17277650,
         "total_supply": 17277650,
         "max_supply": 21000000,
         "quotes": {
            "USD": {
               "price": 6420.75294203,
               "volume_24h": 4234633625.35,
               "market_cap": 110935522069,
               "percentage_change_1h": 0.08,
               "percentage_change_24h": 0.89,
               "percentage_change_7d": -0.26
            }
         },
         "last_updated": 1537430662
      }
   },
   "metadata": {
      "timestamp": 1537430662,
      "num_cryptocurrencies": 935,
      "error": null
   }
}
Global
Endpoint: /global/
Method: GET
Description: Get global market information at a glance.
Optional Parameters:
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
Example URL: https://api.alternative.me/v2/global/
Example URL: https://api.alternative.me/v2/global/?convert=EUR
Example Response: /global/?convert=EUR
{
   "data": {
      "active_cryptocurrencies": 935,
      "active_markets": 15625,
      "bitcoin_percentage_of_market_cap": 55.38,
      "quotes": {
         "USD": {
            "total_market_cap": 199872021187,
            "total_volume_24h": 11884460489
         },
         "EUR": {
            "total_market_cap": 170690706093.698,
            "total_volume_24h": 10149329257.606
         }
      },
      "last_updated": 1537438163
   },
   "metadata": {
      "timestamp": 1537438413,
      "error": null
   }
}
Crypto API v1 End Points
Ticker
Endpoint: /ticker/
Method: GET
Description: Coin and token prices updated every 5 minutes.
Optional Parameters:
limit, [int]: Limit the number of returned results. The default value is 100.
start, [int]: Sets the first element to be fetched, all requests are ordered by the Marketcap. That means the order of the returned elements can change over time.
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
Example URL: https://api.alternative.me/v1/ticker/
Example URL: https://api.alternative.me/v1/ticker/?limit=10
Example URL: https://api.alternative.me/v1/ticker/?start=15&limit=10
Example URL: https://api.alternative.me/v1/ticker/?limit=10&convert=EUR
Example Response: /ticker/
[
   {
      "id": "bitcoin",
      "name": "Bitcoin",
      "symbol": "BTC",
      "rank": "1",
      "price_usd": "6420.1641675",
      "price_btc": "0",
      "24h_volume_usd": "4228877214.79",
      "market_cap_usd": "110925349429",
      "available_supply": "17277650",
      "total_supply": "17277650",
      "max_supply": "21000000",
      "percentage_change_1h": "0.06",
      "percentage_change_24h": "0.89",
      "percentage_change_7d": "-0.27",
      "last_updated": "1537431002"
   },
   ...
]
Ticker (Specific Currency)
Endpoint: /ticker/
Method: GET
Description: Coin and token prices updated every 5 minutes.
Optional Parameters:
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
Example URL: https://api.alternative.me/v1/ticker/bitcoin/
Example URL: https://api.alternative.me/v1/ticker/bitcoin/?convert=EUR
Example Response: /ticker/?convert=EUR
[
   {
      "id": "bitcoin",
      "name": "Bitcoin",
      "symbol": "BTC",
      "rank": "1",
      "price_usd": "6420.1641675",
      "price_btc": "0",
      "24h_volume_usd": "4228877214.79",
      "market_cap_usd": "110925349429",
      "available_supply": "17277650",
      "total_supply": "17277650",
      "max_supply": "21000000",
      "percentage_change_1h": "0.06",
      "percentage_change_24h": "0.89",
      "percentage_change_7d": "-0.27",
      "last_updated": "1537431002",
      "price_eur": "5486.03028112874",
      "24h_volume_eur": "3613575580.03805",
      "market_cap_eur": "94785711087.0803"
   }
]
Global
Endpoint: /global/
Method: GET
Description: Get global market information at a glance.
Optional Parameters:
convert, [string]: In addition to the USD values the converted values will be delivered in the requested currency. Possible fiat conversion target values are: ' USD', 'EUR', 'GBP', 'RUB', 'JPY', 'CAD', 'KRW', 'PLN' it is also possible to convert to other cryptocurrencies like: 'BTC', 'ETH', 'XRP', 'LTC' and 'BCH'.
Example URL: https://api.alternative.me/v1/global/
Example URL: https://api.alternative.me/v1/global/?convert=EUR
Example Response: /global/
{
   "total_market_cap_usd": 200499223404,
   "total_24h_volume_usd": 12188496453,
   "bitcoin_percentage_of_market_cap": 55.32,
   "active_currencies": 937,
   "active_assets": 0,
   "active_markets": 20,
   "last_updated": 1526989682
}
Additional Notes
Supported Exchanges
Binance
BitBay
Bitfinex
Bithumb
Bitstamp
Bittrex
Coinbase Pro
CoinEx
CoinExchange
Cryptopia
FCoin
HitBTC
Huobi
IDEX
Kraken
Kucoin
OKEx
Poloniex
YoBit
Zaif
There is a simple reason why we do not support hundereds of exchanges: Our selection of supported exchanges is hand picked in order to minimize the problem of fake volume. A lot of exchanges are reporting huge volumes while having a very small user base, which lead us to our decision of only supporting exchanges with a good amount of real, daily active users.

Misc
All 'last_updated' fields are unix timestamps.
Limits
Please respect our server capacities and avoid unnecessary requests, our endpoints will only update every 5 minutes anyway.
The limit is set to 60 requests per minute enforced over a 10 minute window. If you need a higher request budget please contact us at support@alternative.me.
Terms of Use (I)
By accessing the Public API, you agree to be bound by the Terms of Use.
Terms of Use (II)
You are free to use our API and data from our API in any way you like, this includes commercial projects of any kind. The free nature of this API will never change. However we may at any time change or discontinue the API.
We greatly appreciate a link to 'alternative.me', a 'Data from alternative.me' text note or other kinds of references to our project. However you are by no means obligated to do so.
The information provided on this website does not constitute investment advice, financial advice, trading advice, or any other sort of advice and you should not treat any of the website's content as such. Alternative.me does not recommend that any cryptocurrency should be bought, sold, or held by you. Do conduct your own due diligence and consult your financial advisor before making any investment decisions.