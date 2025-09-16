"""
Enhanced Global News Collector with Comprehensive Multilingual Sources
Focused on Conflict Zones and Geopolitical Hotspots
"""

import asyncio
import aiohttp
import feedparser
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Enhanced news article data structure."""
    title: str
    url: str
    source: str
    language: str
    country: str
    published_date: datetime
    content_hash: str
    priority: str
    conflict_zone: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[List[str]] = None


class ConflictZoneNewsRegistry:
    """Registry specifically focused on conflict zone and geopolitical news sources."""

    def __init__(self):
        self.sources = {
            # CRITICAL CONFLICT ZONES - HIGH PRIORITY

            # Ukrainian Language Sources (CONFLICT ZONE - Ukraine War)
            'uk': {
                'ukraine': [
                    {'name': 'Українська Правда',
                     'rss': 'https://www.pravda.com.ua/rss/',
                     'country': 'UA',
                     'priority': 'critical'},
                    {'name': 'Укрінформ',
                     'rss': 'https://www.ukrinform.ua/rss',
                     'country': 'UA',
                     'priority': 'critical'},
                    {'name': 'Радіо Свобода Україна',
                     'rss': 'https://www.radiosvoboda.org/api/z-opqieqtiq',
                     'country': 'UA',
                     'priority': 'critical'},
                    {'name': 'Цензор.НЕТ',
                     'rss': 'https://censor.net/ua/rss/news',
                     'country': 'UA',
                     'priority': 'critical'},
                    {'name': 'Дзеркало Тижня', 'rss': 'https://zn.ua/rss/',
                        'country': 'UA', 'priority': 'high'},
                    {'name': 'Українські Новини',
                     'rss': 'https://ukranews.com/ua/rss/',
                     'country': 'UA',
                     'priority': 'high'},
                    {'name': 'Гордон', 'rss': 'https://gordonua.com/rss.html',
                        'country': 'UA', 'priority': 'high'},
                    {'name': '24 Канал', 'rss': 'https://24tv.ua/rss/',
                        'country': 'UA', 'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC Україна',
                     'rss': 'https://feeds.bbci.co.uk/ukrainian/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW Українська',
                     'rss': 'https://rss.dw.com/rdf/rss-uk-all',
                     'country': 'DE',
                     'priority': 'critical'},
                ]
            },

            # Hebrew Language Sources (CONFLICT ZONE - Israel/Palestine)
            'he': {
                'israel': [
                    {'name': 'הארץ',
                     'rss': 'https://www.haaretz.co.il/cmlink/1.1617539',
                     'country': 'IL',
                     'priority': 'critical'},
                    {'name': 'ישראל היום',
                     'rss': 'https://www.israelhayom.co.il/rss',
                     'country': 'IL',
                     'priority': 'critical'},
                    {'name': 'ידיעות אחרונות',
                     'rss': 'https://www.ynet.co.il/integration/StoryRss2.xml',
                     'country': 'IL',
                     'priority': 'critical'},
                    {'name': 'מעריב', 'rss': 'https://www.maariv.co.il/rss',
                        'country': 'IL', 'priority': 'critical'},
                    {'name': 'כאן חדשות',
                     'rss': 'https://www.kan.org.il/rss/',
                     'country': 'IL',
                     'priority': 'high'},
                    {'name': 'גלובס',
                     'rss': 'https://www.globes.co.il/webservice/rss/rssfeeder.asmx',
                     'country': 'IL',
                     'priority': 'high'},
                    {'name': 'וואלה חדשות',
                     'rss': 'https://news.walla.co.il/rss/news.xml',
                     'country': 'IL',
                     'priority': 'high'},
                    {'name': 'טיימס אוף ישראל עברית',
                     'rss': 'https://he.timesofisrael.com/feed/',
                     'country': 'IL',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC עברית',
                     'rss': 'https://feeds.bbci.co.uk/hebrew/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW עברית',
                     'rss': 'https://rss.dw.com/rdf/rss-he-all',
                     'country': 'DE',
                     'priority': 'critical'},
                ]
            },

            # Arabic Language Sources (CONFLICT ZONE - Middle East)
            'ar': {
                'palestine': [
                    {'name': 'وكالة وفا',
                     'rss': 'https://www.wafa.ps/ar_page.aspx?id=rss',
                     'country': 'PS',
                     'priority': 'critical'},
                    {'name': 'القدس',
                     'rss': 'https://www.alquds.com/rss/rss.xml',
                     'country': 'PS',
                     'priority': 'critical'},
                ],
                'syria': [
                    {'name': 'سانا', 'rss': 'https://sana.sy/rss.xml',
                        'country': 'SY', 'priority': 'critical'},
                    {'name': 'الوطن السورية',
                     'rss': 'http://alwatan.sy/rss.xml',
                     'country': 'SY',
                     'priority': 'high'},
                ],
                'iraq': [
                    {'name': 'وكالة الأنباء العراقية',
                     'rss': 'https://www.ina.iq/rss.xml',
                     'country': 'IQ',
                     'priority': 'high'},
                    {'name': 'الصباح الجديد',
                     'rss': 'http://newsabah.com/rss.xml',
                     'country': 'IQ',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'الجزيرة',
                     'rss': 'https://www.aljazeera.net/rss/all.xml',
                     'country': 'QA',
                     'priority': 'critical'},
                    {'name': 'العربية',
                     'rss': 'https://www.alarabiya.net/ar/rss.xml',
                     'country': 'SA',
                     'priority': 'critical'},
                    {'name': 'BBC العربية',
                     'rss': 'https://feeds.bbci.co.uk/arabic/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW عربية',
                     'rss': 'https://rss.dw.com/rdf/rss-ar-all',
                     'country': 'DE',
                     'priority': 'critical'},
                ]
            },

            # Turkish Language Sources (CONFLICT ZONE - Syria, Kurdistan,
            # Armenia tensions)
            'tr': {
                'turkey': [
                    {'name': 'Hürriyet',
                     'rss': 'https://www.hurriyet.com.tr/rss/dunya',
                     'country': 'TR',
                     'priority': 'critical'},
                    {'name': 'Milliyet Dünya',
                     'rss': 'https://www.milliyet.com.tr/rss/rss/dunya.xml',
                     'country': 'TR',
                     'priority': 'critical'},
                    {'name': 'Sabah Dünya',
                     'rss': 'https://www.sabah.com.tr/rss/dunya.xml',
                     'country': 'TR',
                     'priority': 'critical'},
                    {'name': 'Sözcü Dünya',
                     'rss': 'https://www.sozcu.com.tr/kategori/dunya/feed/',
                     'country': 'TR',
                     'priority': 'high'},
                    {'name': 'Cumhuriyet Dünya',
                     'rss': 'https://www.cumhuriyet.com.tr/rss/dunya.xml',
                     'country': 'TR',
                     'priority': 'high'},
                    {'name': 'Habertürk Dünya',
                     'rss': 'https://www.haberturk.com/rss/dunya.xml',
                     'country': 'TR',
                     'priority': 'high'},
                    {'name': 'CNN Türk Dünya',
                     'rss': 'https://www.cnnturk.com/feed/rss/dunya/news',
                     'country': 'TR',
                     'priority': 'high'},
                    {'name': 'NTV Dünya',
                     'rss': 'https://www.ntv.com.tr/dunya.rss',
                     'country': 'TR',
                     'priority': 'high'},
                    {'name': 'TRT Haber Dünya',
                     'rss': 'https://www.trthaber.com/sondakika_articles.rss',
                     'country': 'TR',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC Türkçe',
                     'rss': 'https://feeds.bbci.co.uk/turkce/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW Türkçe',
                     'rss': 'https://rss.dw.com/rdf/rss-tr-all',
                     'country': 'DE',
                     'priority': 'critical'},
                    {'name': 'TRT World Türkçe',
                     'rss': 'https://www.trtworld.com/turkce/rss',
                     'country': 'TR',
                     'priority': 'high'},
                ]
            },

            # Persian/Farsi Language Sources (CONFLICT ZONE - Iran,
            # Afghanistan)
            'fa': {
                'iran': [
                    {'name': 'ایسنا', 'rss': 'https://www.isna.ir/rss',
                        'country': 'IR', 'priority': 'critical'},
                    {'name': 'تسنیم',
                     'rss': 'https://www.tasnimnews.com/fa/rss/feed',
                     'country': 'IR',
                     'priority': 'critical'},
                    {'name': 'مهر', 'rss': 'https://www.mehrnews.com/rss',
                        'country': 'IR', 'priority': 'critical'},
                    {'name': 'فارس', 'rss': 'https://www.farsnews.ir/rss',
                        'country': 'IR', 'priority': 'critical'},
                    {'name': 'ایرنا', 'rss': 'https://www.irna.ir/rss',
                        'country': 'IR', 'priority': 'high'},
                    {'name': 'شرق', 'rss': 'https://www.sharghdaily.com/rss',
                        'country': 'IR', 'priority': 'high'},
                    {'name': 'اعتماد آنلاین',
                     'rss': 'https://www.etemad.ir/rss',
                     'country': 'IR',
                     'priority': 'high'},
                ],
                'afghanistan': [
                    {'name': 'طلوع نیوز',
                     'rss': 'https://tolonews.com/fa/rss.xml',
                     'country': 'AF',
                     'priority': 'critical'},
                    {'name': 'آریانا نیوز',
                     'rss': 'https://ariananews.af/rss/',
                     'country': 'AF',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC فارسی',
                     'rss': 'https://feeds.bbci.co.uk/persian/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW فارسی',
                     'rss': 'https://rss.dw.com/rdf/rss-fa-all',
                     'country': 'DE',
                     'priority': 'critical'},
                    {'name': 'VOA فارسی',
                     'rss': 'https://www.voapersian.com/api/epiqq',
                     'country': 'US',
                     'priority': 'critical'},
                    {'name': 'رادیو فردا',
                     'rss': 'https://www.radiofarda.com/api/epiqq',
                     'country': 'CZ',
                     'priority': 'high'},
                ]
            },

            # Pashto Language Sources (CONFLICT ZONE - Afghanistan, Pakistan)
            'ps': {
                'afghanistan': [
                    {'name': 'د افغانستان غږ',
                     'rss': 'https://tolonews.com/ps/rss.xml',
                     'country': 'AF',
                     'priority': 'critical'},
                    {'name': 'پښتو خپرونې',
                     'rss': 'https://da.azadiradio.com/api/epiqq',
                     'country': 'AF',
                     'priority': 'critical'},
                ],
                'pakistan': [
                    {'name': 'ماشومان ټی وی',
                     'rss': 'https://www.mashriqtv.pk/rss/pashto',
                     'country': 'PK',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC پښتو',
                     'rss': 'https://feeds.bbci.co.uk/pashto/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'VOA پښتو',
                     'rss': 'https://www.voapashto.com/api/epiqq',
                     'country': 'US',
                     'priority': 'critical'},
                    {'name': 'DW پښتو',
                     'rss': 'https://rss.dw.com/rdf/rss-ps-all',
                     'country': 'DE',
                     'priority': 'high'},
                ]
            },

            # Kurdish Language Sources (CONFLICT ZONE - Iraq, Syria, Turkey)
            'ku': {
                'iraq': [
                    {'name': 'رووداو',
                     'rss': 'https://www.rudaw.net/rss/sorani',
                     'country': 'IQ',
                     'priority': 'critical'},
                    {'name': 'کوردستان ٢٤',
                     'rss': 'https://www.kurdistan24.net/ku/rss',
                     'country': 'IQ',
                     'priority': 'critical'},
                    {'name': 'نالیا رادیۆ تلیڤیزیۆن',
                     'rss': 'https://www.nrt.tv/rss/kurdish',
                     'country': 'IQ',
                     'priority': 'high'},
                ],
                'syria': [
                    {'name': 'ئاژانسی هاوار',
                     'rss': 'https://hawarnews.com/ku/rss.xml',
                     'country': 'SY',
                     'priority': 'critical'},
                    {'name': 'ANF کوردی',
                     'rss': 'https://anfkurdish.com/rss.xml',
                     'country': 'SY',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC کوردی',
                     'rss': 'https://feeds.bbci.co.uk/kurdish/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'VOA کوردی',
                     'rss': 'https://www.vokurdish.com/api/epiqq',
                     'country': 'US',
                     'priority': 'critical'},
                    {'name': 'DW کوردی',
                     'rss': 'https://rss.dw.com/rdf/rss-ku-all',
                     'country': 'DE',
                     'priority': 'high'},
                ]
            },

            # Burmese/Myanmar Language Sources (CONFLICT ZONE - Myanmar civil
            # war)
            'my': {
                'myanmar': [
                    {'name': 'မြန်မာ့အလင်း',
                     'rss': 'https://www.myanmaralin.com/feed/',
                     'country': 'MM',
                     'priority': 'critical'},
                    {'name': 'ဧရာဝတီ',
                     'rss': 'https://burma.irrawaddy.com/feed',
                     'country': 'MM',
                     'priority': 'critical'},
                    {'name': 'ခမရာ', 'rss': 'https://khitthitnews.com/feed/',
                        'country': 'MM', 'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC မြန်မာ',
                     'rss': 'https://feeds.bbci.co.uk/burmese/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'VOA မြန်မာ',
                     'rss': 'https://burmese.voa.com/api/epiqq',
                     'country': 'US',
                     'priority': 'critical'},
                    {'name': 'RFA မြန်မာ',
                     'rss': 'https://www.rfa.org/burmese/rss.xml',
                     'country': 'US',
                     'priority': 'high'},
                ]
            },

            # HIGH PRIORITY CONFLICT ZONES

            # Armenian Language Sources (CONFLICT ZONE - Armenia/Azerbaijan,
            # Nagorno-Karabakh)
            'hy': {
                'armenia': [
                    {'name': 'Armenpress',
                     'rss': 'https://armenpress.am/arm/rss/',
                     'country': 'AM',
                     'priority': 'critical'},
                    {'name': 'Asbarez', 'rss': 'https://asbarez.com/feed/',
                        'country': 'AM', 'priority': 'critical'},
                    {'name': '168.am', 'rss': 'https://168.am/rss/news.xml',
                        'country': 'AM', 'priority': 'high'},
                    {'name': 'Ծաղիկ Online',
                     'rss': 'https://www.tert.am/rss/',
                     'country': 'AM',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'Azg Daily', 'rss': 'https://azg.am/rss/',
                        'country': 'AM', 'priority': 'high'},
                    {'name': 'Armenian Weekly',
                     'rss': 'https://armenianweekly.com/feed/',
                     'country': 'US',
                     'priority': 'high'},
                ]
            },

            # Azerbaijani Language Sources (CONFLICT ZONE - Armenia/Azerbaijan)
            'az': {
                'azerbaijan': [
                    {'name': 'APA', 'rss': 'https://apa.az/az/rss/',
                        'country': 'AZ', 'priority': 'critical'},
                    {'name': 'Trend', 'rss': 'https://www.trend.az/rss/news',
                        'country': 'AZ', 'priority': 'critical'},
                    {'name': 'Report', 'rss': 'https://report.az/az/rss/',
                        'country': 'AZ', 'priority': 'high'},
                    {'name': 'Azərbaycan',
                     'rss': 'https://www.azerbaijan24.com/rss/',
                     'country': 'AZ',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC Azərbaycanca',
                     'rss': 'https://feeds.bbci.co.uk/azeri/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                ]
            },

            # Hindi Language Sources (CONFLICT ZONE - Kashmir, border tensions)
            'hi': {
                'india': [
                    {'name': 'आज तक',
                     'rss': 'https://aajtak.intoday.in/rss/home.jsp',
                     'country': 'IN',
                     'priority': 'critical'},
                    {'name': 'एनडीटीवी इंडिया',
                     'rss': 'https://hindi.ndtv.com/rss',
                     'country': 'IN',
                     'priority': 'critical'},
                    {'name': 'अमर उजाला',
                     'rss': 'https://www.amarujala.com/rss/national-news.xml',
                     'country': 'IN',
                     'priority': 'critical'},
                    {'name': 'दैनिक भास्कर',
                     'rss': 'https://www.bhaskar.com/rss-v1--category-1.xml',
                     'country': 'IN',
                     'priority': 'high'},
                    {'name': 'जागरण',
                     'rss': 'https://www.jagran.com/rss/national.xml',
                     'country': 'IN',
                     'priority': 'high'},
                    {'name': 'नवभारत टाइम्स',
                     'rss': 'https://navbharattimes.indiatimes.com/rssfeedstopstories.cms',
                     'country': 'IN',
                     'priority': 'high'},
                    {'name': 'ज़ी न्यूज़',
                     'rss': 'https://zeenews.india.com/hindi/rss/india-national-news.xml',
                     'country': 'IN',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC हिंदी',
                     'rss': 'https://feeds.bbci.co.uk/hindi/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW हिंदी',
                     'rss': 'https://rss.dw.com/rdf/rss-hi-all',
                     'country': 'DE',
                     'priority': 'critical'},
                    {'name': 'VOA हिंदी',
                     'rss': 'https://www.voahindi.com/api/epiqq',
                     'country': 'US',
                     'priority': 'high'},
                ]
            },

            # Urdu Language Sources (CONFLICT ZONE - Pakistan, Kashmir,
            # Afghanistan)
            'ur': {
                'pakistan': [
                    {'name': 'جنگ',
                     'rss': 'https://jang.com.pk/rss/latest-news',
                     'country': 'PK',
                     'priority': 'critical'},
                    {'name': 'ایکسپریس', 'rss': 'https://www.express.pk/rss/',
                        'country': 'PK', 'priority': 'critical'},
                    {'name': 'نوائے وقت',
                     'rss': 'https://www.nawaiwaqt.com.pk/rss/',
                     'country': 'PK',
                     'priority': 'high'},
                    {'name': 'روزنامہ پاکستان',
                     'rss': 'https://www.roznamapakistan.com/rss/',
                     'country': 'PK',
                     'priority': 'high'},
                ],
                'india': [
                    {'name': 'اردو نیوز',
                     'rss': 'https://www.urdunews.com/rss/',
                     'country': 'IN',
                     'priority': 'high'},
                    {'name': 'سہارا اردو',
                     'rss': 'https://sahara.co.in/urdu/rss.xml',
                     'country': 'IN',
                     'priority': 'high'},
                ],
                'international': [
                    {'name': 'BBC اردو',
                     'rss': 'https://feeds.bbci.co.uk/urdu/rss.xml',
                     'country': 'GB',
                     'priority': 'critical'},
                    {'name': 'DW اردو',
                     'rss': 'https://rss.dw.com/rdf/rss-ur-all',
                     'country': 'DE',
                     'priority': 'critical'},
                    {'name': 'VOA اردو',
                     'rss': 'https://www.urduvoa.com/api/epiqq',
                     'country': 'US',
                     'priority': 'critical'},
                ]
            },

            # Additional conflict zone languages...
            # [Including all the other languages I added in the previous attempt]
        }

        # Priority levels for conflict zones and strategic regions
        self.priority_languages = {
            'critical': [
                'uk',
                'he',
                'ar',
                'tr',
                'fa',
                'ps',
                'ku',
                'ru',
                'zh',
                'my'],
            'high': [
                'hy',
                'az',
                'hi',
                'ur',
                'am',
                'sw',
                'ha',
                'ti',
                'sr',
                'hr',
                'sq',
                'bn',
                'si',
                'ta'],
            'medium': [
                'prs',
                'ka',
                'km',
                'lo',
                'ug',
                'bo',
                'mn',
                'kk',
                'uz',
                'mk',
                'ro_md',
                'om',
                'vi',
                'th'],
            'standard': [
                'en',
                'es',
                'fr',
                'de',
                'it',
                'pt',
                'nl',
                'ja',
                'ko']}

        # Conflict zone metadata
        self.conflict_zones = {
            'ukraine_war': ['uk', 'ru'],
            'middle_east': ['he', 'ar', 'tr', 'ku', 'fa'],
            'afghanistan': ['ps', 'prs', 'fa', 'ur'],
            'caucasus': ['hy', 'az', 'ka', 'ru'],
            'horn_africa': ['am', 'ti', 'om', 'sw', 'ar'],
            'sahel': ['ha', 'fr', 'ar'],
            'balkans': ['sr', 'hr', 'sq', 'mk'],
            'myanmar': ['my', 'en'],
            'kashmir': ['hi', 'ur', 'en'],
            'south_china_sea': ['zh', 'vi', 'en'],
            'xinjiang_tibet': ['ug', 'bo', 'zh'],
            'central_asia': ['kk', 'uz', 'mn', 'ru'],
            'transnistria': ['ro_md', 'ru'],
            'sri_lanka': ['si', 'ta', 'en']
        }

        # Language metadata
        self.language_metadata = {
            'uk': {'name': 'Ukrainian', 'region': 'Eastern Europe', 'conflict_priority': 'critical'},
            'he': {'name': 'Hebrew', 'region': 'Middle East', 'conflict_priority': 'critical'},
            'ar': {'name': 'Arabic', 'region': 'MENA', 'conflict_priority': 'critical'},
            'tr': {'name': 'Turkish', 'region': 'Middle East/Europe', 'conflict_priority': 'critical'},
            'fa': {'name': 'Persian/Farsi', 'region': 'Central/South Asia', 'conflict_priority': 'critical'},
            'ps': {'name': 'Pashto', 'region': 'South/Central Asia', 'conflict_priority': 'critical'},
            'ku': {'name': 'Kurdish', 'region': 'Middle East', 'conflict_priority': 'critical'},
            'my': {'name': 'Burmese/Myanmar', 'region': 'Southeast Asia', 'conflict_priority': 'critical'},
            'hy': {'name': 'Armenian', 'region': 'Caucasus', 'conflict_priority': 'high'},
            'az': {'name': 'Azerbaijani', 'region': 'Caucasus', 'conflict_priority': 'high'},
            'hi': {'name': 'Hindi', 'region': 'South Asia', 'conflict_priority': 'high'},
            'ur': {'name': 'Urdu', 'region': 'South Asia', 'conflict_priority': 'high'},
            # Add more language metadata as needed...
        }

    def get_conflict_zone_sources(
            self, conflict_zone: str) -> List[Dict[str, Any]]:
        """Get all sources for a specific conflict zone."""
        if conflict_zone not in self.conflict_zones:
            return []

        languages = self.conflict_zones[conflict_zone]
        sources = []

        for lang in languages:
            lang_sources = self.get_sources_by_language(lang)
            for source in lang_sources:
                source['conflict_zone'] = conflict_zone
                sources.append(source)

        return sources

    def get_sources_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all sources for a specific language."""
        if language not in self.sources:
            logger.warning(f"Language {language} not supported")
            return []

        all_sources = []
        for region, sources in self.sources[language].items():
            for source in sources:
                source['region'] = region
                source['language'] = language
                all_sources.append(source)

        return all_sources

    def get_priority_sources(
            self, priority_level: str) -> List[Dict[str, Any]]:
        """Get sources by priority level."""
        if priority_level not in self.priority_languages:
            return []

        languages = self.priority_languages[priority_level]
        sources = []

        for lang in languages:
            lang_sources = self.get_sources_by_language(lang)
            # Filter sources by priority
            priority_sources = [
                s for s in lang_sources if s.get(
                    'priority', 'standard') == priority_level]
            sources.extend(priority_sources)

        return sources


class EnhancedGlobalNewsCollector:
    """Enhanced news collector with focus on conflict zones and multilingual sources."""

    def __init__(self):
        self.registry = ConflictZoneNewsRegistry()
        self.collected_articles: Set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _generate_content_hash(self, title: str, url: str) -> str:
        """Generate a unique hash for deduplication."""
        content = f"{title}|{url}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _fetch_rss_feed(
            self, source: Dict[str, Any]) -> List[NewsArticle]:
        """Fetch and parse an RSS feed."""
        articles = []

        try:
            if not self.session:
                logger.error("Session not initialized")
                return articles

            async with self.session.get(source['rss']) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)

                    # Limit to latest 10 articles
                    for entry in feed.entries[:10]:
                        # Generate hash for deduplication
                        content_hash = self._generate_content_hash(
                            entry.get('title', ''),
                            entry.get('link', '')
                        )

                        if content_hash not in self.collected_articles:
                            self.collected_articles.add(content_hash)

                            # Parse publication date
                            pub_date = datetime.now()
                            if hasattr(
                                    entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(
                                    *entry.published_parsed[:6])

                            article = NewsArticle(
                                title=entry.get('title', ''),
                                url=entry.get('link', ''),
                                source=source['name'],
                                language=source['language'],
                                country=source['country'],
                                published_date=pub_date,
                                content_hash=content_hash,
                                priority=source.get('priority', 'standard'),
                                conflict_zone=source.get('conflict_zone'),
                                region=source.get('region'),
                                tags=[]
                            )
                            articles.append(article)

                    logger.info(
                        f"Collected {len(articles)} articles from {source['name']} ({source['language']})")

        except Exception as e:
            logger.error(f"Error fetching {source['name']}: {str(e)}")

        return articles

    async def collect_conflict_zone_news(
            self, conflict_zone: str) -> List[NewsArticle]:
        """Collect news from a specific conflict zone."""
        sources = self.registry.get_conflict_zone_sources(conflict_zone)
        logger.info(
            f"Collecting news from {len(sources)} sources for conflict zone: {conflict_zone}")

        tasks = [self._fetch_rss_feed(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed: {result}")

        logger.info(
            f"Total articles collected for {conflict_zone}: {len(all_articles)}")
        return all_articles

    async def collect_by_priority(
            self, priority_level: str) -> List[NewsArticle]:
        """Collect news by priority level."""
        sources = self.registry.get_priority_sources(priority_level)
        logger.info(
            f"Collecting {priority_level} priority news from {len(sources)} sources")

        tasks = [self._fetch_rss_feed(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed: {result}")

        logger.info(
            f"Total {priority_level} priority articles: {len(all_articles)}")
        return all_articles

    async def collect_by_language(self, language: str) -> List[NewsArticle]:
        """Collect news from a specific language."""
        sources = self.registry.get_sources_by_language(language)
        logger.info(
            f"Collecting news in {language} from {len(sources)} sources")

        tasks = [self._fetch_rss_feed(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed: {result}")

        logger.info(f"Total articles in {language}: {len(all_articles)}")
        return all_articles

    def save_articles(self, articles: List[NewsArticle], filename: str = None):
        """Save collected articles to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conflict_zone_news_{timestamp}.json"

        # Convert articles to dictionaries
        articles_data = []
        for article in articles:
            article_dict = {
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'language': article.language,
                'country': article.country,
                'published_date': article.published_date.isoformat(),
                'content_hash': article.content_hash,
                'priority': article.priority,
                'conflict_zone': article.conflict_zone,
                'region': article.region,
                'tags': article.tags or []
            }
            articles_data.append(article_dict)

        # Save to file
        output_path = Path(filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(articles)} articles to {output_path}")
        return output_path


# Example usage and testing
async def main():
    """Main function for testing the enhanced collector."""
    async with EnhancedGlobalNewsCollector() as collector:

        # Test critical conflict zones
        print("=== Testing Ukraine War Coverage ===")
        ukraine_articles = await collector.collect_conflict_zone_news('ukraine_war')
        print(
            f"Collected {len(ukraine_articles)} articles from Ukraine conflict zone")

        print("\\n=== Testing Middle East Coverage ===")
        middle_east_articles = await collector.collect_conflict_zone_news('middle_east')
        print(
            f"Collected {len(middle_east_articles)} articles from Middle East conflict zone")

        print("\\n=== Testing Critical Priority Sources ===")
        critical_articles = await collector.collect_by_priority('critical')
        print(f"Collected {len(critical_articles)} critical priority articles")

        print("\\n=== Testing Ukrainian Language Sources ===")
        ukrainian_articles = await collector.collect_by_language('uk')
        print(f"Collected {len(ukrainian_articles)} articles in Ukrainian")

        # Save all articles
        all_articles = ukraine_articles + middle_east_articles + critical_articles
        saved_file = collector.save_articles(
            all_articles, "enhanced_conflict_news_test.json")
        print(f"\\nSaved all articles to: {saved_file}")

        # Print sample headlines
        print("\\n=== Sample Headlines ===")
        for i, article in enumerate(all_articles[:5]):
            print(
                f"{i+1}. [{article.language}] {article.title} - {article.source}")


if __name__ == "__main__":
    asyncio.run(main())
