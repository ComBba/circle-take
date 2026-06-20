import pytest
from app import oss_storage

OSS_ENV = [
    "ALIBABA_CLOUD_ACCESS_KEY_ID",
    "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    "ALIBABA_CLOUD_REGION",
    "ALIBABA_CLOUD_OSS_BUCKET",
]


def test_endpoint_format():
    assert oss_storage.endpoint("ap-southeast-1") == "https://oss-ap-southeast-1.aliyuncs.com"


def test_object_url_format():
    assert (
        oss_storage.object_url("my-bucket", "ap-southeast-1", "episodes/ep1/take2.png")
        == "https://my-bucket.oss-ap-southeast-1.aliyuncs.com/episodes/ep1/take2.png"
    )


def test_missing_creds_raises(monkeypatch):
    for k in OSS_ENV:
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(oss_storage.OSSConfigError):
        oss_storage.load_config()


def test_config_ok_when_present(monkeypatch):
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "id")
    monkeypatch.setenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "secret")
    monkeypatch.setenv("ALIBABA_CLOUD_REGION", "ap-southeast-1")
    monkeypatch.setenv("ALIBABA_CLOUD_OSS_BUCKET", "bucket")
    cfg = oss_storage.load_config()
    assert cfg.bucket == "bucket" and cfg.region == "ap-southeast-1"
