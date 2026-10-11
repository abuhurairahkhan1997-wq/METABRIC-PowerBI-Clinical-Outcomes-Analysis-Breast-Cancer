from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from statsmodels.duration.survfunc import SurvfuncRight
S=pd.read_pickle(ROOT/'data'/'surv.pkl'); O=pd.read_pickle(ROOT/'data'/'results.pkl')
INK='#0b0b0b'; INK2='#52514e'; BLUE='#2a78d6'; GREY='#a3a29c'; GRID='#e4e3df'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.edgecolor':'#9a9993','axes.labelcolor':INK2,'xtick.color':INK2,'ytick.color':INK2})
D=str(ROOT/'figures')+'/'
# Fig 2 KM
NODE=[('Node-negative',0.35),('1-3 positive nodes',0.65),('4+ positive nodes',1.0)]
fig,axs=plt.subplots(1,3,figsize=(15,5.2),sharey=True)
for ax,(lab,d,tcol,ev,tt) in zip(axs,[('Overall survival',S['os_'],'OS_MONTHS','DEATH_FLAG','All-cause death'),('Disease-specific survival',S['os_'],'OS_MONTHS','dss','Death from breast cancer'),('Relapse-free survival',S['rfs'],'RFS_MONTHS','RECURRENCE_FLAG','Recurrence')]):
    for g,a in NODE:
        dd=d[d.NODE_CATEGORY_KEY==g]; s=SurvfuncRight(dd[tcol].values/12, dd[ev].values)
        x=np.r_[0,s.surv_times]; y=np.r_[1,s.surv_prob]
        ax.step(x,100*y,where='post',color=BLUE,alpha=a,lw=2,label=f'{g} (n = {len(dd):,})')
    ax.set_title(lab,loc='left',fontsize=13,color=INK,fontweight='bold',pad=20); ax.text(0,1.015,f'Event: {tt.lower()}',transform=ax.transAxes,fontsize=9.5,color=INK2,va='bottom')
    ax.set_xlim(0,25); ax.set_ylim(0,100); ax.set_xlabel('Years from diagnosis'); ax.grid(axis='y',color=GRID); ax.spines[['top','right']].set_visible(False)
    ax.axvline(10,color=GREY,lw=0.8,ls='--')
axs[0].set_ylabel('Patients event-free (%)'); axs[0].legend(frameon=False,loc='lower left',fontsize=9.5)
fig.suptitle('Survival separates sharply by nodal status: 10-year disease-specific survival 81% (node-negative) vs 43% (4+ nodes)',x=0.01,ha='left',fontsize=13.5,color=INK)
fig.text(0.01,0.005,'Kaplan–Meier estimates; dashed line marks 10 years. Patients with unknown nodal status not shown. Source: METABRIC (cBioPortal brca_metabric).',fontsize=9,color=INK2)
fig.tight_layout(rect=(0,0.03,1,0.93)); fig.savefig(D+'fig2_km_by_node.png',dpi=200); plt.close(fig)
# Fig 3 age
t=O['age']; t=t[t.group!='Unknown']
fig,ax=plt.subplots(figsize=(10,5.4)); x=np.arange(len(t)); w=0.36
for off,col,c,lab in [(-w/2,'death',BLUE,'All-cause death'),(w/2,'dsd',GREY,'Death from breast cancer')]:
    v=np.array([r[0] for r in t[col]]); lo=np.array([r[1] for r in t[col]]); hi=np.array([r[2] for r in t[col]])
    ax.bar(x+off,v,w*0.92,color=c,label=lab); ax.errorbar(x+off,v,yerr=[v-lo,hi-v],fmt='none',ecolor=INK2,lw=1,capsize=3)
    for xi,vi in zip(x+off,v): ax.text(xi,2,f'{vi:.0f}%',ha='center',va='bottom',fontsize=9.5,color='white' if c==BLUE else INK,fontweight='bold')
ax.set_xticks(x,[f'{g}\n(n = {k:,})' for g,k in zip(t.group,t.os_known)]); ax.set_ylim(0,100); ax.set_ylabel('Patients with known survival status (%)')
ax.spines[['top','right']].set_visible(False); ax.grid(axis='y',color=GRID); ax.set_axisbelow(True); ax.legend(frameon=False,loc='upper left')
ax.set_title('All-cause death rises from 40% to 79% with age; death from breast cancer stays near 31–34% after 40',loc='left',fontsize=12.5,color=INK)
fig.text(0.01,0.01,'Bars: observed proportions; whiskers: Wilson 95% confidence intervals. Age at diagnosis. Source: METABRIC (cBioPortal brca_metabric).',fontsize=9,color=INK2)
fig.tight_layout(rect=(0,0.03,1,1)); fig.savefig(D+'fig3_death_by_age.png',dpi=200); plt.close(fig)
# Fig 4 forest
fig,axs=plt.subplots(1,3,figsize=(15,4.6),sharey=True)
for ax,(k,lab) in zip(axs,[('cox_os','Overall survival'),('cox_dss','Disease-specific survival'),('cox_rfs','Relapse-free survival')]):
    r=O[k]['res'][::-1]; y=np.arange(len(r))
    for yi,(n,hr,lo,hi,p) in zip(y,r):
        c=BLUE if lo>1 or hi<1 else GREY
        ax.plot([lo,hi],[yi,yi],color=c,lw=2); ax.plot(hr,yi,'o',color=c,ms=8)
        ax.text(5.6,yi,f'{hr:.2f} ({lo:.2f}–{hi:.2f})',va='center',fontsize=9.5,color=INK)
    ax.axvline(1,color=INK2,lw=0.8); ax.set_xscale('log'); ax.set_xlim(0.7,5.0); ax.set_xticks([0.8,1,1.5,2,3,4]); ax.set_xticklabels(['0.8','1','1.5','2','3','4'])
    ax.set_title(f'{lab}\nn = {O[k]["n"]:,}; events = {O[k]["events"]:,}',loc='left',fontsize=11.5,color=INK); ax.spines[['top','right']].set_visible(False); ax.set_xlabel('Hazard ratio (log scale)')
axs[0].set_yticks(np.arange(5),[n for n,*_ in O['cox_os']['res'][::-1]])
fig.suptitle('Four or more positive nodes carries the largest adjusted hazard in every model',x=0.01,ha='left',fontsize=13.5,color=INK)
fig.text(0.01,0.01,'Cox proportional hazards models, complete cases. References: node-negative, ER-positive, no chemotherapy. Blue: 95% CI excludes 1. Chemotherapy estimates reflect confounding by indication, not treatment harm.',fontsize=9,color=INK2)
fig.tight_layout(rect=(0,0.04,0.94,0.92)); fig.savefig(D+'fig4_cox_forest.png',dpi=200); plt.close(fig)
print('ok')
