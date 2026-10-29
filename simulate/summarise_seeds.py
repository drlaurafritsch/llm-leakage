"""Compare a synthetic world's leakage estimates with its realised planted effect.

Usage:  python simulate/summarise_seeds.py simulate/runs/leak_s21 .

The planted effect varies by firm (recognition depends on fame) and by rung (the
masker can miss a short firm name), so the benchmark is the realised shift averaged
over the (document, model) pairs that identify gamma. Prints run, rung, planted,
estimate and SE for the pooled prediction task.
"""
import json, os, sys
import pandas as pd
W=sys.argv[1]; code=sys.argv[2]
sys.path.insert(0,code); os.chdir(code)
os.environ['LEAK_WORKDIR']=W; os.environ['LEAK_CONFIG_DIR']=W+'/config'
import simulate.world as sw
from masking.mask import mask_text
from coding.run_models import document_text
F={f['cik']:f for f in json.load(open(W+'/data/interim/sim_truth.json'))['firms']}
ents={json.loads(l)['cik']:json.loads(l) for l in open(W+'/data/interim/entities.jsonl')}
docs={}
for l in open(W+'/data/interim/documents.jsonl'):
    d=json.loads(l); docs[d['doc_id']]=d
lp=pd.read_csv(W+'/results/long_predict.csv',dtype={'doc_id':str})
le=pd.read_csv(W+'/results/leakage_estimates.csv'); le=le[(le.task=='predict')&(le.measure=='all_outcomes')].set_index('level')
out=[]
for level in ['raw','names','generalised']:
  g=lp[lp.level==level].copy()
  g['know']=((g.outcome==1)&(pd.to_datetime(g.event_date)<pd.to_datetime(g.cutoff))).astype(int)
  k=g.groupby('unit').know.agg(['min','max']); ident=set(k.index[k['max']>k['min']])
  texts={}
  def shift(r):
    if not r.know: return 0.0
    f=F[int(r.cik)]
    if f['event_type']!=r.measure: return 0.0
    if r.doc_id not in texts:
        d=docs[r.doc_id]; t=document_text(d)
        texts[r.doc_id]= t if level=='raw' else mask_text(t, ents.get(d['cik'],{}), level)
    rec=sw._recognise(texts[r.doc_id], r.model)
    return 0.3 if (rec and rec['cik']==f['cik']) else 0.0
  s=g[(g.know==1)&g.unit.isin(ident)].apply(shift,axis=1).mean()
  print(f"{os.path.basename(W)},{level},{s:.4f},{le.loc[level,'gamma']:.4f},{le.loc[level,'se']:.4f}",flush=True)
