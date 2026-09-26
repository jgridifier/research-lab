import numpy as np
import pandas as pd
from y9c.panel import decumulate


def frame(ids, dates, values):
    return pd.DataFrame({'rssd_id': ids, 'report_date': pd.to_datetime(dates), 'ytd': values})


def test_complete_year_and_reset():
    data = frame([1]*5, ['2020-03-31','2020-06-30','2020-09-30','2020-12-31','2021-03-31'], [10,25,21,40,8])
    q, missing = decumulate(data, 'ytd')
    np.testing.assert_allclose(q, [10,15,-4,19,8])
    assert q.iloc[:4].sum() == 40
    assert not missing.any()


def test_missing_immediately_prior_quarter_and_entry():
    data = frame([1,1,1,2], ['2020-03-31','2020-09-30','2020-12-31','2020-06-30'], [10,30,45,7])
    q, missing = decumulate(data, 'ytd')
    np.testing.assert_allclose(q, [10,np.nan,15,np.nan], equal_nan=True)
    assert missing.tolist() == [False,True,False,True]


def test_missing_prior_value_and_no_cross_year_subtraction():
    data = frame([1]*4, ['2020-12-31','2021-03-31','2021-06-30','2021-09-30'], [40,np.nan,20,30])
    q, missing = decumulate(data, 'ytd')
    np.testing.assert_allclose(q, [np.nan,np.nan,np.nan,10], equal_nan=True)
    assert missing.tolist() == [True,False,True,False]


def test_unsorted_ids_preserve_input_alignment():
    data = frame([2,1,2,1], ['2020-06-30','2020-03-31','2020-03-31','2020-06-30'], [50,10,20,25])
    q, missing = decumulate(data, 'ytd')
    np.testing.assert_allclose(q, [30,10,20,15])
    assert not missing.any()


def test_negative_decumulation_after_positive_quarters():
    from y9c.panel import nii_discontinuities
    data = frame([1]*5 + [2]*3,
                 ['2020-03-31','2020-06-30','2020-09-30','2020-12-31','2021-03-31',
                  '2020-03-31','2020-09-30','2020-12-31'],
                 [10,25,21,20,-5,10,30,20])
    data['nii_q'], _ = decumulate(data, 'ytd')
    negative, after_positive = nii_discontinuities(data)
    assert negative.tolist() == [False,False,True,True,False,False,False,True]
    assert after_positive.tolist() == [False,False,True,False,False,False,False,False]
    # Year reset, previously negative quarters and missing quarters are not flagged.
    shuffled = data.sample(frac=1, random_state=7)
    assert nii_discontinuities(shuffled)[1].equals(after_positive.reindex(shuffled.index))
