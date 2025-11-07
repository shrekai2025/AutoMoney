FRED observations API

fred/series/observations

Description
Examples
XML
JSON
Parameters
api_key
file_type
series_id
realtime_start
realtime_end
limit
offset
sort_order
observation_start
observation_end
units
frequency
aggregation_method
output_type
vintage_dates
Description
Get the observations or data values for an economic data series.

Examples
This request can return either XML, JSON, Excel Spreadsheet, or a zipped CSV by setting the file_type parameter to xml, json, xlsx, or csv. Note that the default value of file_type is xml. The API key 'abcdefghijklmnopqrstuvwxyz123456' is for demonstration purposes only. Use a registered API key instead.

XML
Request (HTTPS GET)
https://api.stlouisfed.org/fred/series/observations?series_id=GNPCA&api_key=abcdefghijklmnopqrstuvwxyz123456
Response

<observations realtime_start="2013-08-14" realtime_end="2013-08-14" observation_start="1776-07-04" observation_end="9999-12-31" units="lin" output_type="1" file_type="xml" order_by="observation_date" sort_order="asc" count="84" offset="0" limit="100000">
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="1929-01-01" value="1065.9"/>
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="1930-01-01" value="975.5"/>
    ...
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="2009-01-01" value="14565.1"/>
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="2010-01-01" value="14966.5"/>
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="2011-01-01" value="15286.7"/>
    <observation realtime_start="2013-08-14" realtime_end="2013-08-14" date="2012-01-01" value="15693.1"/>
</observations>

JSON
Request (HTTPS GET)
https://api.stlouisfed.org/fred/series/observations?series_id=GNPCA&api_key=abcdefghijklmnopqrstuvwxyz123456&file_type=json
Response

{
    "realtime_start": "2013-08-14",
    "realtime_end": "2013-08-14",
    "observation_start": "1776-07-04",
    "observation_end": "9999-12-31",
    "units": "lin",
    "output_type": 1,
    "file_type": "json",
    "order_by": "observation_date",
    "sort_order": "asc",
    "count": 84,
    "offset": 0,
    "limit": 100000,
    "observations": [
        {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "date": "1929-01-01",
            "value": "1065.9"
        },
        {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "date": "1930-01-01",
            "value": "975.5"
        },
        {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "date": "1931-01-01",
            "value": "912.1"
        },
        ...
        {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "date": "2011-01-01",
            "value": "15286.7"
        },
        {
            "realtime_start": "2013-08-14",
            "realtime_end": "2013-08-14",
            "date": "2012-01-01",
            "value": "15693.1"
        }
    ]
}

Parameters
api_key
Read API Keys for more information.

32 character alpha-numeric lowercase string, required
file_type
A key or file extension that indicates the type of file to send.

string, optional, default: xml
One of the following values: 'xml', 'json', 'xlsx', 'csv'
xml = Extensible Markup Language
json = JavaScript Object Notation
xlsx = Excel Spreadsheet
csv = Comma-Separated Values Text Format (File is returned as compressed zip file. The zip file contains the specified file format csv and a text README file.)

series_id
The id for a series.

string, required
realtime_start
The start of the real-time period. For more information, see Real-Time Periods, vintage_dates.

YYYY-MM-DD formatted string, optional, default: today's date
realtime_end
The end of the real-time period. For more information, see Real-Time Periods, vintage_dates.

YYYY-MM-DD formatted string, optional, default: today's date
limit
The maximum number of results to return.

integer between 1 and 100000, optional, default: 100000
offset
non-negative integer, optional, default: 0
sort_order
Sort results is ascending or descending observation_date order.

One of the following strings: 'asc', 'desc'.
optional, default: asc
observation_start
The start of the observation period.

YYYY-MM-DD formatted string, optional, default: 1776-07-04 (earliest available)
observation_end
The end of the observation period.

YYYY-MM-DD formatted string, optional, default: 9999-12-31 (latest available)
units
A key that indicates a data value transformation.

string, optional, default: lin (No transformation)
One of the following values: 'lin', 'chg', 'ch1', 'pch', 'pc1', 'pca', 'cch', 'cca', 'log'
lin = Levels (No transformation)
chg = Change
ch1 = Change from Year Ago
pch = Percent Change
pc1 = Percent Change from Year Ago
pca = Compounded Annual Rate of Change
cch = Continuously Compounded Rate of Change
cca = Continuously Compounded Annual Rate of Change
log = Natural Log

For unit transformation formulas, see: https://alfred.stlouisfed.org/help#growth_formulas
frequency
An optional parameter that indicates a lower frequency to aggregate values to. The FRED frequency aggregation feature converts higher frequency data series into lower frequency data series (e.g. converts a monthly data series into an annual data series). In FRED, the highest frequency data is daily, and the lowest frequency data is annual. There are 3 aggregation methods available- average, sum, and end of period. See the aggregation_method parameter.

string, optional, default: no value for no frequency aggregation
One of the following values: 'd', 'w', 'bw', 'm', 'q', 'sa', 'a', 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem'

Frequencies without period descriptions:
d = Daily
w = Weekly
bw = Biweekly
m = Monthly
q = Quarterly
sa = Semiannual
a = Annual


Frequencies with period descriptions:
wef = Weekly, Ending Friday
weth = Weekly, Ending Thursday
wew = Weekly, Ending Wednesday
wetu = Weekly, Ending Tuesday
wem = Weekly, Ending Monday
wesu = Weekly, Ending Sunday
wesa = Weekly, Ending Saturday
bwew = Biweekly, Ending Wednesday
bwem = Biweekly, Ending Monday

Note that an error will be returned if a frequency is specified that is higher than the native frequency of the series. For instance if a series has the native frequency 'Monthly' (as returned by the fred/series request), it is not possible to aggregate the series to the higher 'Daily' frequency using the frequency parameter value 'd'.
No frequency aggregation will occur if the frequency specified by the frequency parameter matches the native frequency of the series. For instance if the value of the frequency parameter is 'm' and the native frequency of the series is 'Monthly' (as returned by the fred/series request), observations will be returned, but they will not be aggregated to a lower frequency.
For most cases, it will be sufficient to specify a lower frequency without a period description (e.g. 'd', 'w', 'bw', 'm', 'q', 'sa', 'a') as opposed to frequencies with period descriptions (e.g. 'wef', 'weth', 'wew', 'wetu', 'wem', 'wesu', 'wesa', 'bwew', 'bwem') which only exist for the weekly and biweekly frequencies.
The weekly and biweekly frequencies with periods exist to offer more options and override the default periods implied by values 'w' and 'bw'.
The value 'w' defaults to frequency and period 'Weekly, Ending Friday' when aggregating daily series.
The value 'bw' defaults to frequency and period 'Biweekly, Ending Wednesday' when aggregating daily and weekly series.
Consider the difference between values 'w' for 'Weekly' and 'wef' for 'Weekly, Ending Friday'. When aggregating observations from daily to weekly, the value 'w' defaults to frequency and period 'Weekly, Ending Friday' which is the same as 'wef'. Here, the difference is that the period 'Ending Friday' is implicit for value 'w' but explicit for value 'wef'. However, if a series has native frequency 'Weekly, Ending Monday', an error will be returned for value 'wef' but not value 'w'.
Note that frequency aggregation is currently only available for file_type equal to xml or json due to time constraints.
Read the 'Frequency Aggregation' section of the FRED FAQs for implementation details.
aggregation_method
A key that indicates the aggregation method used for frequency aggregation. This parameter has no affect if the frequency parameter is not set.

string, optional, default: avg
One of the following values: 'avg', 'sum', 'eop'
avg = Average
sum = Sum
eop = End of Period

output_type
An integer that indicates an output type.

integer, optional, default: 1
One of the following values: '1', '2', '3', '4'
1 = Observations by Real-Time Period
2 = Observations by Vintage Date, All Observations
3 = Observations by Vintage Date, New and Revised Observations Only
4 = Observations, Initial Release Only

For output types '2' and '3', some XML attribute names start with the series ID which may have a first character that is a number (i.e. 0 through 9). In this case only, the XML attribute name starts with an underscore then the series ID in order to avoid invalid XML. If the series ID starts with a letter (i.e. A through Z) then an underscore is not prepended.
For more information, read: https://alfred.stlouisfed.org/help/downloaddata#outputformats
vintage_dates
A comma separated string of YYYY-MM-DD formatted dates in history (e.g. 2000-01-01,2005-02-24). Vintage dates are used to download data as it existed on these specified dates in history. Vintage dates can be specified instead of a real-time period using realtime_start and realtime_end.

Sometimes it may be useful to enter a vintage date that is not a date when the data values were revised. For instance you may want to know the latest available revisions on a particular date. Entering a vintage date is also useful to compare series on different releases with different release dates.

string, optional, no vintage dates are set by default.
Your query will be limited to a specific number of vintage dates depending on the series_id, file_type and output_type specified.

output_type=2, series_id=USRECD: 110 csv, 55 xlsx
output_type=2, any daily series: 450 csv, 225 xlsx
any output_type or other series: 1000 csv, 1000 xlsx, 2000 json, 2000 xml