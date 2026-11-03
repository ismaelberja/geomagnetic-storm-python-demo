"""SVG and offline HTML visualizations using synthetic station data ONLY.

All rendering uses Python stdlib and is deterministic across clean machines.
A shaded regional cell is a statistic across fictional stations, not a field.
"""
from __future__ import annotations

from datetime import date
import html
import json
import math
from pathlib import Path
from statistics import median
from .synthetic import STATIONS, BASE_DAY, EVENT_DAY, xyz, horizontal
from .analysis import zones_for_hour, daily_ranges

BG='#081523'; SURFACE='#0e2335'; TEXT='#edf7ff'; MUTED='#a1bdd0'; GRID='#35556b'
CYAN='#5ee6e6'; CORAL='#ffb483'; RED='#ff786d'; BLUE='#59a9f5'; GOLD='#ffd87e'


def E(value: object) -> str:
    return html.escape(str(value), quote=True)


def txt(x: float,y: float,t: object,size: int=16,color: str=TEXT,weight: int=400,anchor: str='start',extra: str='') -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{E(t)}</text>'


def svg_start(w: int,h: int,title: str,subtitle: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(title)}">
<title>{E(title)} — FULLY SYNTHETIC DATA</title>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#112f44"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<radialGradient id="ocean" cx="35%" cy="25%"><stop stop-color="#315c70"/><stop offset=".48" stop-color="#183749"/><stop offset="1" stop-color="#0c1d2c"/></radialGradient>
<clipPath id="globeL"><circle cx="350" cy="414" r="260"/></clipPath><clipPath id="globeR"><circle cx="1050" cy="414" r="260"/></clipPath>
</defs><rect width="{w}" height="{h}" fill="url(#bg)"/>
{txt(52,56,'SCIENTIFIC PYTHON  /  SYNTHETIC DATA LAB',14,CYAN,700,extra='letter-spacing="2"')}
{txt(52,111,title,36,TEXT,700)}
{txt(52,145,subtitle,17,MUTED)}
'''


def footer(w: int,h: int,description: str='Fictional stations · Not an INTERMAGNET product · No continuous Earth-field estimate') -> str:
    return f'<path d="M 52 {h-66} L {w-52} {h-66}" stroke="{GRID}" stroke-width="1"/>'+txt(54,h-35,description,13,MUTED) + txt(w-54,h-35,'Ismael Berja Ruiz  •  Reproducible Python',13,CYAN,anchor='end') + '</svg>\n'


def projection(lat:float,lon:float,center_lon:float,center_lat:float=12) -> tuple[float,float,float]:
    a,b,cl,cp=map(math.radians,(lat,lon,center_lon,center_lat))
    dl=b-cl
    x=math.cos(a)*math.sin(dl)
    y=math.sin(a)*math.cos(cp)-math.cos(a)*math.cos(dl)*math.sin(cp)
    z=math.cos(a)*math.cos(dl)*math.cos(cp)+math.sin(a)*math.sin(cp)
    return x,y,z


def camera_vector(lat:float,lon:float,center_lon:float,north:float,east:float,down:float,center_lat:float=12) -> tuple[float,float]:
    a,b,cl,cp=map(math.radians,(lat,lon,center_lon,center_lat))
    # Convert local geographic N/E/D basis into global Cartesian.
    vn=(-math.sin(a)*math.cos(b),-math.sin(a)*math.sin(b),math.cos(a))
    ve=(-math.sin(b),math.cos(b),0)
    vd=(-math.cos(a)*math.cos(b),-math.cos(a)*math.sin(b),-math.sin(a))
    v=[north*vn[i]+east*ve[i]+down*vd[i] for i in range(3)]
    dx=-math.sin(cl)*v[0]+math.cos(cl)*v[1]
    dy=-math.sin(cp)*(math.cos(cl)*v[0]+math.sin(cl)*v[1])+math.cos(cp)*v[2]
    return dx,dy


def region_clip(points: list[tuple[float,float,float]]) -> list[tuple[float,float,float]]:
    """Clip a spherical cell polygon at the visible (z=0) orthographic plane."""
    result=[]
    if not points:
        return result
    for a,b in zip(points[-1:]+points[:-1],points):
        za,zb=a[2],b[2]
        if (za>=0)!=(zb>=0):
            t=za/(za-zb)
            result.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(3)))
        if zb>=0:
            result.append(b)
    return result


def colour(v:float|None,lim:float=150) -> str:
    if v is None:
        return '#1b3545'
    t=min(1,abs(v)/lim)
    neutral=(177,193,203)
    extreme=(255,112,101) if v>0 else (79,167,250)
    return '#'+''.join(f'{round(neutral[i]*(1-t)+extreme[i]*t):02x}' for i in range(3))


def sphere_background(cx:int,cy:int,r:int,center_lon:float) -> str:
    out=[f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#ocean)" stroke="#7abfd2" stroke-width="2"/>']
    # Meridians and parallels are decorative coordinate guides, not data.
    for lat in [-60,-30,0,30,60]:
        lines=[]
        for lon in range(-180,181,3):
            x,y,z=projection(lat,lon,center_lon)
            if z>=0: lines.append((cx+r*x,cy-r*y))
            elif len(lines)>1:
                out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in lines)+f'" fill="none" stroke="{GRID}" stroke-width=".85" opacity=".65"/>');lines=[]
        if len(lines)>1:out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in lines)+f'" fill="none" stroke="{GRID}" stroke-width=".85" opacity=".65"/>')
    for lon in range(-180,180,30):
        lines=[]
        for lat in range(-90,91,3):
            x,y,z=projection(lat,lon,center_lon)
            if z>=0: lines.append((cx+r*x,cy-r*y))
            elif len(lines)>1:
                out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in lines)+f'" fill="none" stroke="{GRID}" stroke-width=".85" opacity=".65"/>');lines=[]
        if len(lines)>1:out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in lines)+f'" fill="none" stroke="{GRID}" stroke-width=".85" opacity=".65"/>')
    return ''.join(out)


def cell_path(lat_i:int,lon_i:int,center_lon:float,cx:int,cy:int,r:int)->str:
    south=-90+30*lat_i;north=south+30;west=-180+60*lon_i;east=west+60
    route=[]
    for lon in range(west,east,5):route.append((south,lon))
    for lat in range(south,north,5):route.append((lat,east))
    for lon in range(east,west,-5):route.append((north,lon))
    for lat in range(north,south,-5):route.append((lat,west))
    coords=region_clip([projection(a,b,center_lon) for a,b in route])
    if len(coords)<3:return ''
    return 'M '+' L '.join(f'{cx+r*x:.1f} {cy-r*y:.1f}' for x,y,z in coords)+' Z'


def sphere_panel(cx:int,cy:int,r:int,center_lon:int,label:str,rows:list[dict],kind:str='zones') -> str:
    zones=zones_for_hour(rows)
    out=[sphere_background(cx,cy,r,center_lon)]
    if kind=='zones':
        for z in zones:
            p=cell_path(z['lat_band'],z['lon_band'],center_lon,cx,cy,r)
            if not p:
                continue
            v=z['median_delta_h_nt']
            if v is None:
                out.append(f'<path d="{p}" fill="none" stroke="#436174" stroke-width=".6" opacity=".75"/>')
            else:
                out.append(f'<path d="{p}" fill="{colour(v)}" opacity=".84" stroke="#0c2c3a" stroke-width="1"><title>Simulated {z["count"]} stations; median ΔH={v:+.1f} nT</title></path>')
    for row in rows:
        x,y,z=projection(float(row['latitude_deg']),float(row['longitude_deg']),center_lon)
        if z<0:continue
        px,py=cx+r*x,cy-r*y
        station=row['station'];delta=float(row['delta_h_nt'])
        if kind=='vectors':
            dx,dy=camera_vector(float(row['latitude_deg']),float(row['longitude_deg']),center_lon,
                float(row['delta_x_nt']),float(row['delta_y_nt']),float(row['delta_z_nt']))
            d=math.hypot(dx,dy)
            if d>1e-8:
                length=17+9*min(1,abs(float(row['delta_b_nt']))/190)
                tx=px+length*dx/d;ty=py-length*dy/d
                ax=tx-px;ay=ty-py;ang=math.atan2(ay,ax)
                p1=(tx-7*math.cos(ang-.5),ty-7*math.sin(ang-.5));p2=(tx-7*math.cos(ang+.5),ty-7*math.sin(ang+.5))
                out.append(f'<path d="M{px:.1f} {py:.1f} L{tx:.1f} {ty:.1f} M{p1[0]:.1f} {p1[1]:.1f} L{tx:.1f} {ty:.1f} L{p2[0]:.1f} {p2[1]:.1f}" stroke="{colour(float(row["delta_b_nt"]),190)}" stroke-width="2.2" stroke-linecap="round" fill="none"><title>{E(station)}: |ΔB|={row["delta_b_nt"]:.1f} nT; ΔX={row["delta_x_nt"]:+.1f}, ΔY={row["delta_y_nt"]:+.1f}, ΔZ={row["delta_z_nt"]:+.1f} nT (synthetic)</title></path>')
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.1" fill="#ffffff"/>')
        elif kind=='points':
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5.2" fill="{colour(delta)}" stroke="#edf7ff" stroke-width="1"><title>{E(station)}: ΔH={delta:+.1f} nT (synthetic)</title></circle>')
        else:
            n=zones[cell_id_for(row)]['count']
            fill=GOLD if n==1 else '#f7ffff'
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.3" fill="{fill}" stroke="#0a293b" stroke-width=".6"><title>{E(station)}: ΔH={delta:+.1f} nT (synthetic), zone n={n}</title></circle>')
    out.append(txt(cx,cy+r+47,label,21,TEXT,650,anchor='middle'))
    return ''.join(out)


def cell_id_for(row: dict)->int:
    from .analysis import cell_id
    a,b=cell_id(float(row['latitude_deg']),float(row['longitude_deg']))
    return a*6+b


def globe_svg(rows:list[dict],mode:str='zones') -> str:
    if mode not in ('zones','vectors'):
        raise ValueError('Expected zones or vectors')
    title= 'Regional signatures on a 3D Earth' if mode=='zones' else 'Directional magnetic-vector differences'
    sub= ('Geographic cell medians  •  30° × 60°  •  10 May minus 9 May, 18:00 UTC' if mode=='zones'
          else 'Local north / east / down differences  •  10 May minus 9 May, 18:00 UTC')
    body=[svg_start(1400,830,title,sub)]
    for cx,cl,label in ((350,-35,'Atlantic-centred view'),(1050,145,'Pacific-centred view')):
        body.append(sphere_panel(cx,421,255,cl,label,rows,mode))
    if mode=='zones':
        body.append(txt(700,735,'COLOUR = SAMPLED CELL MEDIAN ΔH   •   YELLOW DOT = ONE STATION   •   DARK CELL = INSUFFICIENT COVERAGE',13,MUTED,700,anchor='middle'))
    else:
        body.append(txt(700,735,'ARROW LENGTHS NORMALIZED  •  COLOUR = |ΔB|  •  NOT GLOBAL MAGNETIC FIELD LINES',13,MUTED,700,anchor='middle'))
    body.append(footer(1400,830))
    return ''.join(body)


def chart_base(w:int,h:int,title:str,subtitle:str) -> str:
    return svg_start(w,h,title,subtitle)


def band_plot(rows_by_time: dict[str,list[dict]],axis: str) -> str:
    if axis not in ('latitude','longitude'):
        raise ValueError('Expected geographic axis')
    labels=[f'{-90+30*i:+d}…{-60+30*i:+d}°' for i in range(6)] if axis=='latitude' else [f'{-180+60*i:+d}…{-120+60*i:+d}°' for i in range(6)]
    bands={}
    for clock,rows in rows_by_time.items():
        values=[[] for _ in range(6)]
        from .analysis import cell_id
        for row in rows:
            a,b=cell_id(float(row['latitude_deg']),float(row['longitude_deg']))
            values[a if axis=='latitude' else b].append(float(row['delta_h_nt']))
        bands[clock]=[(median(x) if x else None,len(x)) for x in values]
    title='ΔH by latitude band' if axis=='latitude' else 'ΔH by longitude band'
    out=[chart_base(1350,680,title,'Fictional station medians at matching UTC minutes • 9 May reference vs 10 May')]
    maxabs=max(abs(v) for grp in bands.values() for v,n in grp if v is not None)
    for ii,(clock,results) in enumerate(sorted(bands.items())):
        x0=75+ii*650;y0=200;w=575;h=305;zero=y0+h*.5
        out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="16" fill="{SURFACE}" stroke="#315064"/>')
        out.append(txt(x0+22,y0+34,f'{clock} UTC  /  {sum(n for _,n in results)} usable stations',18,CYAN,700))
        out.append(f'<path d="M {x0+25} {zero:.1f} L {x0+w-25} {zero:.1f}" stroke="#89a5b9" stroke-width="1.5" stroke-dasharray="5 5"/>')
        for i,(v,n) in enumerate(results):
            cx=x0+66+i*81
            out.append(txt(cx,zero+182,labels[i],12,MUTED,anchor='middle'))
            if v is None:continue
            height=112*abs(v)/maxabs
            yy=zero-height if v>=0 else zero
            out.append(f'<rect x="{cx-21:.1f}" y="{yy:.1f}" width="42" height="{max(1,height):.1f}" rx="6" fill="{CORAL if v>=0 else BLUE}"/>')
            out.append(txt(cx, yy-9 if v>=0 else yy+height+21, f'{v:+.0f}',13,TEXT,650,anchor='middle'))
            out.append(txt(cx,y0+h-34,f'n={n}',12,MUTED,anchor='middle'))
    out.append(txt(75,584,f'Bars summarise only fictional {axis} bands; they are NOT spatial interpolation.',16,MUTED))
    out.append(footer(1350,680,'Fictional stations, signed coordinates, real QC logic  •  NOT Earth magnetic measurements'))
    return ''.join(out)


def line_chart() -> str:
    title='Simulated station response and missing-value gaps'
    out=[chart_base(1350,680,title,'Sampled H difference vs the same UTC minute on 9 May • illustrative 10 May 2024 timeline')]
    x0,y0,w,h=100,206,1140,360
    out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="15" fill="{SURFACE}" stroke="#315064"/>')
    stations=[STATIONS[0],STATIONS[6],STATIONS[11]]
    colors=[CYAN,CORAL,GOLD]
    # 15:30..21:00 inclusive, five minute steps.
    minutes=list(range(15*60+30,21*60+1,5))
    values=[]
    for station in stations:
        arr=[]
        for minute in minutes:
            a=xyz(station,BASE_DAY,minute);b=xyz(station,EVENT_DAY,minute)
            arr.append(None if a is None or b is None else horizontal(b)-horizontal(a))
        values.append(arr)
    lows=[v for arr in values for v in arr if v is not None]
    lo=min(-10,min(lows)-10);hi=max(20,max(lows)+10)
    def sx(t):return x0+45+(t-minutes[0])/(minutes[-1]-minutes[0])*(w-90)
    def sy(v):return y0+40+(hi-v)/(hi-lo)*(h-85)
    for i in range(5):
        val=lo+(hi-lo)*i/4
        yy=sy(val)
        out.append(f'<line x1="{x0+45}" x2="{x0+w-45}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{GRID}" opacity=".5"/>')
        out.append(txt(x0+34, yy+5, f'{val:+.0f}',13,MUTED,anchor='end'))
    for minute in range(16*60,22*60):
        if minute%60:continue
        xx=sx(minute);out.append(f'<line x1="{xx:.1f}" x2="{xx:.1f}" y1="{y0+30}" y2="{y0+h-45}" stroke="{GRID}" opacity=".4"/>')
        out.append(txt(xx,y0+h-20,f'{minute//60:02}:00',13,MUTED,anchor='middle'))
    out.append(txt(x0+30,y0-13,'ΔH (nT)',14,MUTED))
    onset=sx(16*60+45)
    out.append(f'<path d="M{onset:.1f} {y0+30} V {y0+h-48}" stroke="{GOLD}" stroke-dasharray="6 6"/>')
    out.append(txt(onset+8,y0+25,'Fictional change begins',12,GOLD))
    for station,col,vals in zip(stations,colors,values):
        pieces=[];current=[]
        for minute,v in zip(minutes,vals):
            if v is None:
                if current:pieces.append(current);current=[]
            else:current.append((sx(minute),sy(v)))
        if current:pieces.append(current)
        for pts in pieces:
            out.append('<polyline points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in pts)+f'" fill="none" stroke="{col}" stroke-width="3" stroke-linecap="round"/>')
    for i,(station,col) in enumerate(zip(stations,colors)):
        out.append(f'<circle cx="{220+i*220}" cy="166" r="7" fill="{col}"/>')
        out.append(txt(236+i*220,172,station.code,17,TEXT,600))
    out.append(txt(960,172,'SIM-012: missing interval = no line',14,GOLD,600))
    out.append(footer(1350,680,'All values generated by deterministic equations; 17:00 and 18:00 gaps remain gaps'))
    return ''.join(out)


def daily_plot()->str:
    title='Daily H range: missing measurements remain missing'
    out=[chart_base(1350,680,title,'Seven fictional days  •  daily max(H) − min(H), with no interpolation across missing days')]
    station_list=[STATIONS[0],STATIONS[1],STATIONS[6]]
    cols=[CYAN,CORAL,GOLD]
    results=[daily_ranges(s) for s in station_list]
    all_vals=[x['range_h_nt'] for arr in results for x in arr if x['range_h_nt'] is not None]
    ymax=max(all_vals)*1.16
    x0,y0,w,h=110,220,1110,335
    out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="16" fill="{SURFACE}" stroke="#315064"/>')
    def sx(i):return x0+60+i*(w-120)/6
    def sy(v):return y0+h-48-v/ymax*(h-90)
    for i in range(5):
        y=sy(ymax*i/4);out.append(f'<path d="M{x0+45} {y:.1f} H{x0+w-38}" stroke="{GRID}" opacity=".5"/>')
        out.append(txt(x0+36,y+4,f'{ymax*i/4:.0f}',12,MUTED,anchor='end'))
    for i in range(7):out.append(txt(sx(i),y0+h-19,f'{i+9:02} May',14,MUTED,anchor='middle'))
    for station,col,arr in zip(station_list,cols,results):
        active=[]
        for i,r in enumerate(arr):
            v=r['range_h_nt']
            if v is None:
                if len(active)>1:out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in active)+f'" fill="none" stroke="{col}" stroke-width="3"/>')
                active=[]
                continue
            active.append((sx(i),sy(v)))
            out.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="4.5" fill="{col}"/>')
        if len(active)>1:out.append('<polyline points="'+' '.join(f'{a:.1f},{b:.1f}' for a,b in active)+f'" fill="none" stroke="{col}" stroke-width="3"/>')
    # Explicit shading/callout for SIM-002: entirely missing day (not zero).
    lost=sx(4)
    out.append(f'<rect x="{lost-22:.1f}" y="{y0+48}" width="44" height="{h-100}" fill="{CORAL}" opacity=".07"/>')
    out.append(txt(lost-12,y0+70,'SIM-002',12,CORAL,700,anchor='end'))
    out.append(txt(lost-12,y0+87,'13 May: no data',12,CORAL,700,anchor='end'))
    for i,(station,col) in enumerate(zip(station_list,cols)):
        out.append(f'<circle cx="{230+i*220}" cy="174" r="7" fill="{col}"/>')
        out.append(txt(246+i*220,180,station.code,17,TEXT,600))
    out.append(txt(1115,175,'13 May SIM-002 gap preserved',14,CORAL,600,anchor='end'))
    out.append(footer(1350,680,'Sample daily ranges from fictional 1-minute XYZ; each missing day is excluded, never zero'))
    return ''.join(out)


def coverage_plot()->str:
    out=[chart_base(1350,680,'Station data coverage and quality screening',
        'Valid synthetic XYZ minutes per day • sentinel rows do not contribute to statistics')]
    vals=[daily_ranges(STATIONS[i]) for i in (0,1,6)]
    colors=[CYAN,CORAL,GOLD]
    x0=100;y0=213;w=1120;h=350
    out.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="16" fill="{SURFACE}" stroke="#315064"/>')
    for pct in [0,25,50,75,100]:
        yy=y0+h-55-pct/100*(h-100)
        out.append(f'<line x1="{x0+52}" x2="{x0+w-20}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="{GRID}" opacity=".55"/>')
        out.append(txt(x0+43,yy+4,f'{pct}%',13,MUTED,anchor='end'))
    bar_w=31
    for day_i in range(7):
        x=x0+113+day_i*142
        for series_i,r in enumerate(vals):
            n=r[day_i]['count'];pct=n/1440*100;bh=(h-100)*pct/100
            out.append(f'<rect x="{x+series_i*(bar_w+5):.1f}" y="{y0+h-55-bh:.1f}" width="{bar_w}" height="{bh:.1f}" rx="4" fill="{colors[series_i]}"/>')
        out.append(txt(x+45,y0+h-23,f'{9+day_i:02} May',14,MUTED,anchor='middle'))
    for i,col in enumerate(colors):
        out.append(f'<rect x="{155+i*220}" y="160" width="14" height="14" rx="3" fill="{col}"/>')
        out.append(txt(180+i*220,174,STATIONS[(0,1,6)[i]].code,16,TEXT,600))
    out.append(txt(940,174,'Blank column = zero valid minutes',14,CORAL))
    out.append(footer(1350,680,'Explicit completeness tests: 1,440 expected minute slots/day; no fabricated gap values'))
    return ''.join(out)


def build_html(snapshots:dict[str,list[dict]]) -> str:
    """A standalone offline Canvas viewer, no third-party JS/network request."""
    for t in ('17:00','18:00'):
        if t not in snapshots:raise ValueError('Need 17:00 and 18:00 synthetic snapshots')
    # Javascript code is original and completely inline.
    data=json.dumps(snapshots,sort_keys=True,separators=(',',':'))
    template=r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Standalone, entirely synthetic geomagnetic-style 3D Earth globe. No real observations.">
<title>Synthetic Geomagnetic Data Lab | Interactive 3D Earth</title>
<style>
:root{color-scheme:dark;font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#081523;color:#eef8ff}*{box-sizing:border-box}
body{margin:0;background:radial-gradient(ellipse at 30% -10%,#1c4153,#081523 67%)}main{max-width:1240px;margin:auto;padding:30px 20px 38px}
small.eyebrow{font-weight:800;letter-spacing:.19em;color:#5ee6e6}h1{font-size:clamp(27px,4vw,48px);line-height:1.12;margin:12px 0 6px}p{color:#b3c6d3;max-width:900px;margin:10px 0 22px}
.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:22px 0}button{background:#163247;border:1px solid #44687e;color:#eaf6fa;border-radius:999px;padding:11px 18px;font-weight:700;cursor:pointer}button.active{background:#b0f0eb;color:#0b2634;border-color:#b0f0eb}button:focus-visible{outline:3px solid #ffd87e;outline-offset:3px}
fieldset{border:0;display:flex;gap:8px;padding:0;margin:0 15px 0 0}legend{font-size:12px;text-transform:uppercase;letter-spacing:.1em;font-weight:700;color:#a9c2d0;margin:0 0 6px}
.viewer{position:relative;border:1px solid #33546a;background:radial-gradient(ellipse at 45% 30%,#163e54,#0b1a28 73%);border-radius:20px;overflow:hidden}canvas{display:block;max-width:100%;width:100%;height:auto;touch-action:none;cursor:grab}canvas:active{cursor:grabbing}
#tip{position:absolute;pointer-events:none;left:16px;top:15px;max-width:330px;background:#06131fe8;border:1px solid #436781;border-radius:12px;padding:11px 14px;font:14px/1.5 ui-monospace,monospace;white-space:pre-line;display:none}
.legend{display:flex;align-items:center;gap:12px;margin:18px 0;color:#acc5d4;font-size:14px;flex-wrap:wrap}.gradient{width:220px;height:12px;border-radius:20px;background:linear-gradient(90deg,#59a9f5,#b1c1cb,#ff786d)}
.info{border-top:1px solid #294457;padding-top:19px;margin-top:22px;font-size:14px;color:#abc2d0}a{color:#74dfed}strong{color:#e8f7fa}
</style></head><body><main>
<small class="eyebrow">SCIENTIFIC PYTHON / SYNTHETIC DATA LAB</small>
<h1>Explore simulated magnetic changes in 3D</h1>
<p><strong>100% fictional stations and measurements.</strong> Rotate the Earth, change the UTC snapshot, and switch between sampled regional medians and local vector-change directions. Cells with fewer than two stations are not shaded. No magnetic field is interpolated between locations.</p>
<div class="controls"><fieldset><legend>UTC time</legend><button id="t17" class="active" type="button">17:00</button><button id="t18" type="button">18:00</button></fieldset><fieldset><legend>Visualisation</legend><button id="zones" class="active" type="button">Regional medians</button><button id="vectors" type="button">Vector changes</button><button id="points" type="button">Station ΔH</button></fieldset><button id="reset" type="button">Reset view</button></div>
<div class="viewer"><canvas id="globe" width="1150" height="650" role="img" aria-label="Interactive 3D globe of fictional observatories. Use buttons to switch time and visualisation. Drag to rotate."></canvas><div id="tip"></div></div>
<div class="legend"><span id="metric">COLOUR: regional ΔH median (nT)</span><span class="gradient"></span><span>negative • zero • positive</span><span id="counts"></span></div>
<div class="info">The event-style data are generated by deterministic equations; the dates 9 and 10 May 2024 are purely illustrative. X = north, Y = east, Z = down. Arrow lengths are normalized. HTML, CSS, JavaScript and synthetic data are entirely embedded. No accounts, external libraries, analytics, CDN or network access. The accompanying source project includes tests and reproduction instructions.</div>
</main><script>
'use strict';
const DATA=__JSON_DATA__;
const canvas=document.getElementById('globe'), ctx=canvas.getContext('2d');
const tip=document.getElementById('tip'),counts=document.getElementById('counts'),metric=document.getElementById('metric');
let when='17:00',mode='zones',yaw=-22*Math.PI/180,pitch=12*Math.PI/180,zoom=1;
let dragging=false,startX=0,startY=0,hot=[];
const W=canvas.width,H=canvas.height,cx=W*.5,cy=H*.5+25;
function latlon(lat,lon){let a=lat*Math.PI/180,b=lon*Math.PI/180;return [Math.cos(a)*Math.cos(b),Math.cos(a)*Math.sin(b),Math.sin(a)];}
function cam(v){let c=Math.cos(yaw),s=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);const x=-s*v[0]+c*v[1],front=c*v[0]+s*v[1];return [x,sp*-front+cp*v[2],cp*front+sp*v[2]];}
function point(lat,lon){let p=cam(latlon(lat,lon)),r=257*zoom;return {x:cx+r*p[0],y:cy-r*p[1],z:p[2]};}
function color(value,lim){if(value===null)return '#1b3545';const t=Math.min(1,Math.abs(value)/lim),n=[177,193,203],ex=value>0?[255,112,101]:[79,167,250];return '#'+n.map((v,i)=>Math.round(v*(1-t)+ex[i]*t).toString(16).padStart(2,'0')).join('');}
function zone(lat,lon){return [Math.min(5,Math.floor((lat+90)/30)),Math.min(5,Math.floor((lon+180)/60))];}
function buildZones(rows){const sums=new Map();for(const row of rows){const [a,b]=zone(row.latitude_deg,row.longitude_deg),key=a+'-'+b;let v=sums.get(key)||[];v.push(row.delta_h_nt);sums.set(key,v);}const out=[];for(let a=0;a<6;a++)for(let b=0;b<6;b++){const values=(sums.get(a+'-'+b)||[]).slice().sort((x,y)=>x-y),n=values.length;out.push({a,b,n,median:n>=2?(n%2?values[(n-1)/2]:(values[n/2]+values[n/2-1])/2):null});}return out;}
function clipVisible(poly){let out=[];for(let i=0;i<poly.length;i++){const a=poly[(i+poly.length-1)%poly.length],b=poly[i],inside=a.z>=0,insideNext=b.z>=0;if(inside!==insideNext){const t=a.z/(a.z-b.z);out.push({x:a.x+t*(b.x-a.x),y:a.y+t*(b.y-a.y),z:0});}if(insideNext)out.push(b);}return out;}
function polygonForCell(a,b){const lat=-90+a*30,lon=-180+b*60,points=[];for(let u=0;u<60;u+=5)points.push(point(lat,lon+u));for(let u=0;u<30;u+=5)points.push(point(lat+u,lon+60));for(let u=60;u>0;u-=5)points.push(point(lat+30,lon+u));for(let u=30;u>0;u-=5)points.push(point(lat+u,lon));return clipVisible(points);}
function drawPolygon(poly,fill,stroke){if(poly.length<3)return;ctx.beginPath();ctx.moveTo(poly[0].x,poly[0].y);for(let i=1;i<poly.length;i++)ctx.lineTo(poly[i].x,poly[i].y);ctx.closePath();ctx.fillStyle=fill;ctx.fill();ctx.strokeStyle=stroke;ctx.lineWidth=.8;ctx.stroke();}
function drawGrid(){ctx.save();ctx.strokeStyle='#43708688';ctx.lineWidth=.7;for(let lat=-60;lat<=60;lat+=30){let points=[];for(let lon=-180;lon<=180;lon+=2){const p=point(lat,lon);if(p.z>=0)points.push(p);else{if(points.length>1)drawLine(points);points=[];}}if(points.length>1)drawLine(points);}for(let lon=-180;lon<180;lon+=30){let points=[];for(let lat=-90;lat<=90;lat+=2){const p=point(lat,lon);if(p.z>=0)points.push(p);else{if(points.length>1)drawLine(points);points=[];}}if(points.length>1)drawLine(points);}ctx.restore();}
function drawLine(pts){ctx.beginPath();ctx.moveTo(pts[0].x,pts[0].y);for(let i=1;i<pts.length;i++)ctx.lineTo(pts[i].x,pts[i].y);ctx.stroke();}
function vecScreen(row){const a=row.latitude_deg*Math.PI/180,b=row.longitude_deg*Math.PI/180,n=[-Math.sin(a)*Math.cos(b),-Math.sin(a)*Math.sin(b),Math.cos(a)],e=[-Math.sin(b),Math.cos(b),0],d=[-Math.cos(a)*Math.cos(b),-Math.cos(a)*Math.sin(b),-Math.sin(a)];const v=[0,1,2].map(i=>n[i]*row.delta_x_nt+e[i]*row.delta_y_nt+d[i]*row.delta_z_nt);return cam(v);}
function draw(){let rows=DATA[when],zones=buildZones(rows);hot=[];ctx.clearRect(0,0,W,H);const r=257*zoom;const grad=ctx.createRadialGradient(cx-r*.45,cy-r*.55,r*.03,cx,cy,r*1.12);grad.addColorStop(0,'#335f73');grad.addColorStop(.48,'#1b3f52');grad.addColorStop(1,'#091a29');ctx.fillStyle=grad;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.fill();
if(mode==='zones')for(const z of zones){let p=polygonForCell(z.a,z.b);drawPolygon(p,z.median===null?'#153043':color(z.median,150),'#29495e');}
ctx.save();ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.clip();drawGrid();ctx.restore();
for(const row of rows){const p=point(row.latitude_deg,row.longitude_deg);if(p.z<0)continue;const [a,b]=zone(row.latitude_deg,row.longitude_deg),z=zones[a*6+b];let marker='#f8faff';if(mode==='zones'&&z.n===1)marker='#ffd87e';if(mode==='points')marker=color(row.delta_h_nt,150);
if(mode==='vectors'){const v=vecScreen(row),len=Math.hypot(v[0],v[1]);if(len>.00001){const scale=(20+9*Math.min(1,row.delta_b_nt/190))/len,ex=p.x+v[0]*scale,ey=p.y-v[1]*scale,theta=Math.atan2(ey-p.y,ex-p.x);ctx.strokeStyle=color(row.delta_b_nt,190);ctx.lineWidth=2.4;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(ex,ey);ctx.moveTo(ex-8*Math.cos(theta-.5),ey-8*Math.sin(theta-.5));ctx.lineTo(ex,ey);ctx.lineTo(ex-8*Math.cos(theta+.5),ey-8*Math.sin(theta+.5));ctx.stroke();}}
ctx.beginPath();ctx.fillStyle=marker;ctx.strokeStyle='#0c2738';ctx.lineWidth=1;ctx.arc(p.x,p.y,mode==='points'?5:3.3,0,Math.PI*2);ctx.fill();ctx.stroke();hot.push({p,row,zone:z});}
ctx.strokeStyle='#8dbdd0';ctx.lineWidth=2;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.stroke();
ctx.fillStyle='#e7f7ff';ctx.font='bold 23px system-ui';ctx.fillText('Invented observatories: '+rows.length+' usable',45,53);ctx.font='15px system-ui';ctx.fillStyle='#acc7d7';ctx.fillText('Rotate: drag  •  Zoom: wheel  •  Hover: inspect station',45,82);
const covered=zones.filter(z=>z.n>=2).length,single=zones.filter(z=>z.n===1).length;counts.textContent=rows.length+' simulated stations · '+covered+' coloured zones · '+single+' single-station cells';metric.textContent=mode==='zones'?'COLOUR: station-supported median ΔH (nT)':mode==='vectors'?'COLOUR: vector-change magnitude |ΔB| (nT)':'COLOUR: station ΔH (nT)';}
function choose(id,field,value,ids){document.getElementById(id).addEventListener('click',()=>{if(field==='time')when=value;else mode=value;for(const key of ids)document.getElementById(key).classList.toggle('active',key===id);draw();});}
choose('t17','time','17:00',['t17','t18']);choose('t18','time','18:00',['t17','t18']);for(const id of ['zones','vectors','points'])choose(id,'mode',id,['zones','vectors','points']);
document.getElementById('reset').addEventListener('click',()=>{yaw=-22*Math.PI/180;pitch=12*Math.PI/180;zoom=1;draw();});
canvas.addEventListener('pointerdown',ev=>{dragging=true;startX=ev.clientX;startY=ev.clientY;canvas.setPointerCapture(ev.pointerId);});
canvas.addEventListener('pointermove',ev=>{if(dragging){yaw+=(ev.clientX-startX)*.007;pitch=Math.max(-1.3,Math.min(1.3,pitch-(ev.clientY-startY)*.006));startX=ev.clientX;startY=ev.clientY;draw();tip.style.display='none';}else{const rect=canvas.getBoundingClientRect(),x=(ev.clientX-rect.left)*W/rect.width,y=(ev.clientY-rect.top)*H/rect.height;let near=hot.filter(h=>Math.hypot(h.p.x-x,h.p.y-y)<12).sort((a,b)=>Math.hypot(a.p.x-x,a.p.y-y)-Math.hypot(b.p.x-x,b.p.y-y))[0];if(near){tip.textContent=near.row.station+' (fictional)\nLat '+near.row.latitude_deg.toFixed(1)+'°, Lon '+near.row.longitude_deg.toFixed(1)+'°\nΔH '+near.row.delta_h_nt.toFixed(1)+' nT\nΔX '+near.row.delta_x_nt.toFixed(1)+' / ΔY '+near.row.delta_y_nt.toFixed(1)+' / ΔZ '+near.row.delta_z_nt.toFixed(1)+' nT\nZone sample size '+near.zone.n;tip.style.display='block';}else tip.style.display='none';}});
canvas.addEventListener('pointerup',()=>dragging=false);canvas.addEventListener('pointercancel',()=>dragging=false);canvas.addEventListener('pointerleave',()=>{if(!dragging)tip.style.display='none';});
canvas.addEventListener('wheel',ev=>{ev.preventDefault();zoom=Math.max(.65,Math.min(1.18,zoom*(ev.deltaY>0?.93:1.07)));draw();},{passive:false});
draw();
</script></body></html>
'''
    return template.replace('__JSON_DATA__',data)
