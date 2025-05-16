from qmtl.common.utils.hash_utils import md5_hex, sha256_hex


def test_sha256_hex():
    assert sha256_hex("abc") == sha256_hex(b"abc")
    assert len(sha256_hex("abc")) == 64


def test_md5_hex():
    assert md5_hex("abc") == md5_hex(b"abc")
    assert len(md5_hex("abc")) == 32
