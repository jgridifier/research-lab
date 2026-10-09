# DATA_SPEC for the daily CP maturity-mix app (Developer)

## Source
- **Primary:** https://www.federalreserve.gov/releases/cp/data/FRB_CP_xml.zip. Member `CP_data.xml` (SDMX-style XML; schema `CP_VOL.xsd`, `CP_RATES.xsd`). Checked HTTP 200 on 2026-10-09.
- **Alternative / human check:** Data Download Program, https://www.federalreserve.gov/datadownload/Choose.aspx?rel=CP.
- **Release pages:** https://www.federalreserve.gov/releases/cp/volumestats.htm and https://www.federalreserve.gov/releases/cp/rates.htm.
- **Timing (Fed About page):** updated daily and "typically posted with a one-day lag". The daily release is "usually available at 1:00 p.m. EST". This is not guaranteed.
  - Schedule a pull at 13:30 ET with retries until 18:00 ET.
  - Treat a missing day as missing. Never fill it forward into the object.
- **Revisions:** the About page says outstandings are revised continuously without notice. Store every daily vintage of the zip with its sha256 and fetch time. The volume and rate history may also change, so diff each vintage against the previous one and log the changes.

## Series used
- **VOL dataset (60 series; `FREQ=9` daily).**
  - Id pattern: `{GROUP}.{BUCKET}.{TIER}.{MEASURE}`.
  - GROUP/TIER pairs: `AB.*.AA` (CP_TYPE AAA), `FIN.*.AA` (FAA), `NONFIN.*.AA` (NAA), `NONFIN.*.A2P2` (NA2), `MKT.*.MKT` (M).
  - BUCKET: `1_4, 5_9, 10_20, 21_40, 41_80, GT80` (CP_MAT_RANGE 1, 5, 10, 21, 41, 81).
  - MEASURE: `AMT` (CP_VOL_TYPE D, $ millions; UNIT_MULT 1000000) or `VOL` (CP_VOL_TYPE N, number of issues).
  - The model uses the AAA, FAA, NAA and NA2 AMT and VOL series. M is used only for the stress comparator.
- **RATES dataset (24 series)**, used only for the stress comparator (spreads): `RIFSPP{NAA|NA2P2|FAA|AAA}D{01|07|15|30|60|90}_N.B`, in percent.

## Repair and validation rules
1. Parse the XML. **Do not use** derived CSVs that collapse NONFIN AA and A2/P2. Key on the attributes `CP_TYPE`, `CP_MAT_RANGE` and `CP_VOL_TYPE`, not on the label text.
2. `OBS_STATUS="ND"` or `OBS_VALUE=-9999` means missing (holiday or closure).
3. Fail the run if:
   - a value is negative or non-integer;
   - any series id is missing;
   - the set of attribute combinations changes.
4. Known historical gaps: NA2 on 2004-04-09 and 2004-12-24; NAA on 2004-12-24. Treat these as missing days.
5. **Weekly object:** a Monday–Friday week labelled by its Friday. Sum AMT and VOL over the valid days of each type. A type-week is usable if it has ≥3 valid days, ≥100 issues and amount > 0. The mix is AMT/total. Support: the log geometric midpoints of 1–4, 5–9, 10–20, 21–40, 41–80 and 81–270 days.
6. **Daily view in the app:** show the partial week to date, flagged "provisional". Forecasts are issued only on completed weeks, after Friday's data post (normally the following Monday at about 1 pm ET).
7. Never compute MKT as the sum of the four types; it is not that sum.
8. Zero buckets are common in FIN and NONFIN.GT80. ALR models use a 1e-4 share replacement, as in the pre-registration.
