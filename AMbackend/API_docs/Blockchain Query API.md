Blockchain Query API

Plaintext query api to retrieve data from blockchain.com
Some API calls are available with CORS headers if you add a &cors=true parameter to the GET request
Please limit your queries to a maximum of 1 every 10 seconds. All bitcoin values are in Satoshi i.e. divide by 100000000 to get the amount in BTC
Real-time
getdifficulty - Current difficulty target as a decimal number
getblockcount - Current block height in the longest chain
latesthash - Hash of the latest block
bcperblock - Current block reward in BTC
totalbc - Total Bitcoins in circulation (delayed by up to 1 hour)
probability - Probability of finding a valid block each hash attempt
hashestowin - Average number of hash attempts needed to solve a block
nextretarget - Block height of the next difficulty re-target
avgtxsize - Average transaction size for the past 1000 blocks. Change the number of blocks by passing an integer as the second argument e.g. avgtxsize/2000
avgtxvalue - Average transaction value (1000 Default)
interval - Average time between blocks in seconds
eta - Estimated time until the next block (in seconds)
avgtxnumber - Average number of transactions per block (100 Default)
Real-time
To filter by x number of confirmations include the confirmations parameter
"e.g. /q/addressbalance/1EzwoHtiXB4iFwedPr49iywjZn2nnekhoj?confirmations=6"
To filter by x number of confirmations include the confirmations parameter
getreceivedbyaddress/$address - Get the total number of bitcoins received by an address (in satoshi). Multiple addresses separated by | Do not use to process payments without the confirmations parameter
Add the parameters start_time and end_time to restrict received by to a specific time period. Provided times should be a unix timestamp in milliseconds. Multiple addresses separated by |
getsentbyaddress/$address - Get the total number of bitcoins send by an address (in satoshi). Multiple addresses separated by | Do not use to process payments without the confirmations parameter
addressbalance/$address - Get the balance of an address (in satoshi). Multiple addresses separated by | Do not use to process payments without the confirmations parameter
addressfirstseen/$address - Timestamp of the block an address was first confirmed in.
Tools
addresstohash/$address - Converts a bitcoin address to a hash 160
hashtoaddress/$hash - Converts a hash 160 to a bitcoin address
hashpubkey/$pubkey - Converts a public key to a hash 160
addrpubkey/$pubkey - Converts a public key to an Address
pubkeyaddr/$address - Converts an address to public key (if available)
Transactions Lookups
txtotalbtcoutput/$txHash - Get total output value of a transaction (in satoshi)
txtotalbtcinput/$txHash - Get total input value of a transaction (in satoshi)
txfee/$txHash - Get fee included in a transaction (in satoshi)
txresult/$txHash/$address - Calculate the result of a transaction sent or received to Address. Multiple addresses separated by |
Misc
unconfirmedcount - Number of pending unconfirmed transactions
24hrprice - 24 hour weighted price from the largest exchanges
marketcap - USD market cap (based on 24 hour weighted price)
24hrtransactioncount - Number of transactions in the past 24 hours
24hrbtcsent - Number of btc sent in the last 24 hours (in satoshi)
hashrate - Estimated network hash rate in gigahash
rejected - Lookup the reason why the provided tx or block hash was rejected (if any)