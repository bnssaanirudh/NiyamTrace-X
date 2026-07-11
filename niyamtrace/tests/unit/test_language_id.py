import pytest
from packages.nlp.language_id import LanguageIdentifier

@pytest.fixture
def identifier():
    return LanguageIdentifier()

def test_english_spans(identifier):
    text = "Block access to INV-204 for the next 7 days."
    result = identifier.identify(text)
    
    # Assert primary language is english
    assert "eng_Latn" in result["primary_language_mix"]
    assert not result["requires_review"]
    
    # Check spans
    protected_ids = [s["text"] for s in result["spans"] if s["type"] == "protected_identifier"]
    assert "INV-204" in protected_ids
    
    numbers = [s["text"] for s in result["spans"] if s["type"] == "number"]
    assert "7" in numbers

def test_hinglish_spans(identifier):
    text = "INV-204 ka access agle 7 din ke liye block karo."
    result = identifier.identify(text)
    
    assert "hin_Latn" in result["primary_language_mix"]
    
    protected_ids = [s["text"] for s in result["spans"] if s["type"] == "protected_identifier"]
    assert "INV-204" in protected_ids

def test_telugu_roman_spans(identifier):
    text = "INV-204 ki access ni vacche 7 rojula paatu block cheyyi."
    result = identifier.identify(text)
    
    assert "tel_Latn" in result["primary_language_mix"]

def test_telugu_script_spans(identifier):
    text = "INV-204కు యాక్సెస్ను వచ్చే 7 రోజుల పాటు బ్లాక్ చేయి."
    result = identifier.identify(text)
    
    assert "tel_Telu" in result["primary_language_mix"]
