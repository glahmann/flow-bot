import discord
import os
import gspread
import json
import pandas as pd
import requests
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.message_content = True
bot = commands.Bot(command_prefix='$',intents=intents)

# NOTE: Sheets API has 60req/min limit at time of writing, may cause performance issue at scale
def get_sheet(spreadsheet_name, worksheet_name):
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('bot-credentials.json', scope)
    g_client = gspread.authorize(credentials)

    # Open the spreadsheet
    worksheet =  g_client.open(spreadsheet_name).worksheet(worksheet_name)
    return(worksheet.get_all_records())

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command(
    help="Provides gage location, flow, and last sample datetime. Color adheres to AW range recommendation.",
	brief="Provides current flow of the channel's river section."
)
async def flow(ctx):
    if ctx.author == ctx.bot.user:
        return

    channel_name = ctx.channel.name
    channel_id = ctx.channel.id

    print(channel_name)
    river_df = pd.DataFrame(get_sheet(os.getenv('G_SPREADSHEET'), os.getenv('G_WORKSHEET')))
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

        await ctx.channel.send(f'Hello {channel_name} boaters\nGage: {site_name}\nFlow: {flow_val} {flow_unit} {flow_status_emoji}\nUpdated: {last_updated}')
    else: 
        await ctx.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')

    # TODO embed
    # embed=discord.Embed(title="Sample Embed", \
    #     url="https://realdrewdata.medium.com/", \
    #     description="This is an embed that will show how to build an embed and the different components", \
    #     color=**discord.Color.blue()**)
    # await ctx.send(embed=embed)

bot.run(os.getenv('BOT_TOKEN'))
