

```python
%matplotlib inline

# basic imports:
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# plot style definitions:

mpl.rcParams['figure.figsize'] = (24.6, 14.6)
mpl.rcParams.update({'font.size': 28})
mpl.rcParams['axes.grid'] = True
mpl.rcParams['grid.color'] = 'k'
mpl.rcParams['grid.linestyle'] = ':'
mpl.rcParams['grid.linewidth'] = 0.5
```

# Glimp Plots

## Pull Glimp files from Dropbox



```python
import urllib.request
import gzip
import zipfile

url = 'https://www.dropbox.com/sh/6y58qwvah518k5t/AAALGDU9ELHO4sOGuNFd7qCMa/Glimp?dl=1'
file_name = 'glimp-raw-data.zip'
urllib.request.urlretrieve(url, file_name)

zip_ref = zipfile.ZipFile(file_name, 'r')
zip_ref.extractall()
zip_ref.close()
```


```python
import subprocess
print(subprocess.Popen("ls -la", shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8'))
```

    total 2588
    drwxrwxrwx  3 jovyan  1000    4096 Nov 22 23:34 .
    drwsrwsr-x 11 jovyan users    4096 Oct 29 13:30 ..
    -rw-r--r--  1 jovyan users   55617 Oct 29 13:28 g.csv.gz
    -rw-r--r--  1 jovyan users      99 Nov 22 23:31 GlicemiaAccessori.csv.gz
    -rw-r--r--  1 jovyan users     561 Nov 22 23:31 GlicemiaCalorie.csv.gz
    -rw-r--r--  1 jovyan users     131 Nov 22 23:31 GlicemiaInsuline.csv.gz
    -rw-r--r--  1 jovyan users    1395 Nov 22 23:31 GlicemiaMisurazioniCalorie.csv.gz
    -rw-r--r--  1 jovyan users 1681256 Nov 22 23:31 GlicemiaMisurazioni.csv
    -rw-r--r--  1 jovyan users     946 Nov 22 23:31 GlicemiaPatches.csv.gz
    -rw-r--r--  1 jovyan users     215 Nov 22 23:31 GlicemiaPunture.csv.gz
    -rw-r--r--  1 jovyan users  540204 Nov 22 23:33 glimp.ipynb
    -rw-r--r--  1 jovyan users  102570 Nov 22 23:31 glimp-raw-data.zip
    drwxr-xr-x  2 jovyan users    4096 Oct 29 12:36 .ipynb_checkpoints
    -rw-r--r--  1 jovyan users  224166 Oct 29 13:22 measurements.csv.gz
    



```python
# measurements is abbreviated with 'mm' here:
from subprocess import call
mm_file_name = 'GlicemiaMisurazioni.csv'
mm_file_name_gz = mm_file_name + '.gz'

call(['gunzip','-f', mm_file_name_gz])
```




    0




```python


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
                    
day0 = mm_raw['2017-10-28']
```


```python
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

def npdate2datetime(numpydate):
    from datetime import datetime,timedelta
    return datetime(1,1,1)+timedelta(days=numpydate-1)

def dayplot(date):
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
        color=['C0','#bbbbbb'],
        style=['-','--'],
        title='Glucose concentration over time on {}'.format(date)
    )
    
    finger = mdt[mdt.type == 0]
    finger.plot(ax=ax, y='raw_gluc', color='red', style='.', markersize=20)
    #insu = mdt[mdt.insulin_u > 0]
    #insu.plot(ax=ax2, y='insulin_u', color='orange', style='.', markersize=20)
    mdt.plot(ax=ax2, y='insulin_total', color='orange')
    ax.set_xlim(pddate, pddate_end)
    
    ax.set_xticklabels([npdate2datetime(x).strftime('%H:%M') for x in ax.get_xticks()])
    ax.set_ylim(50,350)
    ax2.set_ylim(0,50)
    #ax.set_ylabel('RAM Usage in GiB')
    ax.set_ylabel('Glucose concentration mg/dL')
    ax.set_xlabel('')
    ax2.set_ylabel('Insulin Units')
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, ['Glimp corr.', 'Glimp raw', 'Blood'], loc='upper left')
    handles, labels = ax2.get_legend_handles_labels()
    ax2.legend(handles, ['Insulin'], loc='upper right')

dayplot('2017-11-22')
#dayplot('2017-10-28')
```

    [ 0.   0.2  0.4  0.6  0.8  1. ]
    <a list of 6 Text xticklabel objects>



![png](output_7_1.png)



```python
dr = pd.date_range('20170301', periods=6, freq='Min')
s = pd.Series([1,2,3,4,5,6], index=dr)
s.at[dr[3]] = 99
s
t = pd.Timestamp(2017,3,5,7,33,20) + pd.to_timedelta(4, unit='h')
%pinfo t
```


```python
a = pd.DataFrame(mm_raw['2017-10-28']) #explicit copy, omit set warnings later on
a['insulin_total'] = 0
a['insulin_wears_off'] = 0

for x in a.index:
    u = a.loc[x,'insulin_u']
    if u > 0:
        xwo = x + pd.to_timedelta(4, unit='h')
        if xwo not in a.index:
            a.loc[xwo] = [np.nan for n in a]
            a.loc[xwo, 'insulin_wears_off'] = 0
        a.loc[xwo, 'insulin_wears_off'] += u
    
insulin_level = 0
a.sort_index(inplace=True)
for x in a.index:
    if not pd.isnull(a.loc[x,'insulin_u']):
        insulin_level += a.loc[x,'insulin_u']
    if not pd.isnull(a.loc[x,'insulin_wears_off']):
        insulin_level -= a.loc[x,'insulin_wears_off']
    a.loc[x,'insulin_total'] = insulin_level
        

a.plot(y='insulin_total')

#plt.xticks(range(24), range(24))
```




    <matplotlib.axes._subplots.AxesSubplot at 0x7f5500ed8ac8>




![png](output_9_1.png)



```python
x = 30
y = -3
x -= y if y > 0 else 0
x
```




    30


