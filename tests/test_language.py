from spacy.lang.en import EnglishDefaults
from spacy.lang.de import GermanDefaults
import spacy_stanza
import stanza
import pytest


def tags_equal(act, exp):
    """Check if each actual tag in act is equal to one or more expected tags in exp."""
    return all(a == e if isinstance(e, str) else a in e for a, e in zip(act, exp))


def test_spacy_stanza_english():
    lang = "en"
    stanza.download(lang)
    nlp = spacy_stanza.blank(lang)
    assert nlp.Defaults == EnglishDefaults

    doc = nlp("Hello world! This is a test.")

    # Expected POS tags. Note: Different versions of stanza result in different
    # POS tags.
    # fmt: off
    pos_exp = ["INTJ", "NOUN", "PUNCT", ("DET", "PRON"), ("VERB", "AUX"), "DET", "NOUN", "PUNCT"]

    assert [t.text for t in doc] == ["Hello", "world", "!", "This", "is", "a", "test", "."]
    assert [t.lemma_ for t in doc] == ["hello", "world", "!", "this", "be", "a", "test", "."]
    assert tags_equal([t.pos_ for t in doc], pos_exp)

    assert [t.tag_ for t in doc] == ["UH", "NN", ".", "DT", "VBZ", "DT", "NN", '.']
    assert [str(t.morph) for t in doc] == ['', 'Number=Sing', '', 'Number=Sing|PronType=Dem', 'Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin', 'Definite=Ind|PronType=Art', 'Number=Sing', '']
    assert [t.dep_ for t in doc] == ["root", "vocative", "punct", "nsubj", "cop", "det", "root", "punct"]
    assert [t.is_sent_start for t in doc] == [True, False, False, True, False, False, False, False]
    assert any([t.is_stop for t in doc])
    # fmt: on
    assert len(list(doc.sents)) == 2
    assert doc.has_annotation("TAG")
    assert doc.has_annotation("MORPH")
    assert doc.has_annotation("DEP")
    assert doc.has_annotation("SENT_START")

    docs = list(nlp.pipe(["Hello world", "This is a test"]))
    assert docs[0].text == "Hello world"
    assert [t.pos_ for t in docs[0]] == ["INTJ", "NOUN"]
    assert docs[1].text == "This is a test"
    assert tags_equal([t.pos_ for t in docs[1]], pos_exp[3:-1])
    assert doc.ents == tuple()

    # Test NER
    doc = nlp("Barack Obama was born in Hawaii.")
    assert len(doc.ents) == 2
    assert doc.ents[0].text == "Barack Obama"
    assert doc.ents[0].label_ == "PERSON"
    assert doc.ents[1].text == "Hawaii"
    assert doc.ents[1].label_ == "GPE"

    # Test whitespace alignment
    doc = nlp(" Barack  Obama  was  born\n\nin Hawaii.")
    assert [t.pos_ for t in doc] == [
        "SPACE",
        "PROPN",
        "SPACE",
        "PROPN",
        "SPACE",
        "AUX",
        "SPACE",
        "VERB",
        "SPACE",
        "ADP",
        "PROPN",
        "PUNCT",
    ]
    assert [t.dep_ for t in doc] == [
        "",
        "nsubj:pass",
        "",
        "flat",
        "",
        "aux:pass",
        "",
        "root",
        "",
        "case",
        "root",
        "punct",
    ]
    assert [t.head.i for t in doc] == [0, 7, 2, 1, 4, 7, 6, 7, 8, 10, 10, 10]
    assert len(doc.ents) == 2
    assert doc.ents[0].text == "Barack  Obama"
    assert doc.ents[0].label_ == "PERSON"
    assert doc.ents[1].text == "Hawaii"
    assert doc.ents[1].label_ == "GPE"

    # Test serialization
    reloaded_nlp = spacy_stanza.blank(lang).from_bytes(nlp.to_bytes())
    assert reloaded_nlp.config.to_str() == nlp.config.to_str()


def test_spacy_stanza_german():
    lang = "de"
    stanza.download(lang)
    nlp = spacy_stanza.blank(lang)
    assert nlp.Defaults == GermanDefaults

    # warning for misaligned ents due to multi-word token expansion
    with pytest.warns(UserWarning):
        doc = nlp("Auf dem Friedhof an der Straße Am Rosengarten")


def test_spacy_stanza_tokenizer_options():
    # whitespace tokens from spacy tokenizer are handled correctly
    lang = "en"
    stanza.download(lang)
    nlp = spacy_stanza.blank(
        lang, config={"nlp": {"tokenizer": {"processors": {"tokenize": "spacy"}}}}
    )

    doc = nlp(" Barack  Obama  was  born\n\nin Hawaii.")
    assert [t.text for t in doc] == [
        " ",
        "Barack",
        " ",
        "Obama",
        " ",
        "was",
        " ",
        "born",
        "\n\n",
        "in",
        "Hawaii",
        ".",
    ]

    # pretokenized text is handled correctly
    nlp = spacy_stanza.blank(
        lang, config={"nlp": {"tokenizer": {"kwargs": {"tokenize_pretokenized": True}}}}
    )
    doc = nlp("Barack Obama was born in Hawaii.\nBarack Obama was born in Hawaii.")
    assert [t.text for t in doc] == [
        "Barack",
        "Obama",
        "was",
        "born",
        "in",
        "Hawaii.",
        "Barack",
        "Obama",
        "was",
        "born",
        "in",
        "Hawaii.",
    ]
    doc = nlp(
        " Barack  Obama  was  born\n\n in Hawaii.\nBarack Obama was born in Hawaii."
    )
    assert [t.text for t in doc] == [
        "Barack",
        "Obama",
        "was",
        "born",
        "in",
        "Hawaii.",
        "Barack",
        "Obama",
        "was",
        "born",
        "in",
        "Hawaii.",
    ]
