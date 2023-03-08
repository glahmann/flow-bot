import discord
import os
import requests

# <channel_name>:<usgs_gage_id>
site_dict = {
    'ww-test': '12134500',
    # ---- Beginner ----
    'sno-mf-3-upper': '12141300', 
    'sno-powerhouse': '12144500',
    'green-3-yoyo': '12113000',
    'sno-mf-clubstretch': '12141300',
    'sky-2': '12134500',
    # ---- Intermediate ----
    'cedar-gates': '12117600', 
    'green-1-headworks': '12106700', # purification plant
    'sno-sf-2': '12143600',
    'skagit-2': '12178000',
    'nisqually-3': '12089500',
    # ---- Advanced ----
    'sno-mf-4-middlemiddle': '12141300', 
    'sky-1-boulderdrop': '12134500',
    'stilly-sf-2-sillystilly': '12161000',
    'green-2-lowergorge': '12106700',
    'sauk-2': '12189500',
    'tieton-1-uppertieton': '', # Not USGS; Use Dreamflows Tieton At Rimrock
    'tilton-1-upper': '14236200',
    'white-salmon-4': '14123500',
    # ---- Expert & Pro ----
    'sultan-2': '12138160', 
    'lewis-efl-2-falls': '14222500', # Not standardized name
    'tilton-2-lower': '14236200',
    'green-2-uppergorge': '12106700',
    'sultan-1-uppersultan': '12137800'
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
    if message.content.startswith('$flow') and channel_name == 'ww-test': # Second condition for dev only
        print(f'{message.content}\n{channel_name}')
        site_id = site_dict[channel_name]
        if site_id != '': # TODO check is not none?
            base_url = 'http://waterservices.usgs.gov/nwis/iv/' # TODO get this from table
            params = {
                'format': 'json',
                'sites': site_id,
                # TODO get parameterCd from table -- gage may be cfs or feet or both depending on location
                'parameterCd': '00060,00065', #00010', # 00010 temp not present at MM Tanner gage; order not guaranteed
                'siteStatus': 'all'
            }
            resp_json = requests.get(url=base_url, params=params).json()
            resp_selected = resp_json['value']['timeSeries'][0]
            site_name = resp_selected['sourceInfo']['siteName'] # 00060 == cfs
            flow_unit = resp_selected['variable']['unit']['unitCode']  #['unitCode']
            flow_val = resp_selected['values'][0]['value'][0]['value']
            last_updated = resp_selected['values'][0]['value'][0]['dateTime']
            await message.channel.send(f'Hello {channel_name}\nGage: {site_name}\nFlow: {flow_val} {flow_unit}\nUpdated: {last_updated}')

client.run(os.getenv('TOKEN'))
