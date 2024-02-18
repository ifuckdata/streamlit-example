import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


channel_name = "nicoleforcadela"

import os
import subprocess
from datetime import datetime
import re
import json

import asyncio
import time
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import pandas as pd

def format_date(input_date):
    date_obj = datetime.strptime(input_date, '%m/%d/%Y')
    formatted_date = date_obj.strftime('%d %b %Y')
    return formatted_date

def clean_string(input_string):
    cleaned_string = re.sub(r'[^A-Za-z0-9\s-]', '', input_string)
    return cleaned_string


async def get_page_content(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url)
        time.sleep(10)
        page_content = await page.content()

        await browser.close()

        return page_content


def get_vod_list_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    vod_list = []

    table = soup.find('table', {'id': 'twitch-grouped'})
    rows = table.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            vod = {
                'title': clean_string(cells[1].text),
                'vod_link': cells[1].find('a')['href'],
                'date': format_date(cells[2].text),
                'duration': cells[4].text
            }
            vod_list.append(vod)

    for i in range(len(vod_list)):
        vod_list[i]["index"]=i

    return vod_list


async def get_twitch_vods_html(channel_name):
    page_content = await get_page_content(f'https://vodarchive.com/?username={channel_name}')
    vod_list = get_vod_list_from_html(page_content)
    return vod_list


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    return output.decode('utf-8')


def generate_vod_name(vod_list, index):
    vod = vod_list[index]
    name = f'{vod["date"]} {vod["title"]}'.strip()
    return name

def download_vod(vod_list, index, quality):
    vod_url = vod_list[index]["vod_link"]
    vod_m3u8 = run_command(f"streamlink --url {vod_url} --json")
    vod_m3u8 = json.loads(vod_m3u8)
    vod_m3u8 = vod_m3u8['streams'][quality]['url']
    vod_m3u8 = vod_m3u8.split("/")[:-1]
    vod_m3u8 = "/".join(vod_m3u8)
    vod_m3u8 = f"{vod_m3u8}/index-dvr.m3u8"
    print(vod_m3u8)
    name = generate_vod_name(vod_list, index)
    os.system(f"ffmpeg -i {vod_m3u8} -c copy ./'{name}.mp4'")



#channel_name = 'sapphiresings_ph'
available_vods = await get_twitch_vods_html(channel_name)

available_vods_df = pd.DataFrame(available_vods)
pd.options.display.max_rows = None

st.write("hello")
st.dataframe(available_vods_df)
