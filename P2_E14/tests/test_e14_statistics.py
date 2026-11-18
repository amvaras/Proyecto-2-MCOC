"""Oráculos binomiales independientes, límites físicos y sampler reproducible."""
import math
import numpy as np
import pytest
from mcoc_p2.e14.statistics import limit_states,clopper_pearson,zero_failure_upper,beta_cdf,running_probability
from mcoc_p2.e14.sampling import sample_bank,sample_one
from mcoc_p2.e14.model import catalog
def test_joint_limit_states_and_threshold_equality():
    r=limit_states([70,71,60,71],[20,19,21,21])
    np.testing.assert_array_equal(r['g_T'],[0,-1,10,-1]);np.testing.assert_array_equal(r['fail_joint'],[False,True,True,True])
def test_exact_intervals_against_independent_binomial_small_N():
    for n in (2,8,24):
        for k in range(1,n):
            lo,hi=clopper_pearson(k,n)
            lower_tail=sum(math.comb(n,j)*lo**j*(1-lo)**(n-j) for j in range(k,n+1))
            upper_tail=sum(math.comb(n,j)*hi**j*(1-hi)**(n-j) for j in range(k+1))
            assert lower_tail==pytest.approx(.025,abs=3e-12);assert upper_tail==pytest.approx(.025,abs=3e-12)
    assert clopper_pearson(1,2)==pytest.approx([1-math.sqrt(.975),math.sqrt(.975)])
def test_zero_and_all_failures_have_nonzero_width_and_one_sided_bound():
    lo,hi=clopper_pearson(0,20);assert lo==0 and hi==pytest.approx(1-.025**(1/20))
    assert clopper_pearson(20,20)==pytest.approx([.025**(1/20),1])
    assert zero_failure_upper(59)<.05<zero_failure_upper(58)
    seq=running_probability(np.zeros(100,dtype=bool));assert seq[-1]['Pf']==0 and seq[-1]['CI'][1]>0
    for k,n in [(-1,5),(6,5),(0,0),(True,5)]:
        with pytest.raises(ValueError):clopper_pearson(k,n)
def test_sampler_order_independence_unique_seeds_and_declared_frequency():
    sc=catalog();a=sample_bank(20261119,10000,sc);back=sample_bank(20261119,10,sc,ids=list(range(9,-1,-1)))
    assert list(reversed(back['samples']))==a['samples'][:10]
    assert len({tuple(r['seed_words']) for r in a['samples']})==10000
    indices=np.array([r['scenario_index'] for r in a['samples']]);observed=np.bincount(indices,minlength=24)/10000;expected=np.array([s['weight'] for s in sc])
    assert np.max(abs(observed-expected))<.012  # Control de distribución, no inferencia material.
    assert sample_one(42,8,sc)==sample_one(42,8,sc) and sample_one(43,8,sc)!=sample_one(42,8,sc)
