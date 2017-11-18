import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from subprocess import call
mm_file_name = 'GlicemiaMisurazioni.csv'
mm_file_name_gz = mm_file_name + '.gz'

call(['gunzip', mm_file_name_gz])

headers = [
    'record_ver',
    'time',
    'location',
    'weight',
    'raw_gluc',
    'cal_gluc',
    'type',
    'mm_zone',
    'insulin_u',
    'insulin_type',
    'blood',
    'injection_zone',
    'notes'
]

def date_parser(inp):
    out = [dateutil.parser.parse(x.replace('.',':').replace('/','.')) for x in inp]
    return out;

#mm_file = gzip.open(mm_file_name_gz)
mm_raw = pd.read_csv(mm_file_name, 
                     encoding='utf-16-le',
                     sep=';', 
                     header=None, 
                     names=headers,
                     index_col=1,
                    parse_dates=True,
                    date_parser=date_parser)

def event_to_curve(base, event_name, curve_name, event_duration):
    base = pd.DataFrame(base)
    base[curve_name] = 0
    event_off_name = curve_name + 'wears_off'
    base[event_off_name] = 0

    for x in base.index:
        u = base.loc[x,event_name]
        if u > 0:
            xwo = x + event_duration
            if xwo not in base.index:
                base.loc[xwo] = [np.nan for n in base]
                base.loc[xwo, event_off_name] = 0
            base.loc[xwo, event_off_name] += u

    insulin_level = 0
    base = base.sort_index()
    for x in base.index:
        if not pd.isnull(base.loc[x,event_name]):
            insulin_level += base.loc[x,event_name]
        if not pd.isnull(base.loc[x,event_off_name]):
            insulin_level -= base.loc[x,event_off_name]
        base.loc[x,curve_name] = insulin_level
    return base

def dayplot(date):
    mdt = mm_raw[date]
    mdt = event_to_curve(mdt, 'insulin_u', 'insulin_total', pd.to_timedelta(4, unit='h'))

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax2 = ax.twinx()
    mdt.plot(
        ax=ax,
        y=['cal_gluc', 'raw_gluc'],
        color=['C0','#bbbbbb'],
        style=['-','--']
    )
    finger = mdt[mdt.type == 0]
    finger.plot(ax=ax, y='raw_gluc', color='red', style='.', markersize=20)
    #insu = mdt[mdt.insulin_u > 0]
    #insu.plot(ax=ax2, y='insulin_u', color='orange', style='.', markersize=20)
    mdt.plot(ax=ax2, y='insulin_total', color='orange')