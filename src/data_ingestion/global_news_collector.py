"""
Global News Collector - Clases para recolección global de noticias
Proporciona compatibilidad con main.py y funcionalidad de recolección multilingüe
"""

import logging
import requests
import feedparser
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

try:
    from utils.config import config
except ImportError:
    # Fallback config
    class MockConfig:
        def get(self, key, default=None):
            return default
    config = MockConfig()


class GlobalNewsSourcesRegistry:
    """Registry of worldwide news sources organized by region and language."""

    def __init__(self):
        self.sources = {
            # Hebrew Language Sources - MIDDLE EAST CONFLICT
            'he': {
                'israel': [
                    {'name': 'ידיעות אחרונות',
                     'rss': 'https://www.ynet.co.il/Integration/StoryRss2.xml',
                     'country': 'IL'},
                    {'name': 'הארץ',
                     'rss': 'https://www.haaretz.co.il/news/politics/rss/',
                     'country': 'IL'},
                    {'name': 'מעריב',
                     'rss': 'https://www.maariv.co.il/rss/',
                     'country': 'IL'},
                    {'name': 'כלכליסט',
                     'rss': 'https://www.calcalist.co.il/GeneralRSS/GeneralRSS.aspx',
                     'country': 'IL'},
                    {
                        'name': 'גלובס',
                        'rss': 'https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=1725',
                        'country': 'IL'},
                    {'name': 'וואלה! חדשות',
                     'rss': 'https://news.walla.co.il/rss/news.xml',
                     'country': 'IL'},
                    {'name': 'הזמן הישראלי',
                     'rss': 'https://www.israelhayom.co.il/rss',
                     'country': 'IL'},
                ],
                'international': [
                    {'name': 'BBC בעברית',
                     'rss': 'https://feeds.bbci.co.uk/hebrew/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW בעברית',
                     'rss': 'https://rss.dw.com/rdf/rss-heb-all',
                     'country': 'DE'},
                    {'name': 'כאן חדשות',
                     'rss': 'https://www.kan.org.il/rss/',
                     'country': 'IL'},
                ]
            },
            # Turkish Language Sources - REGIONAL CONFLICTS
            'tr': {
                'turkey': [
                    {'name': 'Hürriyet Dünya',
                     'rss': 'https://www.hurriyet.com.tr/rss/dunya',
                     'country': 'TR'},
                    {'name': 'Milliyet Dünya',
                     'rss': 'https://www.milliyet.com.tr/rss/rssNew/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sabah Dünya',
                     'rss': 'https://www.sabah.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Cumhuriyet Dünya',
                     'rss': 'https://www.cumhuriyet.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sözcü Dünya',
                     'rss': 'https://www.sozcu.com.tr/kategori/dunya/feed/',
                     'country': 'TR'},
                    {'name': 'Yeni Şafak Dünya',
                     'rss': 'https://www.yenisafak.com/rss?xml=dunya',
                     'country': 'TR'},
                    {'name': 'Anadolu Ajansı',
                     'rss': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
                     'country': 'TR'},
                ],
                'international': [
                    {'name': 'BBC Türkçe',
                     'rss': 'https://feeds.bbci.co.uk/turkce/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW Türkçe',
                     'rss': 'https://rss.dw.com/rdf/rss-tur-all',
                     'country': 'DE'},
                    {'name': 'TRT Haber',
                     'rss': 'https://www.trthaber.com/sondakika_articles.rss',
                     'country': 'TR'},
                ]
            },
            # English Language Sources
            'en': {
                'international': [
                    {'name': 'BBC World',
                     'rss': 'http://feeds.bbci.co.uk/news/world/rss.xml',
                     'country': 'GB'},
                    {'name': 'CNN International',
                     'rss': 'http://rss.cnn.com/rss/edition.rss',
                     'country': 'US'},
                    {'name': 'Reuters World',
                     'rss': 'https://www.reuters.com/rssFeed/worldNews',
                     'country': 'GB'},
                    {'name': 'Associated Press',
                     'rss': 'https://feeds.washingtonpost.com/rss/world',
                     'country': 'US'},
                    {'name': 'Guardian International',
                     'rss': 'https://www.theguardian.com/world/rss',
                     'country': 'GB'},
                    {'name': 'Financial Times',
                     'rss': 'https://www.ft.com/world?format=rss',
                     'country': 'GB'},
                    {'name': 'The Economist',
                     'rss': 'https://www.economist.com/international/rss.xml',
                     'country': 'GB'},
                    {'name': 'Al Jazeera English',
                     'rss': 'https://www.aljazeera.com/xml/rss/all.xml',
                     'country': 'QA'},
                    {'name': 'Deutsche Welle English',
                     'rss': 'https://rss.dw.com/rdf/rss-en-all',
                     'country': 'DE'},
                    {'name': 'France24 English',
                     'rss': 'https://www.france24.com/en/rss',
                     'country': 'FR'},
                ],
                'usa': [
                    {'name': 'New York Times World',
                     'rss': 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
                     'country': 'US'},
                    {'name': 'Washington Post World',
                     'rss': 'https://feeds.washingtonpost.com/rss/world',
                     'country': 'US'},
                    {'name': 'Wall Street Journal',
                     'rss': 'https://feeds.a.dj.com/rss/RSSWorldNews.xml',
                     'country': 'US'},
                    {'name': 'NPR World',
                     'rss': 'https://feeds.npr.org/1004/rss.xml',
                     'country': 'US'},
                    {'name': 'CBS News World',
                     'rss': 'https://www.cbsnews.com/latest/rss/world',
                     'country': 'US'},
                    {'name': 'ABC News International',
                     'rss': 'https://abcnews.go.com/abcnews/internationalheadlines',
                     'country': 'US'},
                ],
                'uk': [
                    {'name': 'BBC UK',
                     'rss': 'http://feeds.bbci.co.uk/news/uk/rss.xml',
                     'country': 'GB'},
                    {'name': 'Sky News',
                     'rss': 'https://feeds.skynews.com/feeds/rss/world.xml',
                     'country': 'GB'},
                    {'name': 'Independent UK',
                     'rss': 'https://www.independent.co.uk/news/world/rss',
                     'country': 'GB'},
                    {'name': 'Telegraph World',
                     'rss': 'https://www.telegraph.co.uk/news/world/rss',
                     'country': 'GB'},
                ],
                'australia': [
                    {'name': 'ABC Australia',
                     'rss': 'https://www.abc.net.au/news/feed/51120/rss.xml',
                     'country': 'AU'},
                    {'name': 'Sydney Morning Herald',
                     'rss': 'https://www.smh.com.au/rss/world.xml',
                     'country': 'AU'},
                    {'name': 'The Australian',
                     'rss': 'https://www.theaustralian.com.au/news/world/rss',
                     'country': 'AU'},
                ],
                'canada': [
                    {'name': 'CBC News',
                     'rss': 'https://www.cbc.ca/cmlink/rss-world',
                     'country': 'CA'},
                    {'name': 'Globe and Mail',
                     'rss': 'https://www.theglobeandmail.com/world/rss/',
                     'country': 'CA'},
                ],
                'india': [
                    {'name': 'Times of India World',
                     'rss': 'https://timesofindia.indiatimes.com/rssfeeds/296589292.cms',
                     'country': 'IN'},
                    {'name': 'Hindu International',
                     'rss': 'https://www.thehindu.com/news/international/feeder/default.rss',
                     'country': 'IN'},
                    {'name': 'Indian Express World',
                     'rss': 'https://indianexpress.com/section/world/feed/',
                     'country': 'IN'},
                ],
                'south_africa': [
                    {'name': 'News24',
                     'rss': 'https://feeds.news24.com/articles/news24/TopStories/rss',
                     'country': 'ZA'},
                    {'name': 'Mail & Guardian',
                     'rss': 'https://mg.co.za/feed/',
                     'country': 'ZA'},
                ]
            },

            # Spanish Language Sources
            'es': {
                'spain': [
                    {
                        'name': 'El País Internacional',
                        'rss': 'https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada',
                        'country': 'ES'},
                    {'name': 'El Mundo Internacional',
                     'rss': 'https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml',
                     'country': 'ES'},
                    {'name': 'ABC España Internacional',
                     'rss': 'https://www.abc.es/rss/feeds/abc_Internacional.xml',
                     'country': 'ES'},
                    {'name': 'La Vanguardia Internacional',
                     'rss': 'https://www.lavanguardia.com/internacional/rss',
                     'country': 'ES'},
                    {'name': 'RTVE Noticias',
                     'rss': 'https://www.rtve.es/noticias/internacional/rss.xml',
                     'country': 'ES'},
                ],
                'mexico': [
                    {'name': 'El Universal México',
                     'rss': 'https://www.eluniversal.com.mx/rss.xml',
                     'country': 'MX'},
                    {'name': 'Reforma',
                     'rss': 'https://www.reforma.com/rss/portada.xml',
                     'country': 'MX'},
                    {'name': 'Milenio',
                     'rss': 'https://www.milenio.com/rss',
                     'country': 'MX'},
                    {'name': 'Excélsior',
                     'rss': 'https://www.excelsior.com.mx/rss.xml',
                     'country': 'MX'},
                ],
                'argentina': [
                    {'name': 'Clarín Internacional',
                     'rss': 'https://www.clarin.com/rss/mundo/',
                     'country': 'AR'},
                    {'name': 'La Nación Internacional',
                     'rss': 'https://www.lanacion.com.ar/mundo/rss',
                     'country': 'AR'},
                    {'name': 'Página 12',
                     'rss': 'https://www.pagina12.com.ar/rss/secciones/el-mundo/notas',
                     'country': 'AR'},
                ],
                'colombia': [
                    {'name': 'El Tiempo Internacional',
                     'rss': 'https://www.eltiempo.com/rss/mundo',
                     'country': 'CO'},
                    {'name': 'El Espectador Mundial',
                     'rss': 'https://www.elespectador.com/rss/mundo',
                     'country': 'CO'},
                    {'name': 'Semana Internacional',
                     'rss': 'https://www.semana.com/rss/internacional/',
                     'country': 'CO'},
                ],
                'chile': [
                    {'name': 'El Mercurio Internacional',
                     'rss': 'https://www.emol.com/rss/internacional.xml',
                     'country': 'CL'},
                    {'name': 'La Tercera Mundial',
                     'rss': 'https://www.latercera.com/feed/mundo/',
                     'country': 'CL'},
                ],
                'peru': [
                    {'name': 'El Comercio Mundo',
                     'rss': 'https://elcomercio.pe/rss/mundo/',
                     'country': 'PE'},
                    {'name': 'La República Internacional',
                     'rss': 'https://larepublica.pe/rss/internacional',
                     'country': 'PE'},
                ],
                'venezuela': [
                    {'name': 'El Nacional Internacional',
                     'rss': 'https://www.elnacional.com/rss/internacional/',
                     'country': 'VE'},
                ],
                'international': [
                    {'name': 'BBC Mundo',
                     'rss': 'https://feeds.bbci.co.uk/mundo/rss.xml',
                     'country': 'GB'},
                    {'name': 'CNN Español',
                     'rss': 'https://cnnespanol.cnn.com/feed/',
                     'country': 'US'},
                    {'name': 'DW Español',
                     'rss': 'https://rss.dw.com/rdf/rss-es-all',
                     'country': 'DE'},
                    {'name': 'France24 Español',
                     'rss': 'https://www.france24.com/es/rss',
                     'country': 'FR'},
                ]
            },

            # French Language Sources
            'fr': {
                'france': [
                    {'name': 'Le Monde International',
                     'rss': 'https://www.lemonde.fr/international/rss_full.xml',
                     'country': 'FR'},
                    {'name': 'Le Figaro International',
                     'rss': 'https://www.lefigaro.fr/rss/figaro_international.xml',
                     'country': 'FR'},
                    {'name': 'Libération Monde',
                     'rss': 'https://www.liberation.fr/arc/outboundfeeds/rss/category/monde/',
                     'country': 'FR'},
                    {'name': 'France Info Monde',
                     'rss': 'https://www.francetvinfo.fr/monde.rss',
                     'country': 'FR'},
                    {'name': 'L\'Express International',
                     'rss': 'https://www.lexpress.fr/rss/monde.xml',
                     'country': 'FR'},
                ],
                'belgium': [
                    {'name': 'Le Soir International',
                     'rss': 'https://www.lesoir.be/rss/section/actualite-internationale',
                     'country': 'BE'},
                    {'name': 'RTBF Info Monde',
                     'rss': 'https://www.rtbf.be/info/rss/monde',
                     'country': 'BE'},
                ],
                'canada': [
                    {'name': 'Radio-Canada International',
                     'rss': 'https://ici.radio-canada.ca/rss/4159',
                     'country': 'CA'},
                    {'name': 'La Presse International',
                     'rss': 'https://www.lapresse.ca/international/rss',
                     'country': 'CA'},
                ],
                'switzerland': [
                    {'name': 'RTS Info Monde',
                     'rss': 'https://www.rts.ch/info/monde/rss.xml',
                     'country': 'CH'},
                ],
                'international': [
                    {'name': 'France24 Français',
                     'rss': 'https://www.france24.com/fr/rss',
                     'country': 'FR'},
                    {'name': 'RFI Monde',
                     'rss': 'https://www.rfi.fr/fr/rss',
                     'country': 'FR'},
                    {'name': 'TV5 Monde Info',
                     'rss': 'https://information.tv5monde.com/rss.xml',
                     'country': 'FR'},
                ]
            },

            # German Language Sources
            'de': {
                'germany': [
                    {'name': 'Der Spiegel International',
                     'rss': 'https://www.spiegel.de/international/index.rss',
                     'country': 'DE'},
                    {'name': 'Die Zeit International',
                     'rss': 'https://www.zeit.de/politik/ausland/index',
                     'country': 'DE'},
                    {'name': 'Süddeutsche International',
                     'rss': 'https://www.sueddeutsche.de/politik/rss',
                     'country': 'DE'},
                    {'name': 'Frankfurter Allgemeine',
                     'rss': 'https://www.faz.net/rss/aktuell/politik/',
                     'country': 'DE'},
                    {'name': 'Die Welt Politik',
                     'rss': 'https://www.welt.de/politik/?service=Rss',
                     'country': 'DE'},
                    {'name': 'Tagesschau',
                     'rss': 'https://www.tagesschau.de/xml/rss2/',
                     'country': 'DE'},
                ],
                'austria': [
                    {'name': 'Der Standard International',
                     'rss': 'https://www.derstandard.at/rss/International',
                     'country': 'AT'},
                    {'name': 'Die Presse International',
                     'rss': 'https://www.diepresse.com/rss/politik',
                     'country': 'AT'},
                ],
                'switzerland': [
                    {'name': 'NZZ International',
                     'rss': 'https://www.nzz.ch/international.rss',
                     'country': 'CH'},
                    {'name': 'Tages-Anzeiger International',
                     'rss': 'https://www.tagesanzeiger.ch/rss/international',
                     'country': 'CH'},
                ],
                'international': [
                    {'name': 'Deutsche Welle',
                     'rss': 'https://rss.dw.com/rdf/rss-de-all',
                     'country': 'DE'},
                ]
            },

            # Russian Language Sources
            'ru': {
                'russia': [
                    {'name': 'РИА Новости',
                     'rss': 'https://ria.ru/export/rss2/archive/index.xml',
                     'country': 'RU'},
                    {'name': 'ТАСС',
                     'rss': 'https://tass.ru/rss/v2.xml',
                     'country': 'RU'},
                    {'name': 'Интерфакс',
                     'rss': 'https://www.interfax.ru/rss.asp',
                     'country': 'RU'},
                    {'name': 'Газета.Ru',
                     'rss': 'https://www.gazeta.ru/export/rss/lenta.xml',
                     'country': 'RU'},
                    {'name': 'Коммерсантъ',
                     'rss': 'https://www.kommersant.ru/RSS/news.xml',
                     'country': 'RU'},
                    {'name': 'Ведомости',
                     'rss': 'https://www.vedomosti.ru/rss/news',
                     'country': 'RU'},
                ],
                'ukraine': [
                    {'name': 'Украинская Правда',
                     'rss': 'https://www.pravda.com.ua/rss/',
                     'country': 'UA'},
                    {'name': 'УНИАН',
                     'rss': 'https://www.unian.net/rss/news.xml',
                     'country': 'UA'},
                ],
                'belarus': [
                    {'name': 'БелТА',
                     'rss': 'https://www.belta.by/rss/',
                     'country': 'BY'},
                ],
                'international': [
                    {'name': 'RT на русском',
                     'rss': 'https://russian.rt.com/rss',
                     'country': 'RU'},
                    {'name': 'Sputnik',
                     'rss': 'https://sputniknews.com/export/rss2/archive/index.xml',
                     'country': 'RU'},
                ]
            },

            # Chinese Language Sources
            'zh': {
                'china': [
                    {'name': '新华网',
                     'rss': 'http://www.xinhuanet.com/politics/news_politics.xml',
                     'country': 'CN'},
                    {'name': '人民网',
                     'rss': 'http://www.people.com.cn/rss/politics.xml',
                     'country': 'CN'},
                    {'name': '央视网',
                     'rss': 'http://news.cctv.com/rss/china.xml',
                     'country': 'CN'},
                    {'name': '环球时报',
                     'rss': 'https://www.globaltimes.cn/rss/china.xml',
                     'country': 'CN'},
                ],
                'taiwan': [
                    {'name': '中央社',
                     'rss': 'https://feeds.cna.com.tw/rssfeed/china',
                     'country': 'TW'},
                    {'name': '自由時報',
                     'rss': 'https://news.ltn.com.tw/rss/politics.xml',
                     'country': 'TW'},
                ],
                'hong_kong': [
                    {'name': '明報',
                     'rss': 'https://news.mingpao.com/rss/pns/s00001.xml',
                     'country': 'HK'},
                    {'name': '南華早報中文',
                     'rss': 'https://www.scmp.com/rss/91/feed',
                     'country': 'HK'},
                ],
                'singapore': [
                    {'name': '联合早报',
                     'rss': 'https://www.zaobao.com.sg/realtime/china/rss.xml',
                     'country': 'SG'},
                ],
                'international': [
                    {'name': 'BBC中文',
                     'rss': 'https://feeds.bbci.co.uk/zhongwen/simp/rss.xml',
                     'country': 'GB'},
                    {'name': 'VOA中文',
                     'rss': 'https://www.voachinese.com/api/zoomieqiuie',
                     'country': 'US'},
                    {'name': 'DW中文',
                     'rss': 'https://rss.dw.com/rdf/rss-chi-all',
                     'country': 'DE'},
                ]
            },

            # Arabic Language Sources
            'ar': {
                'middle_east': [
                    {'name': 'الجزيرة',
                     'rss': 'https://www.aljazeera.net/feed/rss/all',
                     'country': 'QA'},
                    {'name': 'العربية',
                     'rss': 'https://www.alarabiya.net/ar/rss.xml',
                     'country': 'AE'},
                    {'name': 'سكاي نيوز عربية',
                     'rss': 'https://www.skynewsarabia.com/feed',
                     'country': 'AE'},
                    {'name': 'الميادين',
                     'rss': 'https://www.almayadeen.net/rss',
                     'country': 'LB'},
                    {'name': 'TRT عربي',
                     'rss': 'https://www.trt.net.tr/arabic/rss',
                     'country': 'TR'},
                ],
                'egypt': [
                    {'name': 'الأهرام',
                     'rss': 'http://gate.ahram.org.eg/rss/ahram.xml',
                     'country': 'EG'},
                    {'name': 'اليوم السابع',
                     'rss': 'https://www.youm7.com/rss/sectionRss?sectionId=245',
                     'country': 'EG'},
                    {'name': 'المصري اليوم',
                     'rss': 'https://www.almasryalyoum.com/rss/news',
                     'country': 'EG'},
                ],
                'saudi_arabia': [
                    {'name': 'الرياض',
                     'rss': 'https://www.alriyadh.com/rss.xml',
                     'country': 'SA'},
                    {'name': 'عكاظ',
                     'rss': 'https://www.okaz.com.sa/rss.xml',
                     'country': 'SA'},
                    {'name': 'الشرق الأوسط',
                     'rss': 'https://aawsat.com/feed',
                     'country': 'SA'},
                ],
                'uae': [
                    {'name': 'الإمارات اليوم',
                     'rss': 'https://www.emaratalyoum.com/rss/feed.xml',
                     'country': 'AE'},
                    {'name': 'البيان',
                     'rss': 'https://www.albayan.ae/rss/feed.xml',
                     'country': 'AE'},
                    {'name': 'الخليج',
                     'rss': 'https://www.alkhaleej.ae/rss/feed.xml',
                     'country': 'AE'},
                ],
                'lebanon': [
                    {'name': 'النهار',
                     'rss': 'https://www.annahar.com/rss',
                     'country': 'LB'},
                    {'name': 'الأخبار',
                     'rss': 'https://www.al-akhbar.com/rss',
                     'country': 'LB'},
                ],
                'jordan': [
                    {'name': 'الرأي',
                     'rss': 'https://alrai.com/rss.xml',
                     'country': 'JO'},
                ],
                'morocco': [
                    {'name': 'هسبريس',
                     'rss': 'https://www.hespress.com/rss',
                     'country': 'MA'},
                ],
                'international': [
                    {'name': 'BBC عربي',
                     'rss': 'https://feeds.bbci.co.uk/arabic/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW عربي',
                     'rss': 'https://rss.dw.com/rdf/rss-ar-all',
                     'country': 'DE'},
                    {'name': 'France24 عربي',
                     'rss': 'https://www.france24.com/ar/rss',
                     'country': 'FR'},
                ]
            },

            # Portuguese Language Sources
            'pt': {
                'brazil': [
                    {'name': 'G1 Mundo',
                     'rss': 'http://g1.globo.com/dynamo/mundo/rss2.xml',
                     'country': 'BR'},
                    {'name': 'Folha Internacional',
                     'rss': 'https://feeds.folha.uol.com.br/mundo/rss091.xml',
                     'country': 'BR'},
                    {'name': 'O Estado de S.Paulo Internacional',
                     'rss': 'https://internacional.estadao.com.br/rss.xml',
                     'country': 'BR'},
                    {'name': 'UOL Notícias Internacional',
                     'rss': 'https://rss.uol.com.br/feed/noticias.xml',
                     'country': 'BR'},
                ],
                'portugal': [
                    {'name': 'Público Internacional',
                     'rss': 'https://www.publico.pt/rss/mundo',
                     'country': 'PT'},
                    {'name': 'Correio da Manhã Mundo',
                     'rss': 'https://www.cmjornal.pt/rss/mundo',
                     'country': 'PT'},
                    {'name': 'Expresso Internacional',
                     'rss': 'https://expresso.pt/rss/internacional',
                     'country': 'PT'},
                ],
                'international': [
                    {'name': 'DW Português',
                     'rss': 'https://rss.dw.com/rdf/rss-pt-all',
                     'country': 'DE'},
                    {'name': 'BBC Brasil',
                     'rss': 'https://feeds.bbci.co.uk/portuguese/rss.xml',
                     'country': 'GB'},
                ]
            },

            # Italian Language Sources
            'it': {
                'italy': [
                    {'name': 'Corriere della Sera Esteri',
                     'rss': 'https://www.corriere.it/rss/esteri.xml',
                     'country': 'IT'},
                    {'name': 'La Repubblica Esteri',
                     'rss': 'https://www.repubblica.it/rss/esteri/rss2.0.xml',
                     'country': 'IT'},
                    {'name': 'La Gazzetta del Mezzogiorno Esteri',
                     'rss': 'https://www.lagazzettadelmezzogiorno.it/rss/esteri.xml',
                     'country': 'IT'},
                    {'name': 'ANSA Mondo',
                     'rss': 'https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml',
                     'country': 'IT'},
                ],
                'international': [
                    {'name': 'Vatican News',
                     'rss': 'https://www.vaticannews.va/it/mondo.rss.xml',
                     'country': 'VA'},
                ]
            },

            # Japanese Language Sources
            'ja': {
                'japan': [
                    {'name': 'NHK国際',
                     'rss': 'https://www3.nhk.or.jp/rss/news/cat7.xml',
                     'country': 'JP'},
                    {'name': '読売新聞国際',
                     'rss': 'https://www.yomiuri.co.jp/rss/world.xml',
                     'country': 'JP'},
                    {'name': '朝日新聞国際',
                     'rss': 'https://www.asahi.com/rss/international.xml',
                     'country': 'JP'},
                    {'name': '毎日新聞国際',
                     'rss': 'https://mainichi.jp/rss/etc/world.rss',
                     'country': 'JP'},
                ],
                'international': [
                    {'name': 'BBC日本語',
                     'rss': 'https://feeds.bbci.co.uk/japanese/rss.xml',
                     'country': 'GB'},
                ]
            },

            # Korean Language Sources
            'ko': {
                'south_korea': [
                    {'name': '연합뉴스 국제',
                     'rss': 'https://www.yna.co.kr/rss/international.xml',
                     'country': 'KR'},
                    {'name': '조선일보 국제',
                     'rss': 'https://www.chosun.com/arc/outboundfeeds/rss/category/international/',
                     'country': 'KR'},
                    {'name': '중앙일보 국제',
                     'rss': 'https://rss.joins.com/joins_world_list.xml',
                     'country': 'KR'},
                ],
                'international': [
                    {'name': 'KBS World',
                     'rss': 'http://world.kbs.co.kr/rss/rss_news.xml',
                     'country': 'KR'},
                ]
            },

            # Dutch Language Sources
            'nl': {
                'netherlands': [
                    {'name': 'NOS Buitenland',
                     'rss': 'https://feeds.nos.nl/nosnieuwsbuitenland',
                     'country': 'NL'},
                    {'name': 'De Volkskrant Buitenland',
                     'rss': 'https://www.volkskrant.nl/buitenland/rss.xml',
                     'country': 'NL'},
                    {'name': 'NRC Buitenland',
                     'rss': 'https://www.nrc.nl/rss/buitenland/',
                     'country': 'NL'},
                ],
                'belgium': [
                    {'name': 'VRT NWS Buitenland',
                     'rss': 'https://www.vrt.be/vrtnws/nl/buitenland.rss.xml',
                     'country': 'BE'},
                ]
            },

            # Ukrainian Language Sources (CONFLICT ZONE - Ukraine War)
            'uk': {
                'ukraine': [
                    {'name': 'Українська Правда',
                     'rss': 'https://www.pravda.com.ua/rss/',
                     'country': 'UA',
                     'priority': 'high'},
                    {'name': 'Укрінформ',
                     'rss': 'https://www.ukrinform.ua/rss',
                     'country': 'UA',
                     'priority': 'high'},
                    {'name': 'Радіо Свобода Україна',
                     'rss': 'https://www.radiosvoboda.org/api/z-opqieqtiq',
                     'country': 'UA',
                     'priority': 'high'},
                    {'name': 'Цензор.НЕТ',
                     'rss': 'https://censor.net/ua/rss/news',
                     'country': 'UA',
                     'priority': 'high'},
                    {'name': 'Дзеркало Тижня', 'rss': 'https://zn.ua/rss/',
                        'country': 'UA', 'priority': 'medium'},
                    {'name': 'Українські Новини',
                     'rss': 'https://ukranews.com/ua/rss/',
                     'country': 'UA',
                     'priority': 'medium'},
                    {'name': 'Гордон', 'rss': 'https://gordonua.com/rss.html',
                        'country': 'UA', 'priority': 'medium'},
                    {'name': '24 Канал', 'rss': 'https://24tv.ua/rss/',
                        'country': 'UA', 'priority': 'medium'},
                ],
                'international': [
                    {'name': 'BBC Україна',
                     'rss': 'https://feeds.bbci.co.uk/ukrainian/rss.xml',
                     'country': 'GB',
                     'priority': 'high'},
                    {'name': 'DW Українська',
                     'rss': 'https://rss.dw.com/rdf/rss-uk-all',
                     'country': 'DE',
                     'priority': 'high'},
                ]
            },

            # Hebrew Language Sources - MIDDLE EAST CONFLICT
            'he': {
                'israel': [
                    {'name': 'ידיעות אחרונות',
                     'rss': 'https://www.ynet.co.il/Integration/StoryRss2.xml',
                     'country': 'IL'},
                    {'name': 'הארץ',
                     'rss': 'https://www.haaretz.co.il/news/politics/rss/',
                     'country': 'IL'},
                    {'name': 'מעריב',
                     'rss': 'https://www.maariv.co.il/rss/',
                     'country': 'IL'},
                    {'name': 'כלכליסט',
                     'rss': 'https://www.calcalist.co.il/GeneralRSS/GeneralRSS.aspx',
                     'country': 'IL'},
                    {
                        'name': 'גלובס',
                        'rss': 'https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=1725',
                        'country': 'IL'},
                    {'name': 'וואלה! חדשות',
                     'rss': 'https://news.walla.co.il/rss/news.xml',
                     'country': 'IL'},
                    {'name': 'הזמן הישראלי',
                     'rss': 'https://www.israelhayom.co.il/rss',
                     'country': 'IL'},
                ],
                'international': [
                    {'name': 'BBC בעברית',
                     'rss': 'https://feeds.bbci.co.uk/hebrew/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW בעברית',
                     'rss': 'https://rss.dw.com/rdf/rss-heb-all',
                     'country': 'DE'},
                    {'name': 'כאן חדשות',
                     'rss': 'https://www.kan.org.il/rss/',
                     'country': 'IL'},
                ]
            },
            # Turkish Language Sources - REGIONAL CONFLICTS
            'tr': {
                'turkey': [
                    {'name': 'Hürriyet Dünya',
                     'rss': 'https://www.hurriyet.com.tr/rss/dunya',
                     'country': 'TR'},
                    {'name': 'Milliyet Dünya',
                     'rss': 'https://www.milliyet.com.tr/rss/rssNew/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sabah Dünya',
                     'rss': 'https://www.sabah.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Cumhuriyet Dünya',
                     'rss': 'https://www.cumhuriyet.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sözcü Dünya',
                     'rss': 'https://www.sozcu.com.tr/kategori/dunya/feed/',
                     'country': 'TR'},
                    {'name': 'Yeni Şafak Dünya',
                     'rss': 'https://www.yenisafak.com/rss?xml=dunya',
                     'country': 'TR'},
                    {'name': 'Anadolu Ajansı',
                     'rss': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
                     'country': 'TR'},
                ],
                'international': [
                    {'name': 'BBC Türkçe',
                     'rss': 'https://feeds.bbci.co.uk/turkce/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW Türkçe',
                     'rss': 'https://rss.dw.com/rdf/rss-tur-all',
                     'country': 'DE'},
                    {'name': 'TRT Haber',
                     'rss': 'https://www.trthaber.com/sondakika_articles.rss',
                     'country': 'TR'},
                ]
            }
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
            'am': {'name': 'Amharic', 'region': 'Horn of Africa', 'conflict_priority': 'high'},
            'sw': {'name': 'Swahili', 'region': 'East Africa', 'conflict_priority': 'high'},
            'ha': {'name': 'Hausa', 'region': 'West Africa/Sahel', 'conflict_priority': 'high'},
            'ti': {'name': 'Tigrinya', 'region': 'Horn of Africa', 'conflict_priority': 'high'},
            'sr': {'name': 'Serbian', 'region': 'Balkans', 'conflict_priority': 'high'},
            'hr': {'name': 'Croatian', 'region': 'Balkans', 'conflict_priority': 'high'},
            'sq': {'name': 'Albanian', 'region': 'Balkans', 'conflict_priority': 'high'},
            'bn': {'name': 'Bengali', 'region': 'South Asia', 'conflict_priority': 'high'},
            'si': {'name': 'Sinhala', 'region': 'South Asia', 'conflict_priority': 'high'},
            'ta': {'name': 'Tamil', 'region': 'South Asia', 'conflict_priority': 'high'},
            'prs': {'name': 'Dari', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'ka': {'name': 'Georgian', 'region': 'Caucasus', 'conflict_priority': 'medium'},
            'km': {'name': 'Khmer', 'region': 'Southeast Asia', 'conflict_priority': 'medium'},
            'lo': {'name': 'Lao', 'region': 'Southeast Asia', 'conflict_priority': 'medium'},
            'ug': {'name': 'Uyghur', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'bo': {'name': 'Tibetan', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'mn': {'name': 'Mongolian', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'kk': {'name': 'Kazakh', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'uz': {'name': 'Uzbek', 'region': 'Central Asia', 'conflict_priority': 'medium'},
            'mk': {'name': 'Macedonian', 'region': 'Balkans', 'conflict_priority': 'medium'},
            'ro_md': {'name': 'Moldovan/Romanian', 'region': 'Eastern Europe', 'conflict_priority': 'medium'},
            'om': {'name': 'Oromo', 'region': 'Horn of Africa', 'conflict_priority': 'medium'},
            'vi': {'name': 'Vietnamese', 'region': 'Southeast Asia', 'conflict_priority': 'medium'},
            'th': {'name': 'Thai', 'region': 'Southeast Asia', 'conflict_priority': 'medium'}
        }

        # Sources registry
        self.sources = {
            # Hebrew Language Sources - MIDDLE EAST CONFLICT
            'he': {
                'israel': [
                    {'name': 'ידיעות אחרונות',
                     'rss': 'https://www.ynet.co.il/Integration/StoryRss2.xml',
                     'country': 'IL'},
                    {'name': 'הארץ',
                     'rss': 'https://www.haaretz.co.il/news/politics/rss/',
                     'country': 'IL'},
                    {'name': 'מעריב',
                     'rss': 'https://www.maariv.co.il/rss/',
                     'country': 'IL'},
                    {'name': 'כלכליסט',
                     'rss': 'https://www.calcalist.co.il/GeneralRSS/GeneralRSS.aspx',
                     'country': 'IL'},
                    {
                        'name': 'גלובס',
                        'rss': 'https://www.globes.co.il/webservice/rss/rssfeeder.asmx/FeederNode?iID=1725',
                        'country': 'IL'},
                    {'name': 'וואלה! חדשות',
                     'rss': 'https://news.walla.co.il/rss/news.xml',
                     'country': 'IL'},
                    {'name': 'הזמן הישראלי',
                     'rss': 'https://www.israelhayom.co.il/rss',
                     'country': 'IL'},
                ],
                'international': [
                    {'name': 'BBC בעברית',
                     'rss': 'https://feeds.bbci.co.uk/hebrew/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW בעברית',
                     'rss': 'https://rss.dw.com/rdf/rss-heb-all',
                     'country': 'DE'},
                    {'name': 'כאן חדשות',
                     'rss': 'https://www.kan.org.il/rss/',
                     'country': 'IL'},
                ]
            },
            # Turkish Language Sources - REGIONAL CONFLICTS
            'tr': {
                'turkey': [
                    {'name': 'Hürriyet Dünya',
                     'rss': 'https://www.hurriyet.com.tr/rss/dunya',
                     'country': 'TR'},
                    {'name': 'Milliyet Dünya',
                     'rss': 'https://www.milliyet.com.tr/rss/rssNew/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sabah Dünya',
                     'rss': 'https://www.sabah.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Cumhuriyet Dünya',
                     'rss': 'https://www.cumhuriyet.com.tr/rss/dunya.xml',
                     'country': 'TR'},
                    {'name': 'Sözcü Dünya',
                     'rss': 'https://www.sozcu.com.tr/kategori/dunya/feed/',
                     'country': 'TR'},
                    {'name': 'Yeni Şafak Dünya',
                     'rss': 'https://www.yenisafak.com/rss?xml=dunya',
                     'country': 'TR'},
                    {'name': 'Anadolu Ajansı',
                     'rss': 'https://www.aa.com.tr/tr/rss/default?cat=dunya',
                     'country': 'TR'},
                ],
                'international': [
                    {'name': 'BBC Türkçe',
                     'rss': 'https://feeds.bbci.co.uk/turkce/rss.xml',
                     'country': 'GB'},
                    {'name': 'DW Türkçe',
                     'rss': 'https://rss.dw.com/rdf/rss-tur-all',
                     'country': 'DE'},
                    {'name': 'TRT Haber',
                     'rss': 'https://www.trthaber.com/sondakika_articles.rss',
                     'country': 'TR'},
                ]
            }
        }

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return list(self.sources.keys())

    def get_sources_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all sources for a specific language."""
        sources = []

        if language in self.sources:
            for region_sources in self.sources[language].values():
                sources.extend(region_sources)

        return sources

    def get_sources_by_region(
            self, language: str, region: str) -> List[Dict[str, Any]]:
        """Get sources for a specific language and region."""
        sources = []

        if language in self.sources and region in self.sources[language]:
            sources.extend(self.sources[language][region])

        return sources

    def get_all_sources(self) -> List[Dict[str, Any]]:
        """Get all available sources."""
        all_sources = []
        for language in self.sources:
            all_sources.extend(self.get_sources_by_language(language))
        return all_sources


class EnhancedNewsAPICollector:
    """Enhanced NewsAPI collector with multilingual support."""

    def __init__(self):
        try:
            from .news_collector import NewsAPICollector
            self.newsapi_collector = NewsAPICollector()
        except ImportError:
            self.newsapi_collector = None
            logger.warning("NewsAPICollector not available")

        self.supported_languages = [
            'ar',
            'de',
            'en',
            'es',
            'fr',
            'he',
            'it',
            'nl',
            'no',
            'pt',
            'ru',
            'sv',
            'zh']

    def collect_by_language(
            self,
            language: str,
            max_articles: int = 100) -> int:
        """Collect articles by language using NewsAPI."""
        if not self.newsapi_collector:
            logger.warning("NewsAPI collector not available")
            return 0

        try:
            # Use collect_headlines method which exists in NewsAPICollector
            articles = self.newsapi_collector.collect_headlines(
                language=language,
                max_articles=max_articles
            )
            # The method already saves articles to database
            return len(articles) if articles else 0
        except Exception as e:
            logger.error(
                f"Error in enhanced NewsAPI collection for {language}: {e}")
            return 0

    def collect_multilingual_headlines(
            self,
            language: str,
            max_articles: int = 50) -> int:
        """Collect headlines in specific language."""
        return self.collect_by_language(language, max_articles)


class GlobalRSSCollector:
    """Global RSS collector with enhanced source management."""

    def __init__(self):
        try:
            from .news_collector import RSSCollector
            self.rss_collector = RSSCollector()
        except ImportError:
            self.rss_collector = None
            logger.warning("RSSCollector not available")

        self.registry = GlobalNewsSourcesRegistry()

    def collect_by_language(
            self,
            language: str,
            max_articles: int = 100) -> int:
        """Collect from RSS sources by language."""
        try:
            sources = self.registry.get_sources_by_language(language)
            return self.collect_from_sources(
                sources, max_articles // len(sources) if sources else 0)
        except Exception as e:
            logger.error(f"Error collecting RSS for {language}: {e}")
            return 0

    def collect_from_sources(
            self, sources: List[Dict[str, Any]], max_articles_per_source: int = 20) -> int:
        """Collect from a list of RSS sources."""
        if not self.rss_collector:
            logger.warning("RSS collector not available")
            return 0

        total_collected = 0

        for source in sources:
            try:
                rss_url = source.get('rss')
                if not rss_url:
                    continue

                count = self.rss_collector.collect_from_rss(
                    rss_url=rss_url,
                    source_name=source.get('name', 'Unknown'),
                    max_articles=max_articles_per_source
                )
                total_collected += count

                if count > 0:
                    logger.debug(
                        f"[OK] Collected {count} articles from {source.get('name', rss_url)}")

            except Exception as e:
                logger.warning(
                    f"[ERROR] Error collecting from {source.get('name', 'unknown')}: {e}")
                continue

        return total_collected

    def collect_all_sources(self, max_articles: int = 1000) -> int:
        """Collect from all available RSS sources."""
        try:
            all_sources = self.registry.get_all_sources()
            max_per_source = max_articles // len(
                all_sources) if all_sources else 0
            return self.collect_from_sources(all_sources, max_per_source)
        except Exception as e:
            logger.error(f"Error in global RSS collection: {e}")
            return 0
