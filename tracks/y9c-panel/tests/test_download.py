from datetime import date
import io
import zipfile
import pytest
from y9c.download import quarters, fetch, valid_zip


def test_quarters_stop_at_completed_end():
    assert quarters(date(2026, 9, 25))[-1] == date(2026, 6, 30)
    assert quarters(date(2026, 9, 30))[-1] == date(2026, 9, 30)
    assert quarters(date(2018, 3, 30)) == []


def test_redirect_is_not_followed_and_has_actionable_error(tmp_path):
    class Session:
        def get(self, url, **kwargs):
            assert kwargs['allow_redirects'] is False
            return type('Response', (), {'status_code': 302, 'headers': {'Content-Type': 'text/html', 'Location': '/npw/Home/onError'}, 'content': b'<html>unpublished</html>'})()
    with pytest.raises(RuntimeError, match='status=302.*text/html') as error:
        fetch(Session(), tmp_path / 'BHCF20260930.zip')
    assert 'FinancialDataDownload' in str(error.value)
    assert 'first bytes=' in str(error.value)
    assert not list(tmp_path.iterdir())


def test_atomic_valid_zip_and_invalid_cached_file(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr('BHCF20180331.txt', 'RSSD9001^RSSD9999\n1^20180331\n')
    class Session:
        def get(self, url, **kwargs):
            return type('Response', (), {'status_code': 200, 'headers': {'Content-Type': 'application/zip'}, 'content': buffer.getvalue()})()
    path = tmp_path / 'BHCF20180331.zip'
    path.write_text('<html>blocked</html>')
    assert not valid_zip(path)
    fetch(Session(), path)
    assert valid_zip(path)
    assert not path.with_suffix('.partial').exists()


def test_cached_run_never_requests_or_sleeps(tmp_path, monkeypatch):
    from y9c import download
    monkeypatch.setattr(download, 'RAW', tmp_path)
    monkeypatch.setattr(download, 'quarters', lambda today: [date(2018, 3, 31)])
    with zipfile.ZipFile(tmp_path / 'BHCF20180331.zip', 'w') as z:
        z.writestr('BHCF20180331.txt', 'RSSD9001^RSSD9999\n1^20180331\n')
    def unexpected(*args, **kwargs):
        pytest.fail('Cached run must not make requests or sleep')
    monkeypatch.setattr(download.requests.Session, 'get', unexpected)
    monkeypatch.setattr(download.time, 'sleep', unexpected)
    assert download.main() == 0
