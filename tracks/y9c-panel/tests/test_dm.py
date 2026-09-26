import numpy as np
import pytest
from scipy.stats import t

from y9c.forecast import clustered_dm, dm_tests


def test_hand_computed_cr1():
    # Mean 4; centered cluster sums -5, -1, 6; sum of squares 62.
    result = clustered_dm([1, 2, 3, 4, 6, 8], [0, 0, 1, 1, 2, 2])
    se = np.sqrt(1.5 * 62 / 36)
    assert result['n'] == 6
    assert result['G'] == 3
    assert result['df'] == 2
    assert result['mean_diff'] == 4
    assert result['se'] == pytest.approx(se)
    assert result['t_stat'] == pytest.approx(4 / se)
    assert result['p_value'] == pytest.approx(2 * t.sf(4 / se, 2))


@pytest.mark.parametrize('sign,favored', [(-1, 'naive'), (1, 'pooled_ar')])
def test_sign(sign, favored):
    result = clustered_dm(sign * np.arange(1, 7), [0, 0, 1, 1, 2, 2])
    assert np.sign(result['mean_diff']) == sign
    assert result['favored'] == favored


def test_cluster_aggregation():
    d = np.array([1, 2, 3, 4, 6, 8])
    labels = [0, 0, 1, 1, 2, 2]
    original = clustered_dm(d, labels)
    permuted = clustered_dm(d[[1, 0, 3, 2, 5, 4]], labels)
    assert permuted['t_stat'] == pytest.approx(original['t_stat'])
    merged = clustered_dm(d, [0, 0, 0, 0, 1, 1])
    assert merged['se'] != pytest.approx(original['se'])


@pytest.mark.parametrize('d,clusters', [([1, 2], [0, 0]), ([], [])])
def test_too_few_clusters(d, clusters):
    result = clustered_dm(d, clusters)
    assert np.isnan(result['t_stat'])
    assert np.isnan(result['p_value'])
    assert result['note'] == 'undefined (G<2)'


@pytest.mark.parametrize('d', [[1, 1, 1], [0, 0, 0]])
def test_zero_se(d):
    result = clustered_dm(d, [0, 1, 2])
    assert result['se'] == 0
    assert np.isnan(result['t_stat'])
    assert np.isnan(result['p_value'])
    assert result['note'] == 'undefined (se=0)'
    if d[0] == 0:
        assert result['favored'] == 'tie'


def test_cluster_degrees_of_freedom():
    result = clustered_dm([1, 2, 3, 7, 8, 9], [0, 0, 0, 1, 1, 1])
    assert result['df'] == 1
    assert result['p_value'] == pytest.approx(2 * t.sf(abs(result['t_stat']), df=1))
    assert result['p_value'] != pytest.approx(2 * t.sf(abs(result['t_stat']), df=5))


def test_matched_cases_and_target_quarters():
    import pandas as pd
    cases = pd.DataFrame({'actual': [10, 10, 10, 10], 'naive': [11, 12, 13, 14],
                          'pooled_ar': [12, 14, 16, 18],
                          'target_quarter': pd.period_range('2025Q3', periods=4, freq='Q'),
                          'target_year': [2025, 2025, 2026, 2026]})
    rows = dm_tests(cases)
    assert len(rows) == 6
    full = rows[rows.scope.eq('full')]
    assert full.n.eq(4).all() and full.G.eq(4).all()
    assert full.mean_diff.tolist() == [-2.5, -22.5]
    assert rows[rows.scope.ne('full')].inference.eq('descriptive only (G=2)').all()
