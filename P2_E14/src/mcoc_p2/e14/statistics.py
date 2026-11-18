"""Bernoulli IID condicional al modelo discreto. IC exacto Clopper–Pearson."""
import math
import numpy as np
def limit_states(Tmax_C,delta_C):
    t=np.asarray(Tmax_C,float);d=np.asarray(delta_C,float)
    if t.shape!=d.shape or not np.isfinite(t).all() or not np.isfinite(d).all():raise ValueError('Métricas finitas con igual forma')
    gT=70-t;gD=20-d
    return dict(g_T=gT,g_Delta=gD,fail_T=gT<0,fail_delta=gD<0,fail_joint=(gT<0)|(gD<0))
def _fraction(a,b,x):
    qab=a+b;qap=a+1;qam=a-1;c=1.;d=1-qab*x/qap;small=1e-300
    if abs(d)<small:d=small
    d=1/d;h=d
    for m in range(1,501):
        aa=m*(b-m)*x/((qam+2*m)*(a+2*m));d=1+aa*d
        if abs(d)<small:d=small
        c=1+aa/c
        if abs(c)<small:c=small
        d=1/d;h*=d*c
        aa=-(a+m)*(qab+m)*x/((a+2*m)*(qap+2*m));d=1+aa*d
        if abs(d)<small:d=small
        c=1+aa/c
        if abs(c)<small:c=small
        d=1/d;delta=d*c;h*=delta
        if abs(delta-1)<3e-14:return h
    raise ArithmeticError('Beta no convergió')
def beta_cdf(x,a,b):
    if x<=0:return 0.
    if x>=1:return 1.
    bt=math.exp(math.lgamma(a+b)-math.lgamma(a)-math.lgamma(b)+a*math.log(x)+b*math.log1p(-x))
    return bt*_fraction(a,b,x)/a if x<(a+1)/(a+b+2) else 1-bt*_fraction(b,a,1-x)/b
def _quantile(p,a,b):
    lo=0.;hi=1.
    for _ in range(64):
        mid=(lo+hi)/2
        if beta_cdf(mid,a,b)<p:lo=mid
        else:hi=mid
    return (lo+hi)/2
def clopper_pearson(k,n,confidence=.95):
    if type(k) not in (int,np.int64,np.int32) or type(n) not in (int,np.int64,np.int32) or n<=0 or not 0<=k<=n:raise ValueError('0<=k<=N entero y N>0')
    if not 0<confidence<1:raise ValueError('Confianza entre cero y uno')
    alpha=1-confidence
    lower=0. if k==0 else (alpha/2)**(1/n) if k==n else _quantile(alpha/2,k,n-k+1)
    upper=1. if k==n else -math.expm1(math.log(alpha/2)/n) if k==0 else _quantile(1-alpha/2,k+1,n-k)
    return [lower,upper]
def zero_failure_upper(n,confidence=.95):
    if type(n)is not int or n<=0 or not 0<confidence<1:raise ValueError('N entero positivo y confianza válida')
    return -math.expm1(math.log1p(-confidence)/n)
def running_probability(failures,checkpoints=(10,20,50,100,200,500,1000,5000,10000),confidence=.95):
    f=np.asarray(failures)
    if f.ndim!=1 or f.dtype.kind!='b' or len(f)==0:raise ValueError('Indicadores booleanos IID, sin fallos numéricos omitidos')
    counts=np.cumsum(f,dtype=np.int64);points=sorted(set([int(x) for x in checkpoints if 0<x<=len(f)]+[len(f)]))
    return [dict(N=n,failures=int(counts[n-1]),Pf=float(counts[n-1]/n),CI=clopper_pearson(int(counts[n-1]),n,confidence),confidence=confidence) for n in points]
