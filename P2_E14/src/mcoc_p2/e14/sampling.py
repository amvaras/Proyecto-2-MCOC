"""Una realización es una historia material/clima completa, compartida entre planes."""
import numpy as np
from ..e13.risk import weights
from .io import fingerprint
def sample_one(master_seed,realization,scenarios):
    if type(master_seed)is not int or not 0<=master_seed<2**64 or type(realization)is not int or not 0<=realization<2**32:raise ValueError('Semilla uint64 e ID uint32')
    if len({s['id'] for s in scenarios})!=len(scenarios):raise ValueError('No duplicar átomos')
    w=weights([s['weight'] for s in scenarios]);seq=np.random.SeedSequence([master_seed,realization]);seed=seq.generate_state(4,dtype=np.uint32)
    rng=np.random.Generator(np.random.PCG64(seq));u=float(rng.random());cdf=np.cumsum(w);cdf[-1]=1.;index=int(np.searchsorted(cdf,u,side='right'))
    return dict(realization=realization,seed_words=seed.tolist(),scenario_index=index,scenario=scenarios[index]['id'],uniform=u)
def sample_bank(master_seed,n,scenarios,ids=None):
    if type(n)is not int or not 1<=n<=100000:raise ValueError('N entre 1 y 100000')
    ids=list(range(n)) if ids is None else list(ids)
    if len(ids)!=n or len(set(ids))!=n:raise ValueError('IDs únicos')
    rows=[sample_one(master_seed,i,scenarios) for i in ids]
    if len({tuple(r['seed_words']) for r in rows})!=n:raise ValueError('Colisión de semillas; detener antes de ejecutar')
    return dict(master_seed=master_seed,N=n,bit_generator='PCG64',numpy=np.__version__,derivation='SeedSequence([master_seed,realization_id]); no depende del orden',
        model_fingerprint=fingerprint(scenarios),paired_across_plans=True,meaning='Muestreo IID condicional del modelo discreto; repetición de un átomo no es un ensayo experimental nuevo',samples=rows)
