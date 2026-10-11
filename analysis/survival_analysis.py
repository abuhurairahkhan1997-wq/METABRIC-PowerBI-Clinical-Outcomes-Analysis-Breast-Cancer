from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import pandas as pd, numpy as np, json
from scipy import stats
from statsmodels.duration.survfunc import SurvfuncRight, survdiff
from statsmodels.duration.hazard_regression import PHReg
f = pd.read_csv(ROOT/'data'/'fact_clinical_outcomes.csv')
for c in f.columns:
    if str(f[c].dtype) in ('Int64','Float64'): f[c] = f[c].astype(float)
    elif str(f[c].dtype)=='string': f[c] = f[c].astype(object)
out = {}
def wilson(k, n, z=1.96):
    if n == 0: return (np.nan,)*3
    p = k/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d; h = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return 100*p, 100*(c-h), 100*(c+h)
def rate_table(col, order=None):
    rows=[]
    g = f.groupby(col)
    for k, d in g:
        ok = d[d.OS_KNOWN_FLAG==1]; rk = d[d.RFS_KNOWN_FLAG==1]
        dth = wilson(ok.DEATH_FLAG.sum(), len(ok)); dss = wilson((ok.VITAL_STATUS=='Died of Disease').sum(), len(ok)); rec = wilson(rk.RECURRENCE_FLAG.sum(), len(rk))
        rows.append(dict(group=k, n=len(d), os_known=len(ok), death=dth, dsd=dss, rfs_known=len(rk), rec=rec))
    df = pd.DataFrame(rows)
    if order: df = df.set_index('group').loc[[o for o in order if o in set(df.group)]].reset_index()
    return df
NODE=['Node-negative','1-3 positive nodes','4+ positive nodes','Unknown']; AGE=['<40','40-49','50-59','60-69','70+','Unknown']
for name,col,order in [('node','NODE_CATEGORY_KEY',NODE),('age','AGE_BAND_KEY',AGE),('hist','HISTOLOGICAL_SUBTYPE',None)]:
    t = rate_table(col, order); out[name] = t
    print(f'== {name}'); print(t.to_string(formatters={c:(lambda v: f'{v[0]:.1f} ({v[1]:.1f}-{v[2]:.1f})' if not np.isnan(v[0]) else '-') for c in ['death','dsd','rec']}))
# Cochran-Armitage trend on recurrence across known node categories
def ca(df, score_map, event, known):
    d = df[df[known]==1]; d = d[d.NODE_CATEGORY_KEY.isin(score_map)]
    s = d.NODE_CATEGORY_KEY.map(score_map).values; y = d[event].values; N=len(y); p=y.mean()
    T = np.sum(s*(y-p)); V = p*(1-p)*(np.sum(s*s) - np.sum(s)**2/N)
    z = T/np.sqrt(V); return z, 2*stats.norm.sf(abs(z))
sm={'Node-negative':0,'1-3 positive nodes':1,'4+ positive nodes':2}
print('CA trend recurrence', ca(f, sm, 'RECURRENCE_FLAG','RFS_KNOWN_FLAG'))
print('CA trend death', ca(f, sm, 'DEATH_FLAG','OS_KNOWN_FLAG'))
# age: chi-square all-cause vs disease-specific (known age bands)
ok = f[(f.OS_KNOWN_FLAG==1)&(f.AGE_BAND_KEY!='Unknown')]
for lab, ev in [('all-cause', ok.DEATH_FLAG), ('disease-specific', (ok.VITAL_STATUS=='Died of Disease').astype(int))]:
    ct = pd.crosstab(ok.AGE_BAND_KEY, ev); chi, p, dof, _ = stats.chi2_contingency(ct); print('age', lab, round(chi,1), dof, p)
# Survival
os_ = f.dropna(subset=['OS_MONTHS']); os_ = os_[os_.OS_KNOWN_FLAG==1]
os_['dss'] = (os_.VITAL_STATUS=='Died of Disease').astype(int)
rfs = f.dropna(subset=['RFS_MONTHS']); rfs = rfs[rfs.RFS_KNOWN_FLAG==1]
# median follow-up by reverse KM
rev = SurvfuncRight(os_.OS_MONTHS.values, 1-os_.DEATH_FLAG.values); print('median follow-up (reverse KM) months', rev.quantile(0.5), 'years', rev.quantile(0.5)/12)
km = {}
for lab, d, ev in [('OS', os_, 'DEATH_FLAG'), ('DSS', os_, 'dss'), ('RFS', rfs, 'RECURRENCE_FLAG')]:
    km[lab] = {}
    for g in NODE:
        dd = d[d.NODE_CATEGORY_KEY==g]
        s = SurvfuncRight(dd[('OS_MONTHS' if lab!='RFS' else 'RFS_MONTHS')].values, dd[ev].values)
        med = s.quantile(0.5); ci = s.quantile_ci(0.5)
        t10 = s.surv_prob[np.searchsorted(s.surv_times, 120, side='right')-1]
        km[lab][g] = dict(n=len(dd), events=int(dd[ev].sum()), median_y=med/12 if med==med else None, ci=[c/12 if c==c and c is not None else None for c in ci], s10=float(t10))
        print(lab, g, len(dd), int(dd[ev].sum()), 'median yrs', None if med!=med else round(med/12,1), [None if (c is None or c!=c) else round(c/12,1) for c in ci], '10y surv', round(100*t10,1))
    known = d[d.NODE_CATEGORY_KEY!='Unknown']
    tcol = 'OS_MONTHS' if lab!='RFS' else 'RFS_MONTHS'
    chi, p = survdiff(known[tcol].values, known[ev].values, known.NODE_CATEGORY_KEY.values); print(lab,'logrank', round(chi,1), p)
pd.to_pickle(dict(os_=os_, rfs=rfs), ROOT/'data'/'surv.pkl')
# Cox models (complete case)
def cox(d, tcol, ev, label):
    x = d[(d.NODE_CATEGORY_KEY!='Unknown')&(d.AGE_BAND_KEY!='Unknown')&(d.ER_IHC.isin(['Positive','Negative']))&(d.CHEMOTHERAPY_.isin(['Yes','No']))].copy()
    X = pd.DataFrame({'Age (per 10 years)': x.AGE_AT_DIAGNOSIS/10,
                      '1-3 positive nodes': (x.NODE_CATEGORY_KEY=='1-3 positive nodes').astype(float),
                      '4+ positive nodes': (x.NODE_CATEGORY_KEY=='4+ positive nodes').astype(float),
                      'ER negative': (x.ER_IHC=='Negative').astype(float),
                      'Chemotherapy': (x.CHEMOTHERAPY_=='Yes').astype(float)})
    r = PHReg(x[tcol].values, X.values, status=x[ev].values, ties='efron').fit()
    ci = r.conf_int()
    print(f'== Cox {label} n={len(x)} events={int(x[ev].sum())}')
    res=[]
    for i,c in enumerate(X.columns):
        res.append((c, np.exp(r.params[i]), np.exp(ci[i][0]), np.exp(ci[i][1]), r.pvalues[i])); print(f'{c:22s} HR {np.exp(r.params[i]):.2f} ({np.exp(ci[i][0]):.2f}-{np.exp(ci[i][1]):.2f}) p={r.pvalues[i]:.3g}')
    return dict(n=len(x), events=int(x[ev].sum()), res=res)
for d in (os_, rfs): d['CHEMOTHERAPY_'] = d.TREATMENT_PROFILE_KEY.str.split(' | ', regex=False).str[0]
out['cox_os']=cox(os_, 'OS_MONTHS','DEATH_FLAG','OS'); out['cox_dss']=cox(os_, 'OS_MONTHS','dss','DSS'); out['cox_rfs']=cox(rfs,'RFS_MONTHS','RECURRENCE_FLAG','RFS')
# chemo stratified by node
f['chemo'] = f.TREATMENT_PROFILE_KEY.str.split(' | ', regex=False).str[0]
rk = f[(f.RFS_KNOWN_FLAG==1)&(f.chemo.isin(['Yes','No']))&(f.NODE_CATEGORY_KEY!='Unknown')]
st = rk.groupby(['NODE_CATEGORY_KEY','chemo']).agg(n=('PATIENT_ID','count'), rec=('RECURRENCE_FLAG','sum')); st['rec%']=(100*st.rec/st.n).round(1); print(st)
ch = f[f.chemo.isin(['Yes','No'])]
print(ch.groupby('chemo').agg(n=('PATIENT_ID','count'),age=('AGE_AT_DIAGNOSIS','mean'),er_neg=('ER_IHC',lambda s:(s=='Negative').mean()),n4=('NODE_CATEGORY_KEY',lambda s:(s=='4+ positive nodes').mean())))
print('ER', f.ER_IHC.value_counts(dropna=False).to_dict())
print('age median IQR', f.AGE_AT_DIAGNOSIS.median(), f.AGE_AT_DIAGNOSIS.quantile([.25,.75]).tolist())
print('nodes median', f.LYMPH_NODES_EXAMINED_POSITIVE.median())
pd.to_pickle(out,ROOT/'data'/'results.pkl')
