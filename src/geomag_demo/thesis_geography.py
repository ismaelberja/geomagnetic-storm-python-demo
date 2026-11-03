"""Thesis-inspired geographic-component visualizations using FICTIONAL stations only.

Reference: fictional 9 May 24-hour mean; event: fictional 10 May maximum
absolute departure from that reference. Values are NOT 2024 observations.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date
from html import escape
from statistics import mean,median
import math

from .synthetic import STATIONS, BASE_DAY, EVENT_DAY, horizontal, xyz

COLOURS={'bg':'#071526','panel':'#0f2c40','grid':'#315369','ink':'#eff9ff','muted':'#a0becd','blue':'#6bdbea','salmon':'#f18e7a','grey':'#33485b'}


def fictional_elevation(station):
    """Entirely invented training covariate; occasional None means missing metadata."""
    if not station.code.startswith('SIM-'):
        raise ValueError('Only artificial SIM stations supported')
    try:index=int(station.code.split('-')[1])
    except (IndexError, ValueError) as e:raise ValueError('Invalid synthetic identifier') from e
    if index%9==0:return None
    return float(40+(index*277)%1790)


def components(sample):
    x,y,z=sample
    return {'X':x,'Y':y,'Z':z,'H':horizontal(sample)}


def difference_at_peak(values,reference):
    if not values:raise ValueError('No valid synthetic event observations')
    # The sign at the point of greatest absolute departure is retained.
    return max((v-reference for v in values),key=lambda a:abs(a))


def synthetic_component_peaks(stations=STATIONS):
    names=set();result=[]
    for s in stations:
        if s.code in names:raise ValueError('Duplicate station')
        names.add(s.code)
        quiet={name:[] for name in ('X','Y','Z','H')}
        storm={name:[] for name in ('X','Y','Z','H')}
        for day, target in ((BASE_DAY,quiet),(EVENT_DAY,storm)):
            for minute in range(1440):
                sample=xyz(s,day,minute)
                if sample is None:continue
                for name,value in components(sample).items():target[name].append(value)
        if min(len(quiet['H']),len(storm['H']))<1200:continue
        row={'station':s.code,'latitude_deg':s.latitude,'longitude_deg':s.longitude,
             'invented_elevation_m':fictional_elevation(s),'n_reference':len(quiet['H']),
             'n_event':len(storm['H'])}
        for name in ('X','Y','Z','H'):
            signed=difference_at_peak(storm[name],mean(quiet[name]))
            row['signed_at_peak_'+name]=signed
            row['peak_abs_'+name]=abs(signed)
        result.append(row)
    return result


def svg_start(w,h,title,subtitle):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="FICTIONAL {escape(title)}">',
        f'<title>{escape(title)} · ALL VALUES AND POSITIONS SYNTHETIC</title>',
        f'<rect width="{w}" height="{h}" fill="{COLOURS["bg"]}"/>',
        f'<text x="48" y="63" font-family="Arial,sans-serif" font-size="29" font-weight="700" fill="{COLOURS["ink"]}">{escape(title)}</text>',
        f'<text x="48" y="94" font-family="Arial,sans-serif" font-size="15" fill="{COLOURS["muted"]}">{escape(subtitle)}</text>']


def scatter_panel(parts,rows,component,axis,rect,label,lo,hi):
    x0,y0,w,h=rect
    vals=[r[f'peak_abs_{component}'] for r in rows if r[axis] is not None]
    ymax=max(1,max(vals,default=1)*1.08)
    parts.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="12" fill="{COLOURS["panel"]}" stroke="{COLOURS["grid"]}"/>')
    parts.append(f'<text x="{x0+20}" y="{y0+29}" fill="{COLOURS["ink"]}" font-family="Arial,sans-serif" font-size="19">{escape(label)}</text>')
    parts.append(f'<text x="{x0+20}" y="{y0+51}" fill="{COLOURS["muted"]}" font-family="Arial,sans-serif" font-size="13">Peak absolute Δ{component} (nT), n={len(vals)}</text>')
    for fract in (0,.25,.5,.75,1):
        y=y0+h-47-fract*(h-107)
        parts.append(f'<path d="M{x0+55} {y:.2f} H{x0+w-22}" stroke="{COLOURS["grid"]}" stroke-dasharray="3 6"/>')
        parts.append(f'<text x="{x0+49}" y="{y+4:.2f}" fill="{COLOURS["muted"]}" font-family="Arial,sans-serif" font-size="12" text-anchor="end">{fract*ymax:.0f}</text>')
    for row in rows:
        if row[axis] is None:continue
        x=x0+55+(float(row[axis])-lo)/(hi-lo)*(w-78)
        y=y0+h-47-float(row[f'peak_abs_{component}'])/ymax*(h-107)
        colour=COLOURS['blue'] if row['latitude_deg']>=0 else COLOURS['salmon']
        parts.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.1" fill="{colour}" opacity=".75"><title>{escape(row["station"])}: peak Δ{component}={row[f"signed_at_peak_{component}"]:+.2f} nT (fictional)</title></circle>')
    for t in (0,.5,1):
        x=x0+55+t*(w-78)
        parts.append(f'<text x="{x:.1f}" y="{y0+h-23}" fill="{COLOURS["muted"]}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12">{lo+(hi-lo)*t:.0f}</text>')
    parts.append(f'<text x="{x0+w/2:.1f}" y="{y0+h-4}" fill="{COLOURS["muted"]}" text-anchor="middle" font-family="Arial,sans-serif" font-size="12">{escape(axis.replace("_deg"," (degrees)").replace("invented_elevation_m","Invented elevation (m)"))}</text>')


def component_latitude_svg(rows):
    w,h=1380,1050;p=svg_start(w,h,'Component-dependent variation with latitude','X / Y / Z / H · peak response to artificial 10 May event vs fictional 9 May quiet daily mean')
    for i,k in enumerate(('H','X','Y','Z')):
        scatter_panel(p,rows,k,'latitude_deg',(54+(i%2)*656,132+(i//2)*427,614,402),f'{k} variation × signed latitude',-90,90)
    p.append(f'<text x="54" y="1025" font-family="Arial,sans-serif" font-size="14" fill="{COLOURS["muted"]}">COMPLETELY SYNTHETIC · no polynomial trend inference, source observations or geomagnetic-latitude conversion.</text>')
    return '\n'.join(p+['</svg>'])+'\n'


def longitude_altitude_svg(rows):
    w,h=1420,660;p=svg_start(w,h,'Longitude and elevation: fictional covariate checks','Peak horizontal deviation from an artificial 9 May baseline; altitudes are invented placeholders')
    scatter_panel(p,rows,'H','longitude_deg',(50,135,648,460),'H response vs longitude',-180,180)
    subset=[r for r in rows if r['invented_elevation_m'] is not None]
    scatter_panel(p,rows,'H','invented_elevation_m',(724,135,648,460),'H response vs invented elevation',0,1800)
    p.append(f'<text x="50" y="640" font-family="Arial,sans-serif" font-size="12" fill="{COLOURS["muted"]}">All elevations fabricated; missing values are excluded (not zero). No physical longitude/altitude effects inferred.</text>')
    return '\n'.join(p+['</svg>'])+'\n'


def angular_diff_deg(a,b):
    # Correct circular difference in degrees, for example +179° to -179° is +2°.
    return math.degrees(math.atan2(math.sin(math.radians(a-b)),math.cos(math.radians(a-b))))


def declination_by_hour(stations=STATIONS):
    cells={}
    for s in stations:
        band=min(5,max(0,int((s.latitude+90)//30)))
        for hour in range(24):
            q=[];e=[]
            for minute in range(60*hour,60*(hour+1)):
                a=xyz(s,BASE_DAY,minute);b=xyz(s,EVENT_DAY,minute)
                if a is None or b is None:continue
                q.append(math.degrees(math.atan2(a[1],a[0])));e.append(math.degrees(math.atan2(b[1],b[0])))
            if len(q)<50:continue
            diff=angular_diff_deg(median(e),median(q))
            cells.setdefault((band,hour),[]).append(diff)
    return {k:{'count':len(v),'median_delta_d_deg':median(v) if len(v)>=3 else None} for k,v in cells.items()}


def declination_svg(data):
    w,h=1480,725;p=svg_start(w,h,'Declination: latitude × UTC time','Median angular ΔD (degrees) from fictional 9 May, paired hour by hour on 10 May')
    x0,y0,cw,ch=182,152,48,62
    values=[abs(d['median_delta_d_deg']) for d in data.values() if d['median_delta_d_deg'] is not None]
    scale=max(.001,max(values,default=0))
    def colour(val):
        if val is None:return COLOURS['grey']
        t=min(1,abs(val)/scale)
        rgb=((54,145,190) if val<0 else (231,130,100))
        return '#'+''.join(f'{round(218*(1-t)+z*t):02x}' for z in rgb)
    for band in range(6):
        y=y0+(5-band)*ch
        p.append(f'<text x="{x0-14}" y="{y+36}" text-anchor="end" fill="{COLOURS["ink"]}" font-size="15" font-family="Arial,sans-serif">{-90+30*band:+d}°…{-60+30*band:+d}°</text>')
        for h in range(24):
            row=data.get((band,h),{});val=row.get('median_delta_d_deg')
            p.append(f'<rect x="{x0+h*cw}" y="{y}" width="{cw}" height="{ch}" fill="{colour(val)}" stroke="#18344a" stroke-width=".6"><title>Lat band {band}, {h:02}:00 UTC, median ΔD={val if val is not None else "missing"}, n={row.get("count",0)} (synthetic)</title></rect>')
    for h in range(0,24,2):
        p.append(f'<text x="{x0+(h+.5)*cw}" y="{y0+6*ch+24}" text-anchor="middle" fill="{COLOURS["muted"]}" font-family="Arial,sans-serif" font-size="13">{h:02}</text>')
    p.append(f'<text x="{x0+12*cw}" y="{y0+6*ch+57}" text-anchor="middle" font-family="Arial,sans-serif" font-size="16" fill="{COLOURS["ink"]}">10 May (fictional) · UTC hour</text>')
    p.append(f'<text x="48" y="642" font-family="Arial,sans-serif" font-size="14" fill="{COLOURS["muted"]}">Blue: negative, coral: positive; neutral: near zero; dark: fewer than 3 independent simulated stations.</text>')
    p.append(f'<text x="48" y="672" font-family="Arial,sans-serif" font-size="13" fill="{COLOURS["muted"]}">Colour limits ±{scale:.4f}°; no global declination interpolation and no claim about the 2024 storm.</text>')
    return '\n'.join(p+['</svg>'])+'\n'


def render_all():
    peaks=synthetic_component_peaks()
    decl=declination_by_hour()
    figures={'synthetic_component_latitude.svg':component_latitude_svg(peaks),
             'synthetic_longitude_altitude.svg':longitude_altitude_svg(peaks),
             'synthetic_declination_latitude_time.svg':declination_svg(decl)}
    meta={'source':'FICTIONAL EQUATIONS ONLY: NOT REAL INTERMAGNET STATIONS OR OBSERVATIONS',
          'stations':len(peaks),'quiet_day':'2024-05-09 artificial','event_day':'2024-05-10 artificial',
          'metric':'Peak |component(t) minus 9 May daily mean| for H, X, Y, Z',
          'invented_elevation_available':sum(r['invented_elevation_m'] is not None for r in peaks),
          'invented_elevation_missing':sum(r['invented_elevation_m'] is None for r in peaks),
          'declination_method':'hourly median circular difference D(10 May)-D(9 May); min 50 matched minutes and 3 station per band',
          'scientific_limitation':'Spatial patterns and fabricated elevations are not real scientific observations.'}
    return figures,meta
