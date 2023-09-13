import discord
import gspread
import json
import os
import pandas as pd
import requests
import time
from dateutil import parser
from discord import app_commands
# from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

MY_TEST_GUILD = discord.Object(id=694669381812224000)
MY_GUILD = discord.Object(id=1060601078573437008)
# 1083177865031462934 pnwwwc.dev
intents = discord.Intents.default()
# intents.typing = False
# intents.presences = False
# intents.message_content = True
# bot = commands.Bot(command_prefix='$',intents=intents)
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# NOTE: Sheets API has 60req/min limit at time of writing, may cause performance issue at scale
def get_sheet(spreadsheet_name, worksheet_name):
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('bot-credentials.json', scope)
    g_client = gspread.authorize(credentials)

    # Open the spreadsheet
    worksheet =  g_client.open(spreadsheet_name).worksheet(worksheet_name)
    return(worksheet.get_all_records())


# TODO share parameter to make public response
# TODO log interactions
@tree.command(
    name = "flow", 
    description = "Provides current flow of a channel's river segment.", 
    guild=MY_TEST_GUILD # TODO when left empty is it global for all discords, or just where bot is installed??
)
async def flow(interaction:discord.Interaction):
    channel_name = interaction.channel.name
    channel_id = interaction.channel_id

    print(channel_name)
    river_df = pd.DataFrame(get_sheet(os.getenv('G_SPREADSHEET'), os.getenv('G_WORKSHEET')))
    river = river_df[river_df['discord_channel_id'] == channel_id] # TODO catch unknown channels here
    gage_site_id = river.iloc[0]['gage_site_id']

    if gage_site_id != '' and gage_site_id is not None: 
        gage_api_params = json.loads(river.iloc[0]['gage_api_parameters'])
        gage_type = river.iloc[0]['gage_type']
        min_flow = river.iloc[0]['rec_min_flow']
        max_flow = river.iloc[0]['rec_max_flow']
        aw_link = river.iloc[0]['aw_url']
        links_string = f'[American Whitewater]({aw_link})'
        flowplot_link = river.iloc[0]['flowplot_url']

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
        last_updated = parser.parse(resp_selected['values'][0]['value'][0]['dateTime']).strftime('%Y-%m-%d %H:%M%Z')

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
        if flowplot_link == '':
            embed.add_field(name='Gage', value=f'{site_name}', inline=False)
        embed.add_field(name='Links', value=links_string, inline=False)
        embed.set_footer(text=f'Current flow sourced from {gage_type}.')
        if flowplot_link != '':
            unix_time = int(time.time())
            embed.set_image(url=f'{flowplot_link}&v={unix_time}') # This is NWRFC specific

        await interaction.response.send_message(embed=embed, ephemeral=True)
    else: 
        await interaction.response.send_message(f'Sorry, {channel_name} is not yet supported by Flow Bot.', ephemeral=True)
    # await interaction.response.send_message("Hello!", ephemeral=True) # Makes response only visible to user who calls it

# @client.event
# async def on_ready():
#     print(f'We have logged in as {client.user}')

@client.event
async def on_ready():
    await tree.sync(guild=MY_TEST_GUILD)
    print(f'We have logged in as {client.user}')
# @client.slash_command(
#     name="flow", 
#     guild_ids=['694669381812224000', '1060601078573437008']
# ) 
# async def flow_slash(ctx): 
#     await ctx.respond("You executed the slash command!")




# @bot.command(
#     help="Provides flow, most recent sample datetime, and gage location. \nColor adheres to AW range recommendation.",
# 	brief="Provides current flow of a channel's river section."
# )
# async def flow(ctx):
#     if ctx.author == ctx.bot.user:
#         return

#     channel_name = ctx.channel.name
#     channel_id = ctx.channel.id

#     print(channel_name)
#     river_df = pd.DataFrame(get_sheet(os.getenv('G_SPREADSHEET'), os.getenv('G_WORKSHEET')))
#     river = river_df[river_df['discord_channel_id'] == channel_id]
#     gage_site_id = river.iloc[0]['gage_site_id']

#     if gage_site_id != '' and gage_site_id is not None: 
#         gage_api_params = json.loads(river.iloc[0]['gage_api_parameters'])
#         gage_type = river.iloc[0]['gage_type']
#         min_flow = river.iloc[0]['rec_min_flow']
#         max_flow = river.iloc[0]['rec_max_flow']
#         aw_link = river.iloc[0]['aw_url']
#         links_string = f'[American Whitewater]({aw_link})'
#         flowplot_link = river.iloc[0]['flowplot_url']

#         if river.iloc[0]['has_river_forecast'].lower() == 'true':
#             forecast_link = river.iloc[0]['river_forecast_url']
#             links_string += f'\n[Flow Forecast]({forecast_link})'

#         base_url = river.iloc[0]['gage_api_url']
#         params = { # TODO make params more flexible for different sources, these work with usgs only
#             'format': 'json',
#             'sites': gage_site_id,
#             'parameterCd': gage_api_params['parameterCd'],
#             'siteStatus': 'all'
#         }
#         resp_json = requests.get(url=base_url, params=params).json()
#         resp_selected = resp_json['value']['timeSeries'][0]
#         site_name = resp_selected['sourceInfo']['siteName']
#         flow_unit = resp_selected['variable']['unit']['unitCode']
#         flow_val = float(resp_selected['values'][0]['value'][0]['value'])
#         last_updated = parser.parse(resp_selected['values'][0]['value'][0]['dateTime']).strftime('%Y-%m-%d %H:%M%Z')

#         embed_color = discord.Color.green()
#         if flow_val < river.iloc[0]['rec_min_flow']:
#             embed_color = discord.Color.red()
#         elif flow_val > river.iloc[0]['rec_max_flow']:
#             embed_color = discord.Color.blue()

#         embed=discord.Embed(
#             title=f'Current Conditions', 
#             color=embed_color
#         )
#         embed.add_field(name='Flow', value=f'{flow_val} {flow_unit}', inline=True)
#         embed.add_field(name='Recommended', value=f'{min_flow}-{max_flow} {flow_unit}', inline=True)
#         embed.add_field(name='Updated', value=f'{last_updated}', inline=False)
#         if flowplot_link == '':
#             embed.add_field(name='Gage', value=f'{site_name}', inline=False)
#         embed.add_field(name='Links', value=links_string, inline=False)
#         embed.set_footer(text=f'Current flow sourced from {gage_type}.')
#         if flowplot_link != '':
#             unix_time = int(time.time())
#             embed.set_image(url=f'{flowplot_link}&v={unix_time}') # This is NWRFC specific

#         await ctx.channel.send(embed=embed)
#     else: 
#         await ctx.channel.send(f'Sorry, {channel_name} is not yet supported by Flow Bot.')

client.run(os.getenv('BOT_TOKEN'))
