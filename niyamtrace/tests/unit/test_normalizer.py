import pytest
from packages.nlp.normalizer import TextNormalizer

@pytest.fixture
def normalizer():
    return TextNormalizer()

def test_english_normalization(normalizer):
    text = "Block access to INV-204 for the next 7 days."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "Block access to INV-204 for the next 7 days."
    assert "INV-204" in res["protected_spans"]
    assert "7" in res["protected_spans"]
    assert res["english_pivot"] is None

def test_hinglish_normalization(normalizer):
    text = "INV-204 ka access agle 7 din ke liye block karo."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "INV-204का एक्सेस अगले7दिन के लिए ब्लॉक करो."
    assert "INV-204" in res["protected_spans"]
    assert "roman_transliteration" in res["transformation_trace"]

def test_telugu_roman_normalization(normalizer):
    text = "INV-204 ki access ni vacche 7 rojula paatu block cheyyi."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "INV-204కు యాక్సెస్ను ని వచ్చే7రోజుల పాటు బ్లాక్ చేయి."
    assert "INV-204" in res["protected_spans"]

def test_mixed_normalization(normalizer):
    text = "INV-204 ki access ni next 7 rojulu block cheyyi."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "INV-204కు యాక్సెస్ను ని నెక్స్ట్7రోజులు బ్లాక్ చేయి."

def test_negated_telugu(normalizer):
    text = "INV-204ను బ్లాక్ చేయొద్దు."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "INV-204ను బ్లాక్ చేయొద్దు."

def test_protected_value_case(normalizer):
    text = "USR_8A2 ki ₹25,000 limit ni change cheyyaku."
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "USR_8A2కు₹25,000లిమిట్ ని చేంజ్ చేయకు."
    assert "USR_8A2" in res["protected_spans"]
    assert "₹25,000" in res["protected_spans"]

def test_adversarial_case(normalizer):
    text = "plz block INV-204 ka acce$$!!"
    res = normalizer.normalize(text)
    
    assert res["normalized_text"] == "plz block INV-204का acce$$!!"
    assert "INV-204" in res["protected_spans"]
