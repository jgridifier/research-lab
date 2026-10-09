#!/bin/sh
# Re-render the CP funding program pages from their pinned sources. Pass --check to verify without writing.
set -e
cd "$(dirname "$0")/.."
python3 scripts/render_lab_plan.py programs/cp-funding/LAB_PLAN_cp_funding_2026-10-09.md docs/programs/cp-funding/plan.html \
  --title "Research Lab plan: CP funding forecasts (2026-10-09)" --nav "CP funding: lab plan" \
  --sha256 d78c176ef63adeef012f0dcda5768cdd371490918cded1c618f7d47ce091d2d9 \
  --source-label programs/cp-funding/LAB_PLAN_cp_funding_2026-10-09.md \
  --extra-link ../../tracks/fed-cp-ot/index.html "Fed CP prereg" \
  --extra-link ../../tracks/fed-cp-ot/learning.html "Fed CP learning page" "$@"
python3 scripts/render_lab_plan.py tracks/fed-cp-ot/prereg/PREREG_fed_cp_ot.md docs/tracks/fed-cp-ot/index.html \
  --title "Fed CP maturity mix × OT: Passed burn-in, pinned, awaiting Jared's approval" --nav "Fed CP maturity mix × OT" \
  --sha256 e3da87af2da1002b0635959d751dad4b885c59c985edc3b3a23612fa5bee0ecf \
  --source-label tracks/fed-cp-ot/prereg/PREREG_fed_cp_ot.md \
  --status "Passed burn-in, pinned, awaiting Jared's approval" \
  --note "No out-of-sample (held-out) run has been made, and none starts without a separate approval file. The design keeps oos_authorized: false, which is a record, not the switch." \
  --extra-link learning.html "learning page" \
  --extra-link ../../programs/cp-funding/plan.html "CP funding lab plan" \
  --pin PIN.txt 65032235646fb984f2b0a0b66f100b5257b239f4e66ac7c4a9f2f079aab419da \
  --pin test_design_fed_cp_ot_v1.json 6c87f7ab5efe3a220cb1c50497e3a9edd7435de5965aff4a20f8f6f1b2ce7793 \
  --pin PREREG_fed_cp_ot.md e3da87af2da1002b0635959d751dad4b885c59c985edc3b3a23612fa5bee0ecf \
  --pin fed_cp_ot_learning.html 44e77a0c51476724947386a4fc9686af9caea4ccba9c37ae4ad61f50374f5fc7 \
  --pin GATE_THRESHOLDS_fed_cp_ot.md c15eb60cbe1467090fcc920b8f4e311dd14f7b3bbfd0437e21809355721a6c8a \
  --pin DATA_SPEC_for_app.md 9c50a16e994cdb04e2598b270800e2941d027e314b375e33cbf5caa98f102c6c \
  --pin ENGINEERING_TICKET.md 088d9f2e72a162daf25436b2c76c3b4cfe6b93abd0082d480b5f94befa86346d "$@"
