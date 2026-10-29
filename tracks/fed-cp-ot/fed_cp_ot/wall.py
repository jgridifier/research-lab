"""The one scoring-wall guard. Every loader that returns observations goes through `wall_guard`."""
import json
import numpy as np
import pandas as pd
from .errors import ScoringWallError
from .paths import PREREG_DIR, SCORING_WALL


def oos_authorized(design_path=PREREG_DIR / 'test_design_fed_cp_ot_v1.json'):
    """The design record's flag (a record, not a switch)."""
    return json.loads(design_path.read_text())['oos_authorized'] is True


def readable(date, wall=SCORING_WALL):
    """True if an amount dated `date` (ISO text or Timestamp) may be converted to a number."""
    if wall is None:
        return True
    if isinstance(date, str) and isinstance(wall, str):
        return date <= wall  # ISO dates: fast path, parsed millions of times
    return pd.Timestamp(date) <= pd.Timestamp(wall)


def wall_guard(frame, wall=SCORING_WALL):
    """Return `frame` with every amount dated after `wall` blanked; raise if any slipped through.

    The frame keeps post-wall dates, series and validity (structural), never their values. `wall=None`
    is only for an issued OOS provenance and is passed by `parse.load_vol`, nowhere else.
    """
    if wall is None:
        return frame
    after = frame['date'] > pd.Timestamp(wall)
    out = frame.copy()
    out.loc[after, 'value'] = np.nan
    if out.loc[after, 'value'].notna().any():
        raise ScoringWallError('post-wall amount survived the guard')
    return out
