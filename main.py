import discord
import os
import requests

intents=discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$flow'):
        print(f'{message.content}\n{message.channel}')

        base_url = 'http://waterservices.usgs.gov/nwis/iv/' # TODO get this from table
        params = {
            'format': 'json',
            'sites': '12141300', # MM at Tanner TODO get from table
            # TODO get parameterCd from table -- gage may be cfs or feet or both depending on location
            'parameterCd': '00060,00065,00010', # 00010 temp not present at MM Tanner gage 
            'siteStatus': 'all'
        }
        resp_json = requests.get(url=base_url, params=params).json()
        resp_selected = resp_json['value']['timeSeries'][0]
        site_name = resp_selected['sourceInfo']['siteName'] # 00060 == cfs
        flow_unit = resp_selected['variable']['unit']['unitCode']  #['unitCode']
        flow_val = resp_selected['values'][0]['value'][0]['value']
        last_updated = resp_selected['values'][0]['value'][0]['dateTime']
        await message.channel.send(f'Hello {message.channel}\n{site_name}\n{flow_val} {flow_unit}\nUpdated: {last_updated}')

client.run(os.getenv('TOKEN'))
