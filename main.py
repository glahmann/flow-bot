import discord
import os
import gspread
import json
import pandas as pd
import requests
from oauth2client.service_account import ServiceAccountCredentials

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
client = discord.Client(intents=intents)

# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('bot-credentials.json', scope)
g_client = gspread.authorize(credentials)

# Open the spreadsheet
worksheet =  g_client.open(os.getenv('G_SPREADSHEET')).worksheet(os.getenv('G_WORKSHEET'))
river_df = pd.DataFrame(worksheet.get_all_records())

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel_name = message.channel.name
    channel_id = message.channel.id
    if message.content.startswith('$flow'):
        print(channel_name)
        river = river_df[river_df['discord_channel_id'] == channel_id]
        gage_site_id = river.iloc[0]['gage_site_id']
        gage_api_params = json.loads(river.iloc[0]['gage_api_parameters'])

        if gage_site_id != '' and gage_site_id is not None: 
            base_url = river.iloc[0]['gage_api_url']
            params = { # TODO make params more flexible for different sources, these work with usgs only
                'format': 'json',
                'sites': gage_site_id,
                'parameterCd': gage_api_params['parameterCd'],
                'siteStatus': 'all'
            }
            resp_json = requests.get(url=base_url, params=params).json()
            resp_selected = resp_json['value']['timeSeries'][0]
            site_name = resp_selected['sourceInfo']['siteName']
            flow_unit = resp_selected['variable']['unit']['unitCode']
            flow_val = float(resp_selected['values'][0]['value'][0]['value'])
            last_updated = resp_selected['values'][0]['value'][0]['dateTime']

            flow_status_emoji = '\U0001F7E2' # Green circle
            if flow_val < river.iloc[0]['rec_min_flow']:
                flow_status_emoji = '\U0001F534' # Red circle
            elif flow_val > river.iloc[0]['rec_max_flow']:
                flow_status_emoji = '\U0001F535' # Blue circle

            await message.channel.send(f'Hello {channel_name} boaters\nGage: {site_name}\nFlow: {flow_val} {flow_unit} {flow_status_emoji}\nUpdated: {last_updated}')
        else: 
            await message.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')

client.run(os.getenv('BOT_TOKEN'))
