#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta

import requests
from playwright.async_api import async_playwright, Error as PlaywrightError


# ─── KULLANICI KANAL LİSTESİ ──────────────────────────────────────────────────
KANALLAR = [
    
    {
        "name": "uktntsports1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TNT%20Sports%201&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "uktntsports2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TNT%20Sports%202&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "uktntsports3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TNT%20Sports%203&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "uktntsports4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TNT%20Sports%204&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "uktntsportsultimate",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TNT%20Sports%20Ultimate&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsmainevent",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Main%20Event&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportspremierleague",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Premier%20League&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsfootball",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Football&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsf1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20F1&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportscricket",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Cricket&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsgolf",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Golf&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsaction",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Action&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsarena",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Arena&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportstennis",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Tennis&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsmix",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Mix&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsnews",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20News&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukskysportsracing",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sports%20Racing&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukpremiersports1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Premier%20Sports%201&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukpremiersports2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Premier%20Sports%202&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukeurosport1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Eurosport%201&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukeurosport2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Eurosport%202&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukbbcone",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=BBC%20One&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukbbctwo",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=BBC%20Two&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukitv1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ITV%201&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukchannel4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Channel%204&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "ukchannel5",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Channel%205&code=gb&user=cdnlivetv&plan=free",
        "group": "uk"
    },
    {
        "name": "trbeinsports1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%201&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trbeinsports2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%202&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trbeinsports3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%203&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trbeinsports4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%204&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trbeinsports5",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%205&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
    "name": "trbeinsportsmax1",
    "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%20MAX%201&code=tr&user=cdnlivetv&plan=free",
    "group": "tr"
  },
    {
    "name": "trbeinsportsmax2",
    "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%20MAX%202&code=tr&user=cdnlivetv&plan=free",
    "group": "tr"
  },
    {
        "name": "trbeinsportshaber",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%20Haber&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trssport",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=S%20Sport&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trssport2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=S%20Sport%202&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtivibuspor1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Tivibu%20Spor%201&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtivibuspor2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Tivibu%20Spor%202&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtivibuspor3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Tivibu%20Spor%203&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtivibuspor4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Tivibu%20Spor%204&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtrtspor",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TRT%20Spor&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtrtsporyildiz",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TRT%20Spor%20Yildiz&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "traspor",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=A%20Spor&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "trtv8buçuk",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TV8.5&code=tr&user=cdnlivetv&plan=free",
        "group": "tr"
    },
    {
        "name": "usespn",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPN&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usespn2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPN%202&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usespnu",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPNU&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usespnews",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPNews&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usespndeportes",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPN%20Deportes&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usfoxsports1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Sports%201&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usfoxsports2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Sports%202&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usbigtennetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Big%20Ten%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "ussecnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SEC%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usaccnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ACC%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "uscbsportsnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=CBS%20Sports%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usnbcsports",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=NBC%20Sports&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usnbatv",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=NBA%20TV&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usnflnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=NFL%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usnhlnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=NHL%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usmlbnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=MLB%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "ustennischannel",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Tennis%20Channel&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usgolfchannel",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Golf%20Channel&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "uswillowtv",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Willow%20TV&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "uswwe",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=WWE%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usfightnetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fight%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usabc",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ABC&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "uscbs",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=CBS&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usnbc",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=NBC&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "usfox",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=FOX&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "ususanetwork",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=USA%20Network&code=us&user=cdnlivetv&plan=free",
        "group": "us"
    },
    {
        "name": "frcanalplus",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Canal%2B&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frcanalplussport",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Canal%2B%20Sport&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frcanalplusfoot",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Canal%2B%20Foot&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frcanalplussport360",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Canal%2B%20Sport%20360&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frbeinsports1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%201&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frbeinsports2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%202&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frbeinsports3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%203&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%204&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax5",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%205&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax6",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%206&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax7",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%207&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax8",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%208&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax9",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%209&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    
    {
        "name": "frbeinsportsmax10",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20SPORTS%20MAX%2010&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frrmcsport1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=RMC%20Sport%201&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "frrmcsport2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=RMC%20Sport%202&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "freurosport1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Eurosport%201%20FR&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "freurosport2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Eurosport%202%20FR&code=fr&user=cdnlivetv&plan=free",
        "group": "fr"
    },
    {
        "name": "esdaznlaliga",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%20LaLiga&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esdazn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%201%20ES&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esdazn2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%202%20ES&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esdaznf1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%20F1&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esmovistarlaliga",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Movistar%20LaLiga&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esmovistarligadecampeones",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Movistar%20Liga%20de%20Campeones&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esmovistardeportes",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Movistar%20Deportes&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esmovistargolf",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Movistar%20Golf&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "esmovistarplus",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Movistar%20Plus%2B&code=es&user=cdnlivetv&plan=free",
        "group": "es"
    },
    {
        "name": "deskysportbundesliga1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Bundesliga%201&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "deskysporttopevent",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Top%20Event&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "deskysportpremierleague",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Premier%20League&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "deskysportf1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20F1%20DE&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "dedazn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%201%20DE&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "dedazn2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%202%20DE&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "desport1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sport1&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    {
        "name": "defussball",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=fussball&code=de&user=cdnlivetv&plan=free",
        "group": "de"
    },
    
    {
        "name": "itskysportuno",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Uno&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itskysportcalcio",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Calcio&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itskysportfootball",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20Football&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itskysportf1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20F1%20IT&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itskysportmotogp",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%20MotoGP&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itskysport24",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sky%20Sport%2024&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "itdazn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%201%20IT&code=it&user=cdnlivetv&plan=free",
        "group": "it"
    },
    {
        "name": "catsn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%201&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "catsn2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%202&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "catsn3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%203&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "catsn4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%204&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "catsn5",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=TSN%205&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "casportsnetontario",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sportsnet%20Ontario&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "casportsnetone",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sportsnet%20One&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "casportsnet360",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sportsnet%20360&code=ca&user=cdnlivetv&plan=free",
        "group": "ca"
    },
    {
        "name": "ptsporttv1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sport%20TV%201&code=pt&user=cdnlivetv&plan=free",
        "group": "pt"
    },
    {
        "name": "ptsporttv2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sport%20TV%202&code=pt&user=cdnlivetv&plan=free",
        "group": "pt"
    },
    {
        "name": "ptsporttv3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Sport%20TV%203&code=pt&user=cdnlivetv&plan=free",
        "group": "pt"
    },
    {
        "name": "ptdazn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=DAZN%201%20PT&code=pt&user=cdnlivetv&plan=free",
        "group": "pt"
    },
    {
        "name": "ptbenficatv",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Benfica%20TV&code=pt&user=cdnlivetv&plan=free",
        "group": "pt"
    },
    {
        "name": "nlziggosportselect",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Ziggo%20Sport%20Select&code=nl&user=cdnlivetv&plan=free",
        "group": "nl"
    },
    {
        "name": "nlziggosportvoetbal",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Ziggo%20Sport%20Voetbal&code=nl&user=cdnlivetv&plan=free",
        "group": "nl"
    },
    {
        "name": "nlziggosportracing",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Ziggo%20Sport%20Racing&code=nl&user=cdnlivetv&plan=free",
        "group": "nl"
    },
    {
        "name": "nlespn1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPN%201%20NL&code=nl&user=cdnlivetv&plan=free",
        "group": "nl"
    },
    {
        "name": "nlespn2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=ESPN%202%20NL&code=nl&user=cdnlivetv&plan=free",
        "group": "nl"
    },
    {
        "name": "aufoxleague",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20League&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "aufoxfooty",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Footy&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "aufoxcricket",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Cricket&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "aufoxsports503",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Sports%20503&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "aufoxsports505",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Sports%20505&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "aufoxsports506",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Fox%20Sports%20506&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "auoptussport1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Optus%20Sport%201&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "austansport",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Stan%20Sport&code=au&user=cdnlivetv&plan=free",
        "group": "au"
    },
    {
        "name": "arbeinsports1premium",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%201%20Premium&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arbeinsports2premium",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%202%20Premium&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arbeinsports3premium",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%203%20Premium&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arbeinsportsenglish1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=beIN%20Sports%20English%201&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arssc1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%201&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arssc2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%202&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arssc3",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%203&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arssc4",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%204&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arssc5",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%205&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "arsscextra1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=SSC%20Extra%201&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "aralkass1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Alkass%201&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "aralkass2",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=Alkass%202&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    },
    {
        "name": "aradextrap1",
        "url": "https://cdnlivetv.tv/api/v1/channels/player/?name=AD%20Sports%20Premium%201&code=ar&user=cdnlivetv&plan=free",
        "group": "ar"
    }
    # Yeni kanalları yukarıdaki şablona göre buraya ekleyebilirsiniz.
]

# ─── SİSTEM AYARLARI ──────────────────────────────────────────────────────────
OUTPUT_DIR_NAME = "cdnlive"     # Klasör adı
DEBUG_FILE = "debug_failed.json"

TIMEOUT = 15000                 # Sayfa yükleme zaman aşımı (15s)
FIRST_WAIT = 3.0                # İlk yüklemede akış bekleme süresi (sn)
RELOAD_WAIT = 4.5               # Yenileme sonrası bekleme süresi (sn)
MAX_CONCURRENT = 4              # Eşzamanlı sekme sayısı

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
    "Referer": "https://cdnlivetv.tv/",
    "Origin": "https://cdnlivetv.tv",
}

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--mute-audio",
    "--ignore-certificate-errors",
    "--ignore-ssl-errors",
    "--disable-extensions",
    "--disable-background-networking",
    "--hide-scrollbars",
    "--autoplay-policy=no-user-gesture-required",
    "--disable-blink-features=AutomationControlled",
]

BLOCKED_RESOURCE_TYPES = {"image", "media", "font"}

# ──────────────────────────────────────────────────────────────────────────────


def is_valid_stream_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False

    url = url.strip()

    if not (url.startswith("http://") or url.startswith("https://")):
        return False

    invalid_chars = [
        " ", "{", "}", "<", ">", '"', "'", "`", ";", "(", ")",
        "\\", "\n", "\r", "\t", "&&", "||", "import", "function"
    ]
    if any(c in url for c in invalid_chars):
        return False

    junk_keywords = ["parser", "bundle", "webpack", "chunk", "worker", "player.min"]
    url_lower = url.lower()
    if any(k in url_lower for k in junk_keywords):
        return False

    base_path = url.split("?")[0].lower()
    if not (".m3u8" in base_path or ".mpd" in base_path):
        return False

    return True


def sanitize_filename(name: str) -> str:
    """Dosya adlarında hata yaratabilecek geçersiz karakterleri temizler."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def extract_from_html(html_text: str, base_url: str = "") -> str:
    if not html_text:
        return ""

    html_text = html_text.replace("\\/", "/").replace("\\u0026", "&")

    pattern = r'https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&*+,;=%]+\.(?:m3u8|mpd)(?:\?[a-zA-Z0-9\-._~:/?#\[\]@!$&*+,;=%]*)?'

    matches = re.findall(pattern, html_text, re.IGNORECASE)
    for m in matches:
        if is_valid_stream_url(m):
            return m

    return ""


async def extract_from_js(page) -> str:
    try:
        val = await page.evaluate("""
            () => {
                try {
                    if (typeof jwplayer !== 'undefined' && jwplayer().getPlaylistItem) {
                        const f = jwplayer().getPlaylistItem()?.file;
                        if (f && typeof f === 'string' && f.startsWith('http')) return f;
                    }
                } catch(e){}

                try {
                    if (typeof videojs !== 'undefined') {
                        const players = videojs.getAllPlayers();
                        for (let p of players) {
                            const src = p.currentSrc ? p.currentSrc() : (p.src ? p.src() : null);
                            if (src && typeof src === 'string' && src.startsWith('http')) return src;
                        }
                    }
                } catch(e){}

                try {
                    if (typeof Hls !== 'undefined' && Hls.url && Hls.url.startsWith('http')) return Hls.url;
                } catch(e){}

                const v = document.querySelector('video');
                if (v && v.src && v.src.startsWith('http')) return v.src;

                const s = document.querySelector('video source');
                if (s && s.src && s.src.startsWith('http')) return s.src;

                return null;
            }
        """)
        if val and is_valid_stream_url(val):
            return val
    except Exception:
        pass

    return ""


async def try_trigger_play(page):
    try:
        await page.mouse.click(200, 200)
    except Exception:
        pass

    try:
        await page.evaluate("""
            () => {
                document.querySelectorAll('video').forEach(v => {
                    try { v.muted = true; v.play(); } catch(e) {}
                });
                const btns = document.querySelectorAll(
                    '.jw-icon-display, .vjs-big-play-button, button[aria-label*="play" i], .play-button, #play'
                );
                btns.forEach(b => { try { b.click(); } catch(e) {} });
            }
        """)
    except Exception:
        pass


async def get_stream_url(browser, player_url: str, channel_name: str) -> str:
    stream_url = ""
    found_event = asyncio.Event()

    if not browser.is_connected():
        return ""

    context = None
    page = None

    try:
        context = await browser.new_context(
            user_agent=HEADERS["User-Agent"],
            extra_http_headers={
                "Accept-Language": HEADERS["Accept-Language"],
                "Referer": HEADERS["Referer"],
            },
            bypass_csp=True,
            ignore_https_errors=True,
            viewport={"width": 1280, "height": 720},
        )

        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )

        page = await context.new_page()

        async def route_filter(route):
            req = route.request
            if is_valid_stream_url(req.url):
                await route.continue_()
            elif req.resource_type in BLOCKED_RESOURCE_TYPES:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", route_filter)

        async def on_request(request):
            nonlocal stream_url
            url = request.url
            if not stream_url and is_valid_stream_url(url):
                stream_url = url
                found_event.set()

        async def on_response(response):
            nonlocal stream_url
            if stream_url:
                return

            url = response.url
            if is_valid_stream_url(url):
                stream_url = url
                found_event.set()
                return

            ct = response.headers.get("content-type", "").lower()
            if "application/json" in ct:
                try:
                    text = await response.text()
                    if ".m3u8" in text or ".mpd" in text:
                        found = extract_from_html(text, url)
                        if found and is_valid_stream_url(found):
                            stream_url = found
                            found_event.set()
                except Exception:
                    pass

        page.on("request", on_request)
        page.on("response", on_response)

        try:
            await page.goto(player_url, timeout=TIMEOUT, wait_until="domcontentloaded")
        except Exception:
            pass

        try:
            await asyncio.wait_for(found_event.wait(), timeout=FIRST_WAIT)
        except asyncio.TimeoutError:
            pass

        if not stream_url:
            await try_trigger_play(page)
            try:
                await page.reload(timeout=TIMEOUT, wait_until="domcontentloaded")
                await try_trigger_play(page)
                await asyncio.wait_for(found_event.wait(), timeout=RELOAD_WAIT)
            except Exception:
                pass

        if not stream_url:
            stream_url = await extract_from_js(page)

        if not stream_url:
            try:
                content = await page.content()
                found = extract_from_html(content, player_url)
                if is_valid_stream_url(found):
                    stream_url = found
            except Exception:
                pass

        if not stream_url:
            try:
                for frame in page.frames:
                    if frame.url and frame.url != player_url:
                        try:
                            fc = await frame.content()
                            found = extract_from_html(fc, frame.url)
                            if is_valid_stream_url(found):
                                stream_url = found
                                break
                        except Exception:
                            pass
            except Exception:
                pass

    except Exception:
        pass
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass

    return stream_url if is_valid_stream_url(stream_url) else ""


async def process_all(channels: list) -> tuple:
    success = []
    failed = []
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    total = len(channels)
    done_count = 0
    lock = asyncio.Lock()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=BROWSER_ARGS,
        )

        async def handle(ch):
            nonlocal done_count

            name = str(ch.get("name", "?")).strip()
            player_url = str(ch.get("url", "")).strip()
            image = str(ch.get("image", "")).strip()
            group = str(ch.get("group", "GENEL")).strip().upper()

            if not player_url:
                async with lock:
                    done_count += 1
                    failed.append({
                        "name": name, "player_url": "", "image": image,
                        "group": group, "reason": "URL yok"
                    })
                return

            async with semaphore:
                stream_url = await get_stream_url(browser, player_url, name)

            async with lock:
                done_count += 1
                prefix = f"[{done_count:03d}/{total}]"

                if stream_url and is_valid_stream_url(stream_url):
                    print(f"  ✅ {prefix} {name} → {stream_url[:65]}...")
                    success.append({
                        "name": name,
                        "stream_url": stream_url,
                        "player_url": player_url,
                        "image": image,
                        "group": group,
                    })
                else:
                    print(f"  ❌ {prefix} {name} (Başarısız / Token Alınamadı)")
                    failed.append({
                        "name": name,
                        "player_url": player_url,
                        "image": image,
                        "group": group,
                        "reason": "Geçerli stream URL bulunamadı",
                    })

        await asyncio.gather(*[handle(ch) for ch in channels], return_exceptions=True)

        try:
            await browser.close()
        except Exception:
            pass

    return success, failed


def write_individual_m3u8(items: list, output_dir_name: str, bandwidth: int = 8000000):
    """Bulunan her kanal için cdnlive klasörü altında istenen formatta .m3u8 dosyası oluşturur."""
    base_path = Path(__file__).parent.resolve()
    target_dir = base_path / output_dir_name
    
    # Klasörü oluştur
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📂 Yazma İşlemi Başlatıldı (Klasör: {target_dir})")

    if not items:
        print("   ⚠️ Yazılacak başarılı kanal bulunamadı.")
        return

    for ch in items:
        name = ch["name"]
        stream = ch["stream_url"]

        # Dosya adı için geçersiz karakterleri temizle
        safe_name = sanitize_filename(name)
        file_path = target_dir / f"{safe_name}.m3u8"

        # İstenen formatta M3U8 dosyasını yaz:
        # #EXTM3U
        # #EXT-X-VERSION:3
        # #EXT-X-STREAM-INF:BANDWIDTH=8000000
        # Yayın linki
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write("#EXT-X-VERSION:3\n")
                f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bandwidth}\n")
                f.write(f"{stream}\n")
            print(f"   💾 Yazıldı: {file_path.name}")
        except Exception as e:
            print(f"   ❌ Dosya yazma hatası ({name}): {e}")


def print_report(channels: list, success: list, failed: list):
    turkey_tz = timezone(timedelta(hours=3))
    now = datetime.now(turkey_tz).strftime("%d.%m.%Y %H:%M:%S")

    print(f"\n{'═'*65}")
    print(f"📊 SONUÇ RAPORU")
    print(f"{'═'*65}")
    print(f"  📺 Girilen kanal sayısı  : {len(channels)}")
    print(f"  ✅ Başarıyla çözülen     : {len(success)}")
    print(f"  ❌ Başarısız olan        : {len(failed)}")
    print(f"  📁 Çıktı Klasör Yolu     : ./{OUTPUT_DIR_NAME}/")
    print(f"  🕐 Güncelleme zamanı     : {now}")
    print(f"{'═'*65}\n")


async def main():
    print("═" * 65)
    print("   📺 ÖZEL LİSTE — ÇOKLU KANAL AYRI DOSYA KAYDEDİCİ")
    print("═" * 65 + "\n")

    if not KANALLAR:
        print("⚠️  Lütfen 'KANALLAR' listesine en az bir kanal ekleyin.")
        return

    print(f"📋 İşlenecek kanal sayısı: {len(KANALLAR)}")
    print(f"⚡ Eşzamanlı Sekme       : {MAX_CONCURRENT}")
    print(f"📁 Klasör Hedefi         : ./{OUTPUT_DIR_NAME}/\n")

    success, failed = await process_all(KANALLAR)

    # Kanalları ayrı dosyalar halinde yazdır
    write_individual_m3u8(success, OUTPUT_DIR_NAME)

    with open(DEBUG_FILE, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print_report(KANALLAR, success, failed)
    print(f"✅ Başarıyla tamamlandı! Çalışan kanallar './{OUTPUT_DIR_NAME}/' klasörüne kaydedildi.\n")


if __name__ == "__main__":
    asyncio.run(main())
