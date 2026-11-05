"""PREREG v2 unit tests (T7): q_from_p edge cases, projection, LS discretization, ALR inverse, scoring rules."""
import math
import numpy as np
import pandas as pd
import pytest
from fed_cp_ot.metric import q_from_p, w2sq, project_qf, softmax_alr, alr, X_LOG
from fed_cp_ot import candidates as C
from fed_cp_ot import scoring as S

MIDS = (X_LOG[:-1] + X_LOG[1:]) / 2

@pytest.mark.parametrize('p', [[0]*6, [-0.1,1.1,0,0,0,0], [np.nan,1,0,0,0,0]])
def test_q_from_p_rejects_zero_negative_nonfinite(p):
    with pytest.raises(ValueError): q_from_p(p, X_LOG)

def test_q_from_p_single_atom_is_valid():
    c, v = q_from_p([0, 0, 5, 0, 0, 0], X_LOG)
    assert c.tolist() == [1.0] and v.tolist() == [X_LOG[2]]
    assert w2sq((c, v), (c, v)) == 0.0

def rand_qf(rng, n=7):
    c = np.sort(rng.random(n)); c[-1] = 1.0
    return c, np.sort(rng.uniform(0, 5.5, n))

def test_projection_idempotent_on_six_point_laws():
    rng = np.random.default_rng(1)
    for _ in range(200):
        p = rng.dirichlet(np.ones(6) * rng.choice([0.2, 1, 5]))
        assert np.allclose(project_qf(*q_from_p(p, X_LOG), X_LOG), p, atol=1e-12)

def test_projection_preserves_mass():
    rng = np.random.default_rng(2)
    for _ in range(200):
        assert abs(project_qf(*rand_qf(rng), X_LOG).sum() - 1) < 1e-12

def test_projection_tie_goes_to_lower_bucket():
    for i, m in enumerate(MIDS):
        p = project_qf(np.array([1.0]), np.array([m]), X_LOG)
        assert p[i] == 1.0
    just_above = project_qf(np.array([1.0]), np.array([MIDS[0] + 1e-9]), X_LOG)
    assert just_above[1] == 1.0

def test_projection_is_w2_nearest_among_random_six_point_laws():
    rng = np.random.default_rng(3)
    for _ in range(3):
        q = rand_qf(rng)
        best = w2sq(q, q_from_p(project_qf(*q, X_LOG), X_LOG))
        for _ in range(10_000):
            p = rng.dirichlet(np.ones(6) * rng.choice([0.1, 1.0]))
            assert best <= w2sq(q, q_from_p(p, X_LOG)) + 1e-12

def test_project_qf_rejects_non_quantile_function():
    with pytest.raises(ValueError): project_qf(np.array([0.5, 0.4]), np.array([1.0, 2.0]), X_LOG)

def test_ls_cutpoints_are_the_pinned_half_day_values():
    assert np.allclose(C.LS_CUTS, [1.5041, 2.2513, 3.0204, 3.7013, 4.3883], atol=5e-5)

def test_ls_discretization_sums_to_one_and_folds_tails():
    rng = np.random.default_rng(4)
    for _ in range(500):
        mu, sd = rng.uniform(-3, 9), math.exp(rng.uniform(-9, 3))
        p = C.normal_buckets(mu, sd)
        assert abs(p.sum() - 1) < 1e-12 and (p >= 0).all()
    assert C.normal_buckets(9.0, 0.5)[5] > 0.999 and C.normal_buckets(-3.0, 0.5)[0] > 0.999  # beyond 270 days folds into bucket 6

def test_alr_inverse_has_no_clipping_or_floor():
    z = np.array([-40.0, 0.0, 12.0, 3.0, -2.0])
    p = softmax_alr(z)
    assert abs(p.sum() - 1) < 1e-12 and p[1] < 1e-17            # exp(-40) survives; nothing is floored
    assert np.allclose(np.log(p[1:] / p[0]), z)

def test_alr_input_floor_is_applied_then_renormalised():
    a = alr([0.5, 0.5, 0, 0, 0, 0])
    p = np.array([0.5, 0.5, 1e-4, 1e-4, 1e-4, 1e-4]); p /= p.sum()
    assert np.allclose(a, np.log(p[1:] / p[0]))

def test_war_isotonic_step_is_noop_for_monotone_input():
    assert np.allclose(C._isotonic([1, 2, 3], [1, 1, 1]), [1, 2, 3])
    assert np.allclose(C._isotonic([3, 1, 2], [1, 1, 1]), [2, 2, 2])

def test_entry_order_and_no_extra_candidates():
    assert C.ENTRIES == ('P', 'EWMA0.1', 'EWMA0.2', 'EWMA0.3', 'EWMA0.5', 'EXP', 'LS', 'ALR-AR', 'ALR-VAR', 'MNL-AR',
                         'RIDGE0.1', 'RIDGE1.0', 'RIDGE10.0', 'RIDGE100.0', 'WAR', 'TMAR')
    assert C.NON_OT == C.ENTRIES[:-2]

# ---------------- scoring ----------------
def wk(n, start='2009-01-02'): return list(pd.date_range(start, periods=n, freq='W-FRI'))

def test_gain_is_ratio_of_sums_on_paired_weeks_only():
    w = wk(4)
    cand = {w[0]: 1.0, w[1]: 1.0, w[2]: 1.0}
    comp = {w[1]: 2.0, w[2]: 4.0, w[3]: 100.0}
    assert S.paired_weeks(cand, comp) == [w[1], w[2]]
    assert S.gain(cand, comp, S.paired_weeks(cand, comp)) == pytest.approx(1 - 2 / 6)

def test_subperiod_gain_restricts_pairs():
    w = wk(300)
    cand = {x: 1.0 for x in w}; comp = {x: 2.0 for x in w}
    r = S.evaluate_pair(cand, comp, test=False)
    assert r['n_pairs'] == 300 and r['G'] == pytest.approx(0.5)
    assert r['G_s']['2009-2014'] == pytest.approx(0.5) and r['G_s']['2021-2026'] is None

def test_fewer_than_800_pairs_is_incomplete_not_failed():
    w = wk(799)
    r = S.evaluate_pair({x: 1.0 for x in w}, {x: 2.0 for x in w})
    assert r['incomplete'] and r['p'] is None and '799' in r['incomplete_reason']
    assert not S.hurdles(r)['pairs_ge_800']

def test_phi_reject_rule_is_incomplete_without_extrapolation():
    rng = np.random.default_rng(5)
    e = rng.standard_normal(900); d = np.empty(900); d[0] = e[0]
    for t in range(1, 900): d[t] = 0.998 * d[t - 1] + e[t]
    assert abs(S.phi_hat(d)) >= 0.99
    w = wk(900)
    comp = {x: 10 + v for x, v in zip(w, d - d.min())}; cand = {x: 10.0 for x in w}
    r = S.evaluate_pair(cand, comp)
    assert r['incomplete'] and r['p'] is None and 'phi_hat' in r['incomplete_reason']

def test_grid_critical_values_interpolate_inside_grid_only():
    assert S.GRID[0] == -0.98 and S.GRID[-1] == 0.98 and len(S.GRID) == 197
    cv = list(np.linspace(1, 2, len(S.GRID)))
    assert S.grid_cv(cv, 0.0) == pytest.approx(1.5, abs=0.01)
    assert S.grid_cv(cv, 0.985) is None and S.grid_cv(cv, -0.99) is None

def test_complete_test_rejects_a_clear_gain_and_not_noise():
    rng = np.random.default_rng(6); w = wk(900)
    base = 1 + rng.random(900)
    good = S.evaluate_pair({x: b * 0.8 for x, b in zip(w, base)}, {x: b for x, b in zip(w, base)}, p_draws=4000, grid_draws=0)
    assert not good['incomplete'] and good['p'] < 0.001 and good['G'] == pytest.approx(0.2)
    noise = S.evaluate_pair({x: b for x, b in zip(w, base)}, {x: b + e for x, b, e in zip(w, base, rng.standard_normal(900) * .1)},
                            p_draws=4000, grid_draws=0)
    assert noise['p'] > 0.01  # fixed seed; a zero-mean differential is not rejected at any pinned level (0.05/2 and below)

def test_holm_step_down_and_incomplete_counts_as_p_one():
    assert S.holm([0.01, 0.04]) == [True, True]
    assert S.holm([0.03, 0.2]) == [False, False]          # 0.03 > 0.05/2
    assert S.holm([0.04, 0.001]) == [True, True]
    assert S.holm([None, 0.001]) == [False, True]          # family size stays 2: 0.001 <= 0.025
    assert S.holm([0.03, None]) == [False, False]

def test_claim_requires_every_hurdle():
    w = wk(900)
    base = {x: 1.0 + (i % 7) * .1 for i, x in enumerate(w)}
    losses = {'SEL': {x: v * 0.99 for x, v in base.items()}, 'P': base}   # a 1% gain is significant but under G > 0.02
    out = S.run_family('B', [('SEL', 'P')], losses, p_draws=2000, grid_draws=0)['SEL vs P']
    assert out['holm_reject'] and not out['hurdles']['G_gt_0.02'] and not out['claim']

def test_family_a_non_rejection_wording():
    out = S.run_family('A', [('WAR', 'B*')], {'WAR': {}, 'B*': {}})['WAR vs B*']
    assert out['wording'] == 'underpowered to detect a 5% gain (planning power ≈0.50); not evidence of no gain.'

def test_families_are_the_five_pinned_tests():
    labels = [f'{c} vs {k}' for _, pairs in S.FAMILIES for c, k in pairs]
    assert labels == ['WAR vs B*', 'TMAR vs B*', 'SEL vs P', 'KUMO_best vs SEL', 'KUMO_best vs P']
    assert S.HURDLE_G == 0.02 and S.MIN_PAIRS == 800 and S.PHI_REJECT == 0.99
