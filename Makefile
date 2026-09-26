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
