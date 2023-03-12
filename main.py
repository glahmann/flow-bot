import discord
import os
import requests
from river_data import RIVER_DICT

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
        print(f'{channel_name}\n{channel_id}')
        river = RIVER_DICT[channel_id]
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
