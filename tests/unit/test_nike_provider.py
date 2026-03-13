from support import build_nike_launch_html

from sneaker_launchpad.models import ReleaseState, StoreName
from sneaker_launchpad.providers.nike import parse_nike_launch_html


def test_parse_nike_launch_html_extracts_releases() -> None:
    releases = parse_nike_launch_html(build_nike_launch_html())

    assert len(releases) == 1
    release = releases[0]
    assert release.provider == StoreName.NIKE
    assert release.name == "Air Max Test Pair"
    assert release.colorway == "Infrared"
    assert release.style_code == "HM1234-001"
    assert release.sizes == ("10", "10.5")
    assert release.state == ReleaseState.UPCOMING
    assert release.product_url.endswith("/air-max-test-pair")
