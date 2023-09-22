import discord
import gspread
import json
import os
import pandas as pd
import requests
import time
from dataclasses import dataclass
from dateutil import parser
from discord import app_commands
from oauth2client.service_account import ServiceAccountCredentials

MY_GUILD = discord.Object(id=os.getenv('BOT_GUILD')) # PNW Whitewater Chasers

@dataclass
class RiverSegment:
    gage_site_id: str
    gage_api_url: str
    gage_api_params: str
    gage_src: str
    rec_min_flow: float
    rec_max_flow: float
    site_links: str
    flowplot_link: str

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

client = MyClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# NOTE: Sheets API has 60req/min limit at time of writing, may cause performance issue at scale
def get_gsheet(spreadsheet_name, worksheet_name):
    # Connect to Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('bot-credentials.json', scope)
    g_client = gspread.authorize(credentials)

    # Open the spreadsheet
    worksheet =  g_client.open(spreadsheet_name).worksheet(worksheet_name)
    return(worksheet.get_all_records())


def get_msg_color(flow:float, min_flow:float, max_flow:float):
    color = discord.Color.green()
    if flow < min_flow:
        color = discord.Color.red()
    elif flow > max_flow:
        color = discord.Color.blue()
    return color


def build_river(river:pd.DataFrame):
    gage_site_id = river.iloc[0]['gage_site_id']
    if gage_site_id != '' and gage_site_id is not None: 
        site_links = '[American Whitewater]({})'.format(river.iloc[0]['aw_url'])
        if river.iloc[0]['has_river_forecast'].lower() == 'true':
            site_links += '\n[Flow Forecast]({})'.format(river.iloc[0]['river_forecast_url'])
        river_seg = RiverSegment(
            gage_site_id,
            river.iloc[0]['gage_api_url'],
            json.loads(river.iloc[0]['gage_api_parameters']),
            river.iloc[0]['gage_type'],
            river.iloc[0]['rec_min_flow'],
            river.iloc[0]['rec_max_flow'],
            site_links,
            river.iloc[0]['flowplot_url']
        )
    return river_seg


def build_embed(river:RiverSegment, flow_val:float, flow_unit:str, last_updated:str, site_name:str):
    embed_color = get_msg_color(flow_val, river.rec_min_flow, river.rec_max_flow)

    embed=discord.Embed(
        title=f'Current Conditions', 
        color=embed_color
    )
    embed.add_field(name='Flow', value=f'{flow_val} {flow_unit}', inline=True)
    embed.add_field(name='Recommended', value=f'{river.rec_min_flow}-{river.rec_max_flow} {flow_unit}', inline=True)
    embed.add_field(name='Updated', value=f'{last_updated}', inline=False)
    if river.flowplot_link == '':
        embed.add_field(name='Gage', value=f'{site_name}', inline=False)
    embed.add_field(name='Links', value=river.site_links, inline=False)
    embed.set_footer(text=f'Current flow sourced from {river.gage_src}.')
    if river.flowplot_link != '':
        unix_time = int(time.time())
        embed.set_image(url=f'{river.flowplot_link}&v={unix_time}') # This is NWRFC specific
    return embed


# TODO share parameter to make public response
@client.tree.command(
    name = "flow", 
    description = "Provides current flow of a channel's river segment.", 
)
@app_commands.describe(share='Share this response with the channel?')
@app_commands.choices(share=[
    app_commands.Choice(name='Yes', value=0),
    app_commands.Choice(name='No', value=1)
])
async def flow(interaction:discord.Interaction, share:app_commands.Choice[int]):
    await interaction.response.defer(ephemeral=bool(share.value)) # Prevents errors from 3 second response limitation
    channel_name = interaction.channel.name
    channel_id = interaction.channel_id

    print(f'{channel_name} called by {interaction.user.name}') # TODO log interactions
    river_df = pd.DataFrame(get_gsheet(os.getenv('G_SPREADSHEET'), os.getenv('G_WORKSHEET')))
    river = river_df[river_df['discord_channel_id'] == channel_id] # TODO catch unknown channels here
    if river.size == 0: # Exit if no entry in database for channel
        await interaction.followup.send(f'Sorry, {channel_name} is not supported by Flow Bot.')
        return
    
    try:
        river_seg = build_river(river)
    except:
        await interaction.followup.send(f'Sorry, data is not yet available for {channel_name}.')
        return
    
    params = { # TODO make params more flexible for different sources, these work with usgs only
        'format': 'json',
        'sites': river_seg.gage_site_id,
        'parameterCd': river_seg.gage_api_params['parameterCd'],
        'siteStatus': 'all'
    }
    resp_json = requests.get(url=river_seg.gage_api_url, params=params).json()
    resp_selected = resp_json['value']['timeSeries'][0]

    embed = build_embed(
        river_seg,
        float(resp_selected['values'][0]['value'][0]['value']),
        resp_selected['variable']['unit']['unitCode'],
        parser.parse(resp_selected['values'][0]['value'][0]['dateTime']).strftime('%Y-%m-%d %H:%M%Z'),
        resp_selected['sourceInfo']['siteName']
    )

    await interaction.followup.send(embed=embed)

client.run(os.getenv('BOT_TOKEN'))
