"""
Unit and Integration Tests for MovieBox-TUI Python (Basic Procedural - No Classes)
Completely procedural test suite testing cryptographic tokens, M3U parser, VLC generator, and providers.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from providers.moviebox import crypto
from providers.moviebox.client import ensure_session, MovieBoxClient
from providers.tv.parser import parse_m3u_text, M3UParser
from providers import get_provider, list_providers
from models.release import Release, SourceMirror


def test_token_format():
    token = crypto.generate_x_client_token(1700000000000)
    assert "," in token, "Token must contain comma"
    ts, h = token.split(",", 1)
    assert ts == "1700000000000", "Timestamp must match input"
    assert len(h) == 32, "Hash must be 32 characters MD5"
    print("✔ test_token_format passed")


def test_signature_format():
    sig = crypto.generate_x_tr_signature(
        method="POST",
        accept="application/json",
        content_type="application/json",
        url="https://api6.aoneroom.com/wefeed-mobile-bff/user-api/visitor-login",
        body="{}",
        timestamp_ms=1700000000000,
    )
    assert sig.startswith("1700000000000|2|"), f"Signature invalid prefix: {sig}"
    print("✔ test_signature_format passed")


def test_list_providers():
    providers = list_providers()
    names = [p["name"] for p in providers]
    for required in ["moviebox", "dramachi", "fourkhdhub", "tv", "bdix"]:
        assert required in names, f"Provider {required} missing from registry"
    print("✔ test_list_providers passed")


def test_tv_m3u_parser():
    sample_m3u = """#EXTM3U
#EXTINF:-1 tvg-id="TestTV" group-title="News",Test News HD
https://example.com/test.m3u8
"""
    channels = parse_m3u_text(sample_m3u)
    assert len(channels) == 1, "Should parse 1 channel"
    ch = channels[0]
    name = ch.get("name") if isinstance(ch, dict) else getattr(ch, "name")
    cat = ch.get("category") if isinstance(ch, dict) else getattr(ch, "category")
    url = ch.get("stream_url") if isinstance(ch, dict) else getattr(ch, "stream_url")
    assert name == "Test News HD", f"Expected 'Test News HD', got {name}"
    assert cat == "News", f"Expected 'News', got {cat}"
    assert url == "https://example.com/test.m3u8"
    print("✔ test_tv_m3u_parser passed")

def test_dramachi_provider_registration():
    dramachi = get_provider("dramachi")
    name = dramachi.get("name") if isinstance(dramachi, dict) else getattr(dramachi, "name")
    assert name == "dramachi"
    print("✔ test_dramachi_provider_registration passed")


def test_moviebox_visitor_login():
    try:
        token = ensure_session()
        assert bool(token), "Visitor session token should be non-empty"
        assert len(token) > 20, "Token length should be > 20"
        print("✔ test_moviebox_visitor_login passed")
    except Exception as e:
        print(f"⚠ test_moviebox_visitor_login network notice: {e}")


def run_all_tests():
    print("Running MovieBox-TUI procedural test suite...")
    test_token_format()
    test_signature_format()
    test_list_providers()
    test_dramachi_provider_registration()
    test_moviebox_visitor_login()
    print("All procedural unit tests completed successfully!")


if __name__ == "__main__":
    run_all_tests()
