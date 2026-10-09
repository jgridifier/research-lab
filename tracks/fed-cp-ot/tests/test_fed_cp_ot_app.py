import pytest
from synth import make_zip

def test_app(pins,tmp_path):
    from fed_cp_ot.app import build_app
    import re
    path=tmp_path/'app.html'
    build_app(path,make_zip(tmp_path/'s.zip')); first=path.read_text(); build_app(path,tmp_path/'s.zip')
    assert first==path.read_text()
    assert 'PLACEHOLDER' in first and '<script' not in first and 'http://' not in first and 'stylesheet' not in first
    assert all(d<='2008-12-26' for d in re.findall(r'Week ending (\d{4}-\d{2}-\d{2})',first))

def test_synthetic_app_fallback(tmp_path,monkeypatch):
    from fed_cp_ot import app
    def missing(): raise FileNotFoundError()
    monkeypatch.setattr(app,'latest_vintage',missing)
    path=app.build_app(tmp_path/'app.html')
    assert 'SYNTHETIC PLACEHOLDER DATA' in path.read_text()

def test_app_links_and_mobile_layout(tmp_path):
    from html.parser import HTMLParser
    from fed_cp_ot.app import build_app
    from fed_cp_ot.paths import SOURCE_URL
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.links=[]
        def handle_starttag(self, tag, attrs):
            self.links.extend(value for key,value in attrs if key in ('href','src'))
    page = build_app(tmp_path/'app.html',make_zip(tmp_path/'s.zip')).read_text()
    links=Links(); links.feed(page)
    assert set(links.links) == {'../learning.html','../index.html','../../../index.html',SOURCE_URL}
    assert '@media (min-width:' in page
    assert page.count('<table>') == 4 and page.count('Valid days:') == 4
    assert page.count('Week ending 2008-12-26') == 4

@pytest.mark.realdata
def test_app_pinned_reproduction(real_zip,tmp_path):
    from fed_cp_ot.app import build_app
    from fed_cp_ot.paths import ROOT
    output = build_app(tmp_path/'index.html',real_zip)
    assert output.read_bytes() == (ROOT/'docs/tracks/fed-cp-ot/app/index.html').read_bytes()
