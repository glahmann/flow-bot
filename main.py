import discord
import os
import requests

# This is temp, don't @ me
# {channel_id:{river_info}}
river_dict = {
    1083177865031462934: {'site-id':'12117600', 'channel-name':'dev', 'min-flow':900, 'max-flow':3000}, 
    # ---- Beginner ----
    1067989049014501476: {'site-id':'12141300', 'channel-name':'sno-mf-3-upper', 'min-flow':1000, 'max-flow':3000}, 
    1060604175718826015: {'site-id':'12144500', 'channel-name':'sno-powerhouse', 'min-flow':300, 'max-flow':4000},
    1060606179706929193: {'site-id':'12113000', 'channel-name':'green-3-yoyo', 'min-flow':1000, 'max-flow':2000},
    1060634900417486971: {'site-id':'12141300', 'channel-name':'sno-mf-clubstretch', 'min-flow':800, 'max-flow':2500},
    1060605777896820897: {'site-id':'12134500', 'channel-name':'sky-2', 'min-flow':1000, 'max-flow':4000},
    # ---- Intermediate ----
    1060635111529402419: {'site-id':'12117600', 'channel-name':'cedar-gates', 'min-flow':400, 'max-flow':1200}, 
    1060604581953941585: {'site-id':'12106700', 'channel-name':'green-1-headworks', 'min-flow':1000, 'max-flow':3000}, # purification plant
    1060604744869105786: {'site-id':'12143600', 'channel-name':'sno-sf-2', 'min-flow':300, 'max-flow':2500},
    1060639549912526928: {'site-id':'12178000', 'channel-name':'skagit-2', 'min-flow':1500, 'max-flow':15000},
    1075975821216464956: {'site-id':'12089500', 'channel-name':'nisqually-3', 'min-flow':900, 'max-flow':3000},
    # ---- Advanced ----
    1060602511901335592: {'site-id':'12141300', 'channel-name':'sno-mf-4-middlemiddle', 'min-flow':1000, 'max-flow':5000}, 
    1060605564062806036: {'site-id':'12134500', 'channel-name':'sky-1-boulderdrop', 'min-flow':700, 'max-flow':20000},
    1060629615162445874: {'site-id':'12161000', 'channel-name':'stilly-sf-2-sillystilly', 'min-flow':5.2, 'max-flow':8.0},
    1060605201804972123: {'site-id':'12106700', 'channel-name':'green-2-lowergorge', 'min-flow':1000, 'max-flow':4000},
    1062431458192527390: {'site-id':'12189500', 'channel-name':'sauk-2', 'min-flow':2000, 'max-flow':15000},
    1062438564396282027: {'site-id':'', 'channel-name':'tieton-1-uppertieton', 'min-flow':1000, 'max-flow':3200}, # Not USGS; Use Dreamflows Tieton At Rimrock
    1067270362036981822: {'site-id':'14236200', 'channel-name':'tilton-1-upper', 'min-flow':800, 'max-flow':2000},
    1076677633212952596: {'site-id':'14123500', 'channel-name':'white-salmon-4', 'min-flow':500, 'max-flow':2000},
    # ---- Expert & Pro ----
    1068767691378262066: {'site-id':'12138160', 'channel-name':'sultan-2', 'min-flow':350, 'max-flow':3000}, 
    1060631962227834980: {'site-id':'14222500', 'channel-name':'lewis-efl-2-falls', 'min-flow':600, 'max-flow':2800}, # Not standardized channel-name
    1060633487624912906: {'site-id':'14236200', 'channel-name':'tilton-2-lower', 'min-flow':800, 'max-flow':4000},
    1060605060599529643: {'site-id':'12106700', 'channel-name':'green-2-uppergorge', 'min-flow':1000, 'max-flow':4000},
    1062438461564526722: {'site-id':'12137800', 'channel-name':'sultan-1-uppersultan', 'min-flow':400, 'max-flow':1500},
    # ---- Pro ----
    1071634874693337100: {'site-id':'12161000', 'channel-name':'canyon-creek-cc-stilly', 'min-flow':5.5, 'max-flow':6.5},
    1083583845305167892: {'site-id':'', 'channel-name':'pilchuck-2', 'min-flow':600, 'max-flow':4000} # WADOE gage
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

    channel_name = message.channel.name
    channel_id = message.channel.id
    # TODO handle non-usgs sources
    if message.content.startswith('$flow'):
        print(f'{message.content}\n{channel_name}\n{channel_id}')
        river = river_dict[channel_id]
        if river['site-id'] != '' and river['site-id'] is not None: 
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

            await message.channel.send(f'Hello {channel_name} boaters\nGage: {site_name}\nFlow: {flow_val} {flow_unit} {flow_status_emoji}\nUpdated: {last_updated}')
        else: 
            await message.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')
client.run(os.getenv('TOKEN'))
