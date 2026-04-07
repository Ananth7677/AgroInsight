from app.services.query_parser import (
    extract_explicit_crop,
    extract_explicit_crops,
    extract_location_from_query,
    extract_soil_from_query,
    has_deictic_crop_reference,
    is_compare_query,
    is_harmful_query,
    is_smalltalk_or_offtopic_query,
    is_weather_query,
    rewrite_query_with_focus_crop,
)


def test_extract_location_from_query_detects_state():
    cleaned, location = extract_location_from_query("is corn suitable in california usa")
    assert location == "California, United States"
    assert "california" not in cleaned


def test_extract_crop_alias_normalizes_soyabean():
    crop = extract_explicit_crop("is soyabean profitable now?")
    assert crop == "soybean"



def test_extract_explicit_crops_for_compare():
    crops = extract_explicit_crops("compare maize vs soybean for next 3 months")
    assert "maize" in crops and "soybean" in crops



def test_extract_soil_from_query_detects_red_soil():
    cleaned, soil = extract_soil_from_query("i have red soil here")
    assert soil == "red"
    assert "red soil" not in cleaned



def test_rewrite_deictic_crop_dedupes_crop_tokens():
    q = rewrite_query_with_focus_crop("will this crop corn work", "corn")
    assert q.lower().count("corn") == 1



def test_intent_detectors():
    assert is_compare_query("compare rice vs maize")
    assert is_weather_query("how will the weather be in next 10 days")
    assert has_deictic_crop_reference("will this crop work")
    assert is_smalltalk_or_offtopic_query("how are you")
    assert not is_smalltalk_or_offtopic_query("which do you think is the best")
    assert is_harmful_query("how to demolish a home")
