import pytest
from support import build_adidas_release_html

from sneaker_launchpad.models import StoreName
from sneaker_launchpad.providers.adidas import parse_adidas_release_html
from sneaker_launchpad.providers.nike import CatalogFetchError


def test_parse_adidas_release_html_extracts_ld_json_products() -> None:
    releases = parse_adidas_release_html(build_adidas_release_html())

    assert len(releases) == 1
    release = releases[0]
    assert release.provider == StoreName.ADIDAS
    assert release.name == "Adizero Prime Test"
    assert release.style_code == "JR9999"


def test_parse_adidas_release_html_raises_when_waf_page_returned() -> None:
    blocked_page = """
    <html><body>
      <title>adidas</title>
      <h1>Unfortunately we are unable to give you access to our site at this time.</h1>
    </body></html>
    """

    with pytest.raises(CatalogFetchError):
        parse_adidas_release_html(blocked_page)
