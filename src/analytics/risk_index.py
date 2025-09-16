"""Calculate composite risk index per country.
Combines recent event count, fatalities, GDP per capita (inverse), oil production volatility and democracy score.
Stores in table `country_risk`.
"""
import sqlite3
from datetime import datetime, timedelta
from utils.config import config, logger

DB=config.database.path

WEIGHTS={
    'events':0.3,
    'fatalities':0.25,
    'gdp_pc':0.15,
    'oil_vol':0.15,
    'democracy':0.15
}

def calc_risk():
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    last30=(datetime.utcnow()-timedelta(days=30)).isoformat()
    # recent events per country
    cur.execute("""SELECT json_extract(location,'$[0]'),json_extract(location,'$[1]'), COALESCE(magnitude,0), COALESCE(type,''), published_at, COALESCE(json_extract(content,'$fatalities'),0) FROM events WHERE published_at>? AND location IS NOT NULL""",(last30,))
    rows=cur.fetchall()
    events_by={}
    from utils.geo import latlon_to_iso3
    for lat,lon,mag,ev_type,ts,fatal in rows:
        iso=latlon_to_iso3(lat,lon)
        if not iso:
            continue
        d=events_by.setdefault(iso,{"events":0,"fatal":0})
        d["events"]+=1
        d["fatal"]+=fatal if fatal else (1 if ev_type=='earthquake' else 0)

    # indicators
    def latest(table,col):
        cur.execute(f"SELECT iso3,{col} FROM {table} WHERE {col} IS NOT NULL AND year=(SELECT MAX(year) FROM {table} t2 WHERE t2.iso3={table}.iso3)")
        return {r[0]:r[1] for r in cur.fetchall()}
    gdp_pc=latest('country_indicators','value')  # maybe multiple indicators; simplified
    dem=latest('country_politics','lib_dem')
    oil=latest('country_energy','oil_production_kbd')

    # min-max normalize helpers
    def norm(dic):
        if not dic:return {}
        v=list(dic.values());mn=min(v);mx=max(v);rng=mx-mn if mx!=mn else 1
        return {k:(dic[k]-mn)/rng for k in dic}
    norm_gdp=norm({k:1/v for k,v in gdp_pc.items() if v})  # inverse (low gdp => high risk)
    norm_dem=norm({k:1-v for k,v in dem.items() if v})      # inverse democracy score
    norm_oil=norm(oil)  # high production => may lower risk or raise? here just raw

    # build risk score
    risk={}
    for iso in events_by:
        risk[iso]=0
        risk[iso]+=WEIGHTS['events']*events_by[iso]['events']
        risk[iso]+=WEIGHTS['fatalities']*events_by[iso]['fatal']
        risk[iso]+=WEIGHTS['gdp_pc']*norm_gdp.get(iso,0)
        risk[iso]+=WEIGHTS['democracy']*norm_dem.get(iso,0)
        risk[iso]+=WEIGHTS['oil_vol']*norm_oil.get(iso,0)

    # normalize final risk 0-100
    if risk:
        mx=max(risk.values());mn=min(risk.values());rng=mx-mn if mx!=mn else 1
        risk={k:round(100*(v-mn)/rng,2) for k,v in risk.items()}

    cur.execute("CREATE TABLE IF NOT EXISTS country_risk (iso3 TEXT PRIMARY KEY, risk REAL, last_updated TEXT)")
    for iso,score in risk.items():
        cur.execute("INSERT OR REPLACE INTO country_risk (iso3,risk,last_updated) VALUES (?,?,?)",(iso,score,datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    logger.info("Risk index placeholder calculated (needs upgrading with geoparsing)")

if __name__=='__main__':
    calc_risk()
