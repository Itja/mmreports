# basic imports:
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

import urllib.request
import gzip
import zipfile
import dateutil.parser
from subprocess import call

# plot style definitions:
_CSV_HEADERS = [
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


def prog_init():
    mpl.rcParams['figure.figsize'] = (24.6, 14.6)
    mpl.rcParams.update({'font.size': 28})
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['grid.color'] = 'k'
    mpl.rcParams['grid.linestyle'] = ':'
    mpl.rcParams['grid.linewidth'] = 0.5


def fetch_data():
    url = 'https://www.dropbox.com/sh/6y58qwvah518k5t/AAALGDU9ELHO4sOGuNFd7qCMa/Glimp?dl=1'
    file_name = 'glimp-raw-data.zip'
    urllib.request.urlretrieve(url, file_name)

    zip_ref = zipfile.ZipFile(file_name, 'r')
    zip_ref.extractall()
    zip_ref.close()

    # measurements is abbreviated with 'mm' here:
    mm_file_name = 'GlicemiaMisurazioni.csv'
    mm_file_name_gz = mm_file_name + '.gz'

    #call(['gunzip','-f', mm_file_name_gz])
    mm_file_nozip = gzip.open(mm_file_name_gz)

    #mm_file = gzip.open(mm_file_name_gz)
    mm_raw = pd.read_csv(mm_file_nozip,
                         encoding='utf-16-le',
                         sep=';',
                         header=None,
                         names=_CSV_HEADERS,
                         index_col=1,
                         parse_dates=True,
                         date_parser=lambda inp: [dateutil.parser.parse(x.replace('.',':').replace('/','.')) for x in inp])

    return mm_raw


def event_to_curve(base, event_name, curve_name, event_duration):
    base = pd.DataFrame(base)
    base[curve_name] = 0
    event_off_name = curve_name + 'wears_off'
    base[event_off_name] = 0

    for x in base.index:
        u = base.loc[x, event_name]
        if u > 0:
            xwo = x + event_duration
            if xwo not in base.index:
                base.loc[xwo] = [np.nan for n in base]
                base.loc[xwo, event_off_name] = 0
            base.loc[xwo, event_off_name] += u

    insulin_level = 0
    base = base.sort_index()
    for x in base.index:
        if not pd.isnull(base.loc[x, event_name]):
            insulin_level += base.loc[x, event_name]
        if not pd.isnull(base.loc[x, event_off_name]):
            insulin_level -= base.loc[x, event_off_name]
        base.loc[x, curve_name] = insulin_level
    return base


def npdate2datetime(numpydate):
    from datetime import datetime, timedelta
    return datetime(1, 1, 1) + timedelta(days=numpydate - 1)


def dayplot(mm_raw, date):
    pddate = pd.Timestamp(date)
    pddate_end = pddate + pd.to_timedelta(24, unit='h')
    mdt = mm_raw[date]
    mdt = event_to_curve(mdt, 'insulin_u', 'insulin_total', pd.to_timedelta(4, unit='h'))

    fig = plt.figure()
    locs, labels = plt.xticks()
    print(locs)
    print(labels)
    ax = fig.add_subplot(111)
    ax2 = ax.twinx()

    mdt.plot(
        ax=ax,
        y=['cal_gluc', 'raw_gluc'],
        color=['C0', '#bbbbbb'],
        style=['-', '--'],
        title='Glucose concentration over time on {}'.format(date)
    )

    finger = mdt[mdt.type == 0]
    finger.plot(ax=ax, y='raw_gluc', color='red', style='.', markersize=20)
    # insu = mdt[mdt.insulin_u > 0]
    # insu.plot(ax=ax2, y='insulin_u', color='orange', style='.', markersize=20)
    mdt.plot(ax=ax2, y='insulin_total', color='orange')
    ax.set_xlim(pddate, pddate_end)

    ax.set_xticklabels([npdate2datetime(x).strftime('%H:%M') for x in ax.get_xticks()])
    ax.set_ylim(50, 350)
    ax2.set_ylim(0, 50)
    # ax.set_ylabel('RAM Usage in GiB')
    ax.set_ylabel('Glucose concentration mg/dL')
    ax.set_xlabel('')
    ax2.set_ylabel('Insulin Units')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, ['Glimp corr.', 'Glimp raw', 'Blood'], loc='upper left')
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, ['Insulin'], loc='upper right')
    plt.savefig('meow.png')

mm_raw = fetch_data()
dayplot(mm_raw, '2017-11-24')
# dayplot('2017-10-28')