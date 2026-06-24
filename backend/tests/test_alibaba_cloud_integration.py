"""The Alibaba Cloud proof file must name both services and target aliyuncs.com — no network."""
from app import alibaba_cloud_integration as aci


def test_manifest_lists_both_alibaba_services():
    m = aci.alibaba_services_used()
    assert "model_studio_dashscope" in m
    assert "object_storage_oss" in m


def test_model_studio_endpoints_target_dashscope_aliyuncs():
    ms = aci.alibaba_services_used()["model_studio_dashscope"]
    assert "dashscope-intl" in ms["chat_endpoint"] and "aliyuncs.com" in ms["chat_endpoint"]
    assert "aliyuncs.com" in ms["video_endpoint"]
    # The text/vision/video model IDs are surfaced for the proof manifest.
    assert {"text", "vision", "video_t2v"} <= set(ms["models"])


def test_oss_section_uses_oss2_sdk_and_aliyuncs_endpoint():
    oss = aci.alibaba_services_used()["object_storage_oss"]
    assert oss["sdk"] == "oss2"
    assert "aliyuncs.com" in oss["endpoint_pattern"]


def test_reexports_are_the_real_oss_callables():
    # Re-exports keep this proof file live code, not a stub.
    assert callable(aci.oss_put_bytes) and callable(aci.oss_signed_url)
    assert aci.oss_endpoint("ap-southeast-1") == "https://oss-ap-southeast-1.aliyuncs.com"
