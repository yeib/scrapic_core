from scrapic.core.i18n import t, TRANSLATIONS


def test_i18n_translation_keys_exist():
    assert "EN" in TRANSLATIONS
    assert "ES" in TRANSLATIONS
    assert t("language", "EN") == "Language"
    assert t("language", "ES") == "Idioma"


def test_i18n_fallback_behavior():
    # Fallback to key itself if not found
    assert t("non_existent_key", "EN") == "non_existent_key"
    # Fallback to EN if language is unknown
    assert t("language", "FR") == "Language"
