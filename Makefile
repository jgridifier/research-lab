PYTHON = .venv/bin/python
TRACK = tracks/y9c-panel
VENV_STAMP = .venv/.y9c-requirements.stamp

.PHONY: y9c-venv y9c-data y9c-notebook y9c-page y9c y9c-test

$(VENV_STAMP): $(TRACK)/requirements.txt
	test -x $(PYTHON) || python3 -m venv .venv
	.venv/bin/pip install -r $(TRACK)/requirements.txt
	touch $@

y9c-venv: $(VENV_STAMP)

y9c-data: $(VENV_STAMP)
	$(PYTHON) $(TRACK)/scripts/download_y9c.py
	$(PYTHON) $(TRACK)/scripts/build_y9c_panel.py

y9c-notebook: $(VENV_STAMP)
	$(PYTHON) -m ipykernel install --prefix .venv --name y9c-venv --display-name 'Y-9C (.venv)'
	.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=y9c-venv --ExecutePreprocessor.timeout=600 $(TRACK)/notebooks/y9c_nii_forecast.ipynb

y9c-page: $(VENV_STAMP)
	$(PYTHON) $(TRACK)/scripts/render_results_page.py

y9c:
	$(MAKE) y9c-venv
	$(MAKE) y9c-data
	$(MAKE) y9c-notebook
	$(MAKE) y9c-page

y9c-test: $(VENV_STAMP)
	PYTHONPATH=$(TRACK) $(PYTHON) -m pytest $(TRACK)/tests -q

SF_TRACK = tracks/statement-forecast

.PHONY: statement-forecast-test statement-forecast-notebook statement-forecast-page statement-forecast

statement-forecast-test: $(VENV_STAMP)
	PYTHONPATH=$(TRACK):$(SF_TRACK) $(PYTHON) -m pytest $(SF_TRACK)/tests -q

statement-forecast-notebook: $(VENV_STAMP)
	$(PYTHON) -m ipykernel install --prefix .venv --name y9c-venv --display-name 'Y-9C (.venv)'
	.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=y9c-venv --ExecutePreprocessor.timeout=600 $(SF_TRACK)/notebooks/statement_forecast_eb.ipynb

statement-forecast-page: $(VENV_STAMP)
	$(PYTHON) $(SF_TRACK)/scripts/render_results_page.py

statement-forecast:
	$(MAKE) y9c-venv
	$(MAKE) y9c-data
	$(MAKE) statement-forecast-notebook
	$(MAKE) statement-forecast-page

.PHONY: statement-forecast-combo-test statement-forecast-combo-notebook statement-forecast-combo-page statement-forecast-combo

statement-forecast-combo-test: $(VENV_STAMP)
	PYTHONPATH=$(TRACK):$(SF_TRACK) $(PYTHON) -m pytest $(SF_TRACK)/tests/test_combo_*.py $(SF_TRACK)/tests/test_published_v1_outputs.py -q

statement-forecast-combo-notebook: $(VENV_STAMP)
	$(PYTHON) -m ipykernel install --prefix .venv --name y9c-venv --display-name 'Y-9C (.venv)'
	.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=y9c-venv --ExecutePreprocessor.timeout=1800 $(SF_TRACK)/notebooks/statement_forecast_combo.ipynb

statement-forecast-combo-page: $(VENV_STAMP)
	$(PYTHON) $(SF_TRACK)/scripts/render_combo_results_page.py

statement-forecast-combo:
	$(MAKE) y9c-venv
	$(MAKE) y9c-data
	$(MAKE) statement-forecast-combo-notebook
	$(MAKE) statement-forecast-combo-page

TOT_TRACK = tracks/y9c-trading-ot
TOT_PATH = $(TRACK):$(SF_TRACK):$(TOT_TRACK):$(TOT_TRACK)/tests

.PHONY: trading-ot-venv trading-ot-test trading-ot-panel trading-ot-page

trading-ot-venv: $(VENV_STAMP)
	.venv/bin/pip install -r $(TOT_TRACK)/requirements.txt

trading-ot-test: trading-ot-venv
	OMP_NUM_THREADS=1 PYTHONPATH=$(TOT_PATH) $(PYTHON) -m pytest -c $(TOT_TRACK)/pytest.ini $(TOT_TRACK)/tests -q

trading-ot-panel: trading-ot-venv
	OMP_NUM_THREADS=1 PYTHONPATH=$(TOT_PATH) $(PYTHON) -m trading_ot.run panel

trading-ot-page: trading-ot-venv
	PYTHONPATH=$(TOT_PATH) $(PYTHON) $(TOT_TRACK)/scripts/render_results_page.py
