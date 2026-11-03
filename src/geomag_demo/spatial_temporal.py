"""Latitude/longitude × UTC-hour tutorial built from FICTIONAL XYZ samples only.

Inspired by the geographic/time questions in the author's Physics BSc thesis,
but all stations and source values are deterministically fabricated. It must
never be cited as a real geomagnetic-latitude relationship or storm phase.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from html import escape
import math
from statistics import median

from .synthetic import STATIONS, BASE_DAY, EVENT_DAY, END_DAY, xyz, horizontal
from .analysis import cell_id

HOUR_MIN_VALID = 50
MIN_BAND_STATIONS = 3
PEAK_HOURS = tuple((date(2024,5,10),h) for h in range(17,24)) + tuple((date(2024,5,11),h) for h in range(7))
DAY_LIST = tuple(date(2024,5,d) for d in range(10,16))


def hourly_median(station, day:date, hour:int):
    if not 0<=hour<=23:raise ValueError('UTC hour out of range')
    values=[horizontal(v) for mi in range(hour*60,(hour+1)*60) if (v:=xyz(station,day,mi)) is not None]
    return median(values) if len(values)>=HOUR_MIN_VALID else None


def compare_station_hours(stations=STATIONS)->list[dict]:
    """Return per-station hourly ΔH vs same hour on 9 May; missing stays None."""
    result=[];names=set()
    for station in stations:
        if station.code in names:raise ValueError('Duplicate fictional station')
        names.add(station.code)
        ref=[hourly_median(station,BASE_DAY,h) for h in range(24)]
        for day in DAY_LIST:
            for h in range(24):
                current=hourly_median(station,day,h)
                v=current-ref[h] if current is not None and ref[h] is not None else None
                result.append({'station':station.code,'lat_deg':station.latitude,'lon_deg':station.longitude,
                               'date':day,'hour':h,'delta_h_nt':v})
    return result


def aggregate_bands(rows:list[dict],axis:str,min_stations:int=MIN_BAND_STATIONS)->list[dict]:
    if axis not in ('latitude','longitude'):raise ValueError('Unknown geographic axis')
    if min_stations<2:raise ValueError('Require independent stations before colouring a band')
    grouped=defaultdict(dict)
    for r in rows:
        if r['delta_h_nt'] is None:continue
        l=float(r['lat_deg']);g=float(r['lon_deg']);a,b=cell_id(l,g)
        idx=a if axis=='latitude' else b
        k=(r['date'],r['hour'],idx)
        if r['station'] in grouped[k]:raise ValueError('Duplicate station per hour/band')
        val=float(r['delta_h_nt'])
        if not math.isfinite(val):raise ValueError('Nonfinite measured value')
        grouped[k][r['station']]=val
    output=[]
    for day in DAY_LIST:
        for hour in range(24):
            for idx in range(6):
                values=list(grouped[(day,hour,idx)].values());n=len(values)
                output.append(dict(date=day,hour=hour,band=idx,n_valid_stations=n,
                                   median_delta_h_nt=median(values) if n>=min_stations else None))
    return output


def ranks(values):
    indexed=sorted(range(len(values)),key=lambda i:values[i]);out=[0.0]*len(values);i=0
    while i<len(indexed):
        j=i+1
        while j<len(indexed) and values[indexed[i]]==values[indexed[j]]:j+=1
        for k in indexed[i:j]:out[k]=(i+j+1)/2
        i=j
    return out


def spearman(xs,ys):
    if len(xs)!=len(ys) or len(xs)<3: return None
    a,b=ranks(xs),ranks(ys);am=sum(a)/len(a);bm=sum(b)/len(b)
    da=sum((v-am)**2 for v in a);db=sum((v-bm)**2 for v in b)
    if not da or not db:return None
    return sum((x-am)*(y-bm) for x,y in zip(a,b))/math.sqrt(da*db)


def peak_by_latitude(rows:list[dict],min_event_hours:int=10)->list[dict]:
    if min_event_hours<1:raise ValueError('Invalid minimum event hours')
    grouped=defaultdict(list);loc={}
    for r in rows:
        key=(r['date'],r['hour'])
        if key not in PEAK_HOURS:continue
        s=r['station']
        pos=(float(r['lat_deg']),float(r['lon_deg']))
        if s in loc and loc[s]!=pos:raise ValueError('Conflicting station position')
        loc[s]=pos
        if r['delta_h_nt'] is not None:
            grouped[s].append(abs(float(r['delta_h_nt'])))
    out=[]
    for s,pos in sorted(loc.items()):
        vals=grouped.get(s,[])
        if len(vals)<min_event_hours:continue
        out.append({'station':s,'latitude_deg':pos[0],'longitude_deg':pos[1],
                    'absolute_latitude_deg':abs(pos[0]),'peak_abs_delta_h_nt':max(vals),
                    'n_event_hours':len(vals)})
    return out


COLORS={'bg':'#071526','panel':'#102a3c','ink':'#f2f8ff','muted':'#99bbca','stroke':'#335365','blue':'#238bbd','red':'#ee8069','white':'#eaf4f7','missing':'#334354','aqua':'#68d5eb'}


def tag(x):return escape(str(x),quote=True)


def svg_header(width:int,height:int,title:str,sub:str):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{tag(title)} — 100% SYNTHETIC">',
            f'<title>{tag(title)} — COMPLETELY FICTIONAL OBSERVATIONS</title>',
            f'<rect width="{width}" height="{height}" fill="{COLORS["bg"]}"/>',
            f'<text x="47" y="60" font-family="Arial,sans-serif" font-size="31" font-weight="700" fill="{COLORS["ink"]}">{tag(title)}</text>',
            f'<text x="47" y="93" font-family="Arial,sans-serif" font-size="15" fill="{COLORS["muted"]}">{tag(sub)}</text>',
            f'<text x="{width-45}" y="{height-25}" text-anchor="end" font-family="Arial,sans-serif" font-size="11" fill="{COLORS["muted"]}">FICTIONAL DATA ONLY · Ismael Berja Ruiz · Python / Scientific analysis</text>']


def interpol_colour(v:float|None,scale:float=190.0):
    if v is None:return COLORS['missing']
    r=max(-1,min(1,v/scale))
    if r<0:from_,to,alpha=(32,110,162),(237,245,246),r+1
    else:from_,to,alpha=(237,245,246),(232,88,74),r
    rgb=[round(a+(b-a)*alpha) for a,b in zip(from_,to)]
    return '#'+''.join(f'{k:02x}' for k in rgb)


def heatmap_svg(rows:list[dict],axis:str)->str:
    if axis not in ('latitude','longitude'):raise ValueError('Axis must be latitude or longitude')
    if len(rows)!=len(DAY_LIST)*24*6:raise ValueError('Expected complete 6-day x 6-band grid')
    title=('Latitude' if axis=='latitude' else 'Longitude')+' × time — synthetic station response'
    sub='Hourly medians of ΔH versus 9 May at matching UTC hour · a designed simulation, NOT May 2024 observations'
    w,h=1500,775;out=svg_header(w,h,title,sub)
    x0,y0=180,139;stepx=8.4;stepy=65;fullw=144*stepx
    out.append(f'<rect x="{x0-8}" y="{y0-8}" width="{fullw+16:.1f}" height="{6*stepy+16}" rx="16" fill="{COLORS["panel"]}" stroke="{COLORS["stroke"]}"/>')
    for i in range(6):
        j=5-i
        start=-90+30*j if axis=='latitude' else -180+60*j
        width=30 if axis=='latitude' else 60
        label=f'{start:+d}°…{start+width:+d}°'
        out.append(f'<text x="{x0-19}" y="{y0+i*stepy+42}" text-anchor="end" font-family="Arial,sans-serif" font-size="18" font-weight="600" fill="{COLORS["ink"]}">{tag(label)}</text>')
    for k,r in enumerate(rows):
        ti=k//6;j=r['band'];y=(5-j)*stepy;x=x0+ti*stepx
        v=r['median_delta_h_nt'];c=interpol_colour(v)
        out.append(f'<rect x="{x:.2f}" y="{y0+y:.2f}" width="{stepx+.1:.2f}" height="{stepy}" fill="{c}"/>')
    for i,d in enumerate(DAY_LIST):
        x=x0+i*24*stepx
        out.append(f'<path d="M{x:.1f} {y0-6} V{y0+6*stepy+6}" stroke="#5f7a8a" stroke-width="1.2"/>')
        out.append(f'<text x="{x+101:.1f}" y="{y0+6*stepy+39}" text-anchor="middle" font-family="Arial,sans-serif" font-size="18" fill="{COLORS["ink"]}">{d:%d %b}</text>')
    out.append(f'<text x="{x0+fullw/2:.1f}" y="610" text-anchor="middle" font-family="Arial,sans-serif" font-size="17" fill="{COLORS["muted"]}">UTC date &amp; hour · 10–15 May (fictional timeline)</text>')
    legend=[(-180,'−180'),(-90,'−90'),(0,'0'),(90,'+90'),(180,'+180')]
    xx=350;ly=643
    for k in range(100):out.append(f'<rect x="{xx+k*7}" y="{ly}" width="7.1" height="17" fill="{interpol_colour(-190+380*k/99)}"/>')
    for value,lbl in legend:
        x=xx+((value+190)/380)*700
        out.append(f'<text x="{x:.1f}" y="{ly+38}" font-family="Arial,sans-serif" text-anchor="middle" fill="{COLORS["ink"]}" font-size="13">{lbl}</text>')
    out.append(f'<text x="{xx-14}" y="{ly+14}" text-anchor="end" fill="{COLORS["muted"]}" font-family="Arial,sans-serif" font-size="14">Median ΔH (nT)</text>')
    out.append(f'<rect x="1190" y="{ly}" width="24" height="17" fill="{COLORS["missing"]}"/><text x="1225" y="{ly+14}" font-family="Arial,sans-serif" font-size="13" fill="{COLORS["muted"]}">fewer than 3 stations</text>')
    out.append(f'<text x="45" y="{h-57}" font-family="Arial,sans-serif" font-size="12" fill="{COLORS["muted"]}">Signed geographic bands; no interpolation, no causal latitude claim, colour scaling clips visuals only.</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'


def latitude_peak_svg(peaks:list[dict])->str:
    if not peaks:raise ValueError('No eligible fictional stations')
    w,h=1500,775;title='Station peak variation × latitude — fictional association'
    sub='Maximum |ΔH| at 10 May 17:00–11 May 06:59 UTC; artificial event and station geometry'
    out=svg_header(w,h,title,sub)
    rho=spearman([p['absolute_latitude_deg'] for p in peaks],[p['peak_abs_delta_h_nt'] for p in peaks]);ymax=max(250,math.ceil(max(p['peak_abs_delta_h_nt'] for p in peaks)/50)*50)
    x0,y0,width,height=125,165,860,465
    out.append(f'<rect x="{x0}" y="{y0}" width="{width}" height="{height}" rx="13" fill="{COLORS["panel"]}" stroke="{COLORS["stroke"]}"/>')
    for v in range(0,int(ymax)+1,50):
        y=y0+height-(v/ymax)*height
        out.append(f'<path d="M{x0} {y:.1f} H{x0+width}" stroke="{COLORS["stroke"]}" stroke-dasharray="4 6"/>')
        out.append(f'<text x="{x0-10}" y="{y+4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="14" fill="{COLORS["muted"]}">{v}</text>')
    for p in peaks:
        x=x0+int(float(p['absolute_latitude_deg'])/90*width)
        y=y0+height-float(p['peak_abs_delta_h_nt'])/ymax*height
        color=COLORS['aqua'] if p['latitude_deg']>=0 else COLORS['red']
        out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="6.5" fill="{color}" fill-opacity=".83" stroke="#fff" stroke-width=".45"><title>{tag(p["station"])}: lat={p["latitude_deg"]:+.2f}°, peak |ΔH|={p["peak_abs_delta_h_nt"]:.1f} nT; SYNTHETIC</title></circle>')
    for v in range(0,91,15):
        x=x0+v/90*width
        out.append(f'<text x="{x:.1f}" y="{y0+height+29}" text-anchor="middle" fill="{COLORS["muted"]}" font-family="Arial,sans-serif" font-size="14">{v}°</text>')
    out.append(f'<text x="{x0+width/2}" y="{y0+height+62}" text-anchor="middle" fill="{COLORS["ink"]}" font-family="Arial,sans-serif" font-size="17">Absolute geographic latitude (°)</text>')
    out.append(f'<text x="{x0+10}" y="{y0-18}" fill="{COLORS["ink"]}" font-family="Arial,sans-serif" font-size="16">Max |ΔH| (nT) · station-level</text>')
    out.append(f'<text x="{x0+35}" y="{y0+36}" fill="{COLORS["ink"]}" font-family="Arial,sans-serif" font-size="17">Spearman ρ = {rho:+.2f} · n={len(peaks)}</text>')
    counts=[sum(cell_id(p['latitude_deg'],p['longitude_deg'])[0]==i for p in peaks) for i in range(6)]
    bx=1080;out.append(f'<text x="{bx}" y="{y0+15}" fill="{COLORS["ink"]}" font-family="Arial,sans-serif" font-size="20">Station coverage by latitude</text>')
    for i in range(6):
        y=y0+55+i*64
        out.append(f'<text x="{bx}" y="{y+18}" fill="{COLORS["muted"]}" font-family="Arial,sans-serif" font-size="14">{(-90+30*i):+d}…{(-60+30*i):+d}°</text>')
        out.append(f'<rect x="{bx+116}" y="{y}" width="{210*counts[i]/max(counts):.1f}" height="22" rx="5" fill="{COLORS["aqua"]}"/>')
        out.append(f'<text x="{bx+130+210*counts[i]/max(counts):.1f}" y="{y+17}" fill="{COLORS["ink"]}" font-family="Arial,sans-serif" font-size="13">{counts[i]}</text>')
    out.append(f'<text x="45" y="712" fill="{COLORS["muted"]}" font-family="Arial,sans-serif" font-size="13">The latitude pattern is PURPOSELY CONSTRUCTED by the equations in synthetic.py; it is NOT an observed physical relationship.</text>')
    out.append('</svg>');return '\n'.join(out)+'\n'


def render_all(stations=STATIONS):
    rows=compare_station_hours(stations)
    lat=aggregate_bands(rows,'latitude')
    lon=aggregate_bands(rows,'longitude')
    peaks=peak_by_latitude(rows)
    summary={'source':'COMPLETELY SYNTHETIC STATION EQUATIONS; NO INTERMAGNET',
             'station_total':len(stations),'date_range':'2024-05-10 through 2024-05-15, artificial test dates',
             'hourly_station_comparisons':len(rows),'hourly_valid':sum(r['delta_h_nt'] is not None for r in rows),
             'eligible_peak_stations':len(peaks),'min_stations_per_coloured_band':MIN_BAND_STATIONS,
             'spearman_rho_abs_geographic_lat_peak':round(spearman([p['absolute_latitude_deg'] for p in peaks],[p['peak_abs_delta_h_nt'] for p in peaks]),4),
             'warning':'Any statistical association is intentionally produced by fictional equations, not a real measured geomagnetic phenomenon.'}
    outputs={'synthetic_latitude_time_response.svg':heatmap_svg(lat,'latitude'),
             'synthetic_longitude_time_response.svg':heatmap_svg(lon,'longitude'),
             'synthetic_latitude_peak_relationship.svg':latitude_peak_svg(peaks)}
    return outputs,summary
