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
    help="Provides flow, most recent sample datetime, and gage location. \nColor adheres to AW range recommendation.",
	brief="Provides current flow of a channel's river section."
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

    if gage_site_id != '' and gage_site_id is not None: 
        gage_api_params = json.loads(river.iloc[0]['gage_api_parameters'])
        gage_type = river.iloc[0]['gage_type']
        min_flow = river.iloc[0]['rec_min_flow']
        max_flow = river.iloc[0]['rec_max_flow']
        aw_link = river.iloc[0]['aw_url']
        links_string = f'[American Whitewater]({aw_link})'

        if river.iloc[0]['has_river_forecast'].lower() == 'true':
            forecast_link = river.iloc[0]['river_forecast_url']
            links_string += f'\n[Flow Forecast]({forecast_link})'

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

        embed_color = discord.Color.green()
        if flow_val < river.iloc[0]['rec_min_flow']:
            embed_color = discord.Color.red()
        elif flow_val > river.iloc[0]['rec_max_flow']:
            embed_color = discord.Color.blue()

        embed=discord.Embed(
            title=f'Current Conditions', 
            color=embed_color
        )
        embed.add_field(name='Flow', value=f'{flow_val} {flow_unit}', inline=True)
        embed.add_field(name='Recommended', value=f'{min_flow}-{max_flow} {flow_unit}', inline=True)
        embed.add_field(name='Updated', value=f'{last_updated}', inline=False)
        embed.add_field(name='Gage', value=f'{site_name}', inline=False)
        embed.add_field(name='Links', value=links_string, inline=False)
        embed.set_footer(text=f'Data sourced from {gage_type}.')

        await ctx.channel.send(embed=embed)
    else: 
        await ctx.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')

bot.run(os.getenv('BOT_TOKEN'))
