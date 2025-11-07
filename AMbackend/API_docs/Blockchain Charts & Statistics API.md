Blockchain Charts & Statistics API

The Blockchain Charts & Statistics API provides a simple interface to programmatically interact with the charts and statistics displayed on blockchain.info.
Preamble
Date parameters are represented as YYYY-MM-DDThh:mm:ss or YYYY-MM-DD. The timezone is UTC. Durations are represented by concatenating the number of time units and the time unit it represents (for example '1year', '3months', etc..). Available time units are: minute, hour, day, week and year.
Charts API
Get the data behind Blockchain's charts
This method can be used to get and manipulate data behind Blockchain.com's charts.
URL: https://api.blockchain.info/charts/$chartName?timespan=$timespan&rollingAverage=$rollingAverage&start=$start&format=$format&sampled=$sampled
Method: GET
Example: https://api.blockchain.info/charts/transactions-per-second?timespan=5weeks&rollingAverage=8hours&format=json
$timespan- Duration of the chart, default is 1 year for most charts, 1 week for mempool charts. (Optional)
$rollingAverage- Duration over which the data should be averaged. (Optional)
$start- Datetime at which to start the chart. (Optional)
$format- Either JSON or CSV, defaults to JSON. (Optional)
$sampled- Boolean set to 'true' or 'false' (default 'true'). If true, limits the number of datapoints returned to ~1.5k for performance reasons. (Optional)
Please note that values for charts can be represented in scientific notation (14,627,700 is represented as 1.46277E7)
Response: 200 OK, application/json
{
  "status": "ok",
  "name": "Confirmed Transactions Per Day",
  "unit": "Transactions",
  "period": "day",
  "description": "The number of daily confirmed Bitcoin transactions.",
  "values": [
    {
      "x": 1442534400,
      "y": 188330
    },
    "..."
  ]
}
Response: 200 OK, text/csv; charset=ascii
2015-09-18 00:00:00,188330.0
2015-09-19 00:00:00,117999.0
2015-09-20 00:00:00,105933.0
Stats API
Get the data behind Blockchain's stats
This method can be used to get and manipulate data behind Blockchain.com's https://api.blockchain.info/stats
URL: https://api.blockchain.info/stats
Method: GET
Example: https://api.blockchain.info/stats
Response: 200 OK, application/json
{
  "market_price_usd": 610.036975,
  "hash_rate": 1841098926.6292908,
  "total_fees_btc": 6073543165,
  "n_btc_mined": 205000000000,
  "n_tx": 233805,
  "n_blocks_mined": 164,
  "minutes_between_blocks": 8.2577,
  "totalbc": 1587622500000000,
  "n_blocks_total": 430098,
  "estimated_transaction_volume_usd": 123429768.68108143,
  "blocks_size": 117490685,
  "miners_revenue_usd": 1287626.6577490852,
  "nextretarget": 431423,
  "difficulty": 225832872179,
  "estimated_btc_sent": 20233161880242,
  "miners_revenue_btc": 2110,
  "total_btc_sent": 184646388663542,
  "trade_volume_btc": 21597.09997288,
  "trade_volume_usd": 13175029.536228297,
  "timestamp": 1474035340000
}
Pools API
translation(translations.poolsDesc)
This method can be used to get and manipulate data behind Blockchain.com's pools information.
URL: https://api.blockchain.info/pools?timespan=$timespan
Method: GET
Example: https://api.blockchain.info/pools?timespan=5days
$timespan- Duration over which the data is computed, maximum 10 days, default is 4 days. (Optional)
Response: 200 OK, application/json
{
  "GHash.IO": 7,
  "95.128.48.209": 1,
  "NiceHash Solo": 1,
  "Solo CKPool": 2,
  "1Hash": 11,
  "217.11.225.189": 1,
  "Unknown": 10,
  "BitClub Network": 23,
  "Telco 214": 5,
  "HaoBTC": 29,
  "GBMiners": 2,
  "SlushPool": 44,
  "91.220.131.39": 1,
  "Kano CKPool": 13,
  "BTCC Pool": 74,
  "60.205.107.55": 1,
  "BitMinter": 1,
  "BitFury": 58,
  "AntPool": 87,
  "F2Pool": 104,
  "ViaBTC": 54,
  "BW.COM": 77,
  "BTC.com": 2,
  "47.89.51.25": 1,
  "74.118.157.122": 2
}