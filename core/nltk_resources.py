from __future__ import annotations

import zipfile

import nltk


REQUIRED_RESOURCES = {
    "corpora/stopwords": "stopwords",
    "corpora/wordnet": "wordnet",
    "corpora/omw-1.4": "omw-1.4",
    "taggers/averaged_perceptron_tagger_eng": "averaged_perceptron_tagger_eng",
}


def ensure_nltk_resources() -> None:
    """Best-effort probe for NLTK resources.

    The project should remain usable even when these corpora are not available,
    so this function intentionally avoids auto-downloading them.
    """
    for resource_path in REQUIRED_RESOURCES:
        try:
            nltk.data.find(resource_path)
        except (LookupError, OSError, zipfile.BadZipFile):
            continue


def has_nltk_resource(resource_path: str) -> bool:
    try:
        nltk.data.find(resource_path)
        return True
    except (LookupError, OSError, zipfile.BadZipFile):
        return False