import discord
import os
import requests

# This is temp, don't @ me
river_dict = {
    'dev': {'site-id':'', 'min-flow':900, 'max-flow':3000},
    # ---- Beginner ----
    'sno-mf-3-upper': {'site-id':'12141300', 'min-flow':1000, 'max-flow':3000}, 
    'sno-powerhouse': {'site-id':'12144500', 'min-flow':300, 'max-flow':4000},
    'green-3-yoyo': {'site-id':'12113000', 'min-flow':1000, 'max-flow':2000},
    'sno-mf-clubstretch': {'site-id':'12141300', 'min-flow':800, 'max-flow':2500},
    'sky-2': {'site-id':'12134500', 'min-flow':1000, 'max-flow':4000},
    # ---- Intermediate ----
    'cedar-gates': {'site-id':'12117600', 'min-flow':400, 'max-flow':1200}, 
    'green-1-headworks': {'site-id':'12106700', 'min-flow':1000, 'max-flow':3000}, # purification plant
    'sno-sf-2': {'site-id':'12143600', 'min-flow':300, 'max-flow':2500},
    'skagit-2': {'site-id':'12178000', 'min-flow':1500, 'max-flow':15000},
    'nisqually-3': {'site-id':'12089500', 'min-flow':900, 'max-flow':3000},
    # ---- Advanced ----
    'sno-mf-4-middlemiddle': {'site-id':'12141300', 'min-flow':1000, 'max-flow':5000}, 
    'sky-1-boulderdrop': {'site-id':'12134500', 'min-flow':700, 'max-flow':20000},
    'stilly-sf-2-sillystilly': {'site-id':'12161000', 'min-flow':5.2, 'max-flow':8.0},
    'green-2-lowergorge': {'site-id':'12106700', 'min-flow':1000, 'max-flow':4000},
    'sauk-2': {'site-id':'12189500', 'min-flow':2000, 'max-flow':15000},
    'tieton-1-uppertieton': {'site-id':'', 'min-flow':1000, 'max-flow':3200}, # Not USGS; Use Dreamflows Tieton At Rimrock
    'tilton-1-upper': {'site-id':'14236200', 'min-flow':800, 'max-flow':2000},
    'white-salmon-4': {'site-id':'14123500', 'min-flow':500, 'max-flow':2000},
    # ---- Expert & Pro ----
    'sultan-2': {'site-id':'12138160', 'min-flow':350, 'max-flow':3000}, 
    'lewis-efl-2-falls': {'site-id':'14222500', 'min-flow':600, 'max-flow':2800}, # Not standardized name
    'tilton-2-lower': {'site-id':'14236200', 'min-flow':800, 'max-flow':4000},
    'green-2-uppergorge': {'site-id':'12106700', 'min-flow':1000, 'max-flow':4000},
    'sultan-1-uppersultan': {'site-id':'12137800', 'min-flow':400, 'max-flow':1500},
    # ---- Pro ----
    'canyon-creek-cc-stilly': {'site-id':'12161000', 'min-flow':5.5, 'max-flow':6.5}
}

intents = discord.Intents.default()
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

    channel_name = str(message.channel)
    # TODO handle non-usgs sources
    if message.content.startswith('$flow'):
        print(f'{message.content}\n{channel_name}')
        river = river_dict[channel_name]
        if river['site-id'] != '' and river['site-id'] is not None: # TODO check is not none? 
            base_url = 'http://waterservices.usgs.gov/nwis/iv/' # TODO get this from table
            params = {
                'format': 'json',
                'sites': river['site-id'],
                # TODO get parameterCd from table -- gage may be cfs or feet or both depending on location
                'parameterCd': '00060,00065', #cfs, ft; order not guaranteed
                'siteStatus': 'all'
            }
            resp_json = requests.get(url=base_url, params=params).json()
            resp_selected = resp_json['value']['timeSeries'][0]
            site_name = resp_selected['sourceInfo']['siteName']
            flow_unit = resp_selected['variable']['unit']['unitCode']
            flow_val = float(resp_selected['values'][0]['value'][0]['value'])
            last_updated = resp_selected['values'][0]['value'][0]['dateTime']

            flow_status_emoji = '\U0001F7E2' # Green circle
            if flow_val < river['min-flow']:
                flow_status_emoji = '\U0001F534' # Red circle
            elif flow_val > river['max-flow']:
                flow_status_emoji = '\U0001F535' # Blue circle

            await message.channel.send(f'Hello {channel_name} boaters!\nGage: {site_name}\nFlow: {flow_val} {flow_unit} {flow_status_emoji}\nUpdated: {last_updated}')
        else: 
            await message.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')
client.run(os.getenv('TOKEN'))
