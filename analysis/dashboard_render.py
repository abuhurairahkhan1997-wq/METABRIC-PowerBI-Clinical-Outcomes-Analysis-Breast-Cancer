from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import imageio.v2 as imageio
f = pd.read_csv(ROOT/'data'/'fact_clinical_outcomes.csv')
for c in f.columns:
    if str(f[c].dtype) in ('Int64','Float64'): f[c]=f[c].astype(float)
    elif str(f[c].dtype)=='string': f[c]=f[c].astype(object)
BLUE='#2a78d6'; INK='#0b0b0b'; INK2='#52514e'; BG='#f3f2ef'; CARD='#ffffff'; GRID='#e4e3df'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11})
AGE=['Unknown','<40','40-49','50-59','60-69','70+']; NODE=['Unknown','Node-negative','1-3 positive nodes','4+ positive nodes']
def pct(a,b): return a/b if b else np.nan
def card(fig, x,y,w,h):
    fig.add_artist(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0,rounding_size=0.006',transform=fig.transFigure,fc=CARD,ec='#dddcd8',lw=0.8,zorder=0))
def style(ax,title,sub=None,dx=0):
    ax.text(dx,1.09 if sub else 1.04,title,transform=ax.transAxes,fontsize=13,color=INK,fontweight='bold')
    if sub: ax.text(dx,1.03,sub,transform=ax.transAxes,fontsize=9.5,color=INK2)
    for s in ['top','right','left']: ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#9a9993'); ax.tick_params(colors=INK2,length=0)
def render(d, label, path):
    fig = plt.figure(figsize=(19.2,10.8),dpi=100,facecolor=BG)
    fig.text(0.5,0.955,'METABRIC Breast Cancer Clinical Outcomes Dashboard',ha='center',fontsize=22,fontweight='bold',color=INK)
    ok=d[d.OS_KNOWN_FLAG==1]; rk=d[d.RFS_KNOWN_FLAG==1]
    kp=[('Total Patients',f"{d.PATIENT_ID.nunique():,}"),('Death Rate (all-cause)',f"{100*pct(ok.DEATH_FLAG.sum(),len(ok)):.1f}%"),
        ('Average Age at Diagnosis',f"{d.AGE_AT_DIAGNOSIS.mean():.1f}"),('Recurrence Rate',f"{100*pct(rk.RECURRENCE_FLAG.sum(),len(rk)):.1f}%"),
        ('Median Observed OS (years)',f"{d.OS_YEARS.median():.1f}"),('Median Observed RFS (years)',f"{d.RFS_YEARS.median():.1f}")]
    for i,(k,v) in enumerate(kp):
        x=40/1920+i*312/1920; y=1-195/1080; w=280/1920; h=105/1080; card(fig,x,y,w,h)
        fig.text(x+0.008,y+h-0.03,k,fontsize=11,color=INK2); fig.text(x+0.008,y+0.018,v,fontsize=26,fontweight='bold',color=INK)
    sl=['Age Band','Histological Subtype','Treatment Profile','Node Category']
    for i,s in enumerate(sl):
        x=40/1920+i*470/1920; y=1-285/1080; w=430/1920; h=70/1080; card(fig,x,y,w,h)
        val = label if (s=='Node Category' and label!='All') else 'All'
        fig.text(x+0.008,y+h-0.024,s,fontsize=10,color=INK2)
        fig.text(x+0.008,y+0.012,val+'   ▾',fontsize=12,color=BLUE if val!='All' else INK,fontweight='bold' if val!='All' else 'normal')
    boxes=[(40,305),(975,305),(40,665),(975,665)]
    axs=[]
    for j,(x,y) in enumerate(boxes):
        X=x/1920; Y=1-(y+340)/1080; W=905/1920; H=340/1080; card(fig,X,Y,W,H)
        lo = 0.135 if j==2 else 0.035
        axs.append(fig.add_axes([X+lo,Y+0.03 if j==2 else Y+0.05,W-lo-0.02,H-0.10 if j==2 else H-0.12]))
    # 1 age
    a=axs[0]; c=d.groupby('AGE_BAND_KEY').PATIENT_ID.nunique().reindex(AGE).fillna(0)
    b=a.bar(c.index,c.values,color=BLUE,width=0.6); a.bar_label(b,fmt='%d',color=INK,fontsize=10,padding=2); style(a,'Patients by Age Band'); a.set_yticks([]); a.margins(y=0.15)
    # 2 histology
    a=axs[1]; g=d.groupby('HISTOLOGICAL_SUBTYPE').agg(n=('PATIENT_ID','nunique'),k=('OS_KNOWN_FLAG','sum'),dd=('DEATH_FLAG','sum')); g=g[g.n>=10]; g['r']=g.dd/g.k; g=g.dropna().sort_values('r',ascending=False)
    b=a.bar([s.replace('Tubular/ cribriform','Tubular/cribriform') for s in g.index],100*g.r,color=BLUE,width=0.6); a.bar_label(b,fmt='%.1f%%',fontsize=9.5,color=INK,padding=2)
    style(a,'Observed All-Cause Death Rate by Histological Subtype','Subtypes under 10 patients hidden'); a.set_yticks([]); a.tick_params(axis='x',labelsize=9.5); a.margins(y=0.15)
    # 3 treatment
    a=axs[2]; g=d.groupby('TREATMENT_PROFILE_KEY').agg(n=('PATIENT_ID','nunique'),k=('RFS_KNOWN_FLAG','sum'),rr=('RECURRENCE_FLAG','sum')); g=g[g.n>=10]; g['r']=g.rr/g.k; g=g.dropna().sort_values('r')
    b=a.barh(g.index,100*g.r,color=BLUE,height=0.65); a.bar_label(b,fmt='%.1f%%',fontsize=8.5,color=INK,padding=3); style(a,'Observed Recurrence Rate by Treatment Profile','Chemo | Hormone | Radio | Surgery  ·  groups under 10 patients hidden',dx=-0.24)
    a.set_xticks([]); a.tick_params(axis='y',labelsize=8); a.spines['bottom'].set_visible(False); a.margins(x=0.12)
    # 4 node
    a=axs[3]; m=d.groupby('NODE_CATEGORY_KEY').OS_YEARS.median().reindex(NODE).dropna()
    b=a.bar(m.index,m.values,color=BLUE,width=0.55); a.bar_label(b,fmt='%.1f',fontsize=10,color=INK,padding=2); style(a,'Median Observed OS Follow-up Time by Node Category'); a.set_yticks([]); a.margins(y=0.15)
    fig.text(40/1920,40/1080,'Source: METABRIC clinical cohort, cBioPortal study brca_metabric (n = 2,509). Descriptive exploratory analysis; observed associations do not establish causation, treatment effectiveness or individual prognosis.',fontsize=9.5,color=INK2)
    fig.text(40/1920,18/1080,'Death rate is all-cause; rates use patients with known status as the denominator. Median OS/RFS are medians of observed follow-up time, not Kaplan–Meier estimates. Re-rendered in Python from the Power BI model data.',fontsize=9.5,color=INK2)
    fig.savefig(path,facecolor=BG); plt.close(fig)
render(f,'All',str(ROOT/'figures')+'/dashboard_overview.png')
frames=[]
for lab in ['All','Node-negative','1-3 positive nodes','4+ positive nodes']:
    d=f if lab=='All' else f[f.NODE_CATEGORY_KEY==lab]
    p=str(ROOT/'figures'/f'frame_{len(frames)}.png'); render(d,lab,p); frames.append(p)
from PIL import Image
ims=[Image.open(p).convert('RGB').resize((1280,720),Image.LANCZOS) for p in frames]
ims[0].save(str(ROOT/'figures')+'/dashboard_node_filter.gif',save_all=True,append_images=ims[1:],duration=2200,loop=0,optimize=True)
print('ok')
