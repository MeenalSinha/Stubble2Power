"""
Centralized Multilingual Localization Framework.
Provides verified UI strings in English (en), Hindi (hi), and Punjabi (pa).
Technical identifiers, NASA observation codes, and scientific units remain untranslated.
"""

from typing import Dict, Any

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "app_title": {
        "en": "Stubble2Power - Satellite Fire Intelligence & Mobile Bio-Refineries",
        "hi": "Stubble2Power - उपग्रह अग्नि आसूचना एवं मोबाइल बायो-रिफाइनरी",
        "pa": "Stubble2Power - ਸੈਟੇਲਾਈਟ ਅੱਗ ਖੁਫੀਆ ਅਤੇ ਮੋਬਾਈਲ ਬਾਇਓ-ਰਿਫਾਇਨਰੀਆਂ"
    },
    "app_subtitle": {
        "en": "NASA Satellite Fire Intelligence & Mobile Bio-Refineries for Clean Energy",
        "hi": "नासा उपग्रह अग्नि आसूचना और स्वच्छ ऊर्जा हेतु मोबाइल बायो-रिफाइनरी",
        "pa": "ਨਾਸਾ ਸੈਟੇਲਾਈਟ ਅੱਗ ਖੁਫੀਆ ਜਾਣਕਾਰੀ ਅਤੇ ਸਾਫ਼ ਊਰਜਾ ਲਈ ਮੋਬਾਈਲ ਬਾਇਓ-ਰਿਫਾਇਨਰੀਆਂ"
    },
    "role_workspace": {
        "en": "Active Role Workspace",
        "hi": "सक्रिय भूमिका कार्यक्षेत्र",
        "pa": "ਸਰਗਰਮ ਭੂਮਿਕਾ ਵਰਕਸਪੇਸ"
    },
    "public_visitor": {
        "en": "Public Visitor Workspace",
        "hi": "सार्वजनिक आगंतुक कार्यक्षेत्र",
        "pa": "ਜਨਤਕ ਦਰਸ਼ਕ ਵਰਕਸਪੇਸ"
    },
    "farmer_workspace": {
        "en": "Farmer Workspace",
        "hi": "किसान कार्यक्षेत्र",
        "pa": "ਕਿਸਾਨ ਵਰਕਸਪੇਸ"
    },
    "operator_workspace": {
        "en": "Field Operator Workspace",
        "hi": "फील्ड ऑपरेटर कार्यक्षेत्र",
        "pa": "ਫੀਲਡ ਓਪਰੇਟਰ ਵਰਕਸਪੇਸ"
    },
    "agri_analyst_workspace": {
        "en": "Agricultural Analyst Workspace",
        "hi": "कृषि विश्लेषक कार्यक्षेत्र",
        "pa": "ਖੇਤੀਬਾੜੀ ਵਿਸ਼ਲੇਸ਼ਕ ਵਰਕਸਪੇਸ"
    },
    "env_analyst_workspace": {
        "en": "Environmental Analyst Workspace",
        "hi": "पर्यावरण विश्लेषक कार्यक्षेत्र",
        "pa": "ਵਾਤਾਵਰਣ ਵਿਸ਼ਲੇਸ਼ਕ ਵਰਕਸਪੇਸ"
    },
    "org_manager_workspace": {
        "en": "Organization Manager Workspace",
        "hi": "संगठन प्रबंधक कार्यक्षेत्र",
        "pa": "ਸੰਸਥਾ ਪ੍ਰਬੰਧਕ ਵਰਕਸਪੇਸ"
    },
    "admin_workspace": {
        "en": "System Administrator Workspace",
        "hi": "सिस्टम प्रशासक कार्यक्षेत्र",
        "pa": "ਸਿਸਟਮ ਪ੍ਰਸ਼ਾਸਕ ਵਰਕਸਪੇਸ"
    },
    "select_language": {
        "en": "Language",
        "hi": "भाषा",
        "pa": "ਭਾਸ਼ਾ"
    },
    "tenant_organization": {
        "en": "Tenant Organization",
        "hi": "किरायेदार संगठन",
        "pa": "ਸੰਬੰਧਿਤ ਸੰਸਥਾ"
    },
    "authenticated_as": {
        "en": "Authenticated Identity",
        "hi": "प्रमाणित पहचान",
        "pa": "ਪ੍ਰਮਾਣਿਤ ਪਛਾਣ"
    },
    "biomass_available": {
        "en": "Collectable Biomass",
        "hi": "एकत्र करने योग्य बायोमाਸ",
        "pa": "ਇਕੱਠੀ ਕਰਨ ਯੋਗ ਪਰਾਲੀ"
    },
    "farms_managed": {
        "en": "Farms Managed",
        "hi": "प्रबंधित खेत",
        "pa": "ਪ੍ਰਬੰਧਿਤ ਖੇਤ"
    },
    "harvest_yield": {
        "en": "Harvest Yield",
        "hi": "फसल पैदावार",
        "pa": "ਫ਼ਸਲ ਦਾ ਝਾੜ"
    },
    "net_avoided_co2e": {
        "en": "Net Avoided CO2e",
        "hi": "शुद्ध बचा हुआ CO2e",
        "pa": "ਸ਼ੁੱਧ ਬਚਾਇਆ ਗਿਆ CO2e"
    },
    "carbon_credits": {
        "en": "Carbon Credit Potential",
        "hi": "कार्बन क्रेडिट क्षमता",
        "pa": "ਕਾਰਬਨ ਕ੍ਰੈਡਿਟ ਸਮਰੱਥਾ"
    },
    "logistics_distance": {
        "en": "Logistics Road Distance",
        "hi": "लॉजिस्टिक्स सड़क दूरी",
        "pa": "ਲੌਜਿਸਟਿਕਸ ਸੜਕ ਦੂਰੀ"
    },
    "export_report": {
        "en": "Export Report",
        "hi": "रिपोर्ट निर्यात करें",
        "pa": "ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰੋ"
    },
    "privacy_consent": {
        "en": "Privacy & Consent Management",
        "hi": "गोपनीयता और सहमति प्रबंधन",
        "pa": "ਗੋਪਨੀਯਤਾ ਅਤੇ ਸਹਿਮਤੀ ਪ੍ਰਬੰਧਨ"
    }
}


def t(key: str, lang: str = "en") -> str:
    """Translates a message key into the selected language (fallback to English)."""
    lang_code = (lang or "en").lower()[:2]
    if lang_code not in ["en", "hi", "pa"]:
        lang_code = "en"
    entry = TRANSLATIONS.get(key, {})
    return entry.get(lang_code, entry.get("en", key))
