from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

import pytest

from bibdec import Bibliography


@pytest.fixture
def bibliography_string():
    return dedent(
        """\
        @article{key1,
          author          = {Test Author and Another Author},
          title           = {Some novel contribution},
          year            = {2021},
          volume          = {42},
          number          = {420--450},
          journal         = {Journal of Novel Contributions}
        }

        @inproceedings{key2,
          author          = {Third Author and Test Author},
          title           = {We made a conference paper},
          booktitle       = {Proceedings of the Best Conference},
          year            = {1997}
        }

        @book{key3,
          author         = {Some Guy},
          editor         = {Some Editor},
          title          = {This book is useful},
          publisher      = {Some Publisher},
          year           = {2020}
        }
        """
    )


@pytest.fixture
def bibliography(bibliography_string):
    return Bibliography(bibliography_string)


def test_bibliography_created_correct_from_file(bibliography_string):
    with TemporaryDirectory() as tmpdir:
        bib_file = Path(tmpdir) / "bibliography.bib"
        with open(bib_file, "w") as f:
            f.write(bibliography_string)
        with open(bib_file, "r") as f:
            bibliography_loaded = Bibliography.load(f)
    bibliography = Bibliography(bibliography_string)
    assert bibliography_loaded.full_bibliography == bibliography.full_bibliography
    assert bibliography_loaded.bib_database.entries == bibliography.bib_database.entries


def test_bibliography_has_correct_length(bibliography, bibliography_string):
    num_keys = bibliography_string.count("@")
    assert len(bibliography) == num_keys


def test_keys_are_added_after_calling(bibliography):
    @bibliography.register_cites({"key1"})
    def some_function():
        pass

    assert len(bibliography.citations) == 0
    some_function()
    assert len(bibliography.citations) == 1
    assert {"key1"} in bibliography.citations.values()


def test_keys_work_as_strings(bibliography):
    @bibliography.register_cites("key1")
    def some_function():
        pass

    some_function()
    assert len(bibliography.citations) == 1
    assert {"key1"} in bibliography.citations.values()


def test_nonexistent_key_raises_error(bibliography):
    with pytest.raises(ValueError):

        @bibliography.register_cites("nonexistent_key")
        def function_with_error():
            pass


def test_simple_cite_function_works(bibliography):
    def cite_function(a, *, __check_validity__=False):
        citations = {}
        if a == 1 or __check_validity__:
            citations["a=1"] = "key1"
        if a == 2 or __check_validity__:
            citations["a=2"] = "key2"
        return citations

    @bibliography.register_cites(cite_function=cite_function)
    def simple_function(a):
        pass

    simple_function(0)
    assert len(bibliography.citations) == 0

    simple_function(1)
    assert len(bibliography.citations) == 1
    assert {"key1"} in bibliography.citations.values()
    assert any("a=1" in signature for signature in bibliography.citations)

    simple_function(2)
    assert len(bibliography.citations) == 2
    assert {"key2"} in bibliography.citations.values()
    assert any("a=2" in signature for signature in bibliography.citations)


def test_multiple_cites_cite_function_works(bibliography):
    def cite_function(a, b, *, __check_validity__=False):
        citations = {}
        if a == 1 or __check_validity__:
            citations["a=1"] = "key1"
        if a == 2 or __check_validity__:
            citations["a=2"] = "key2"
        if b == 1 or __check_validity__:
            citations["b=1"] = "key3"
        return citations

    @bibliography.register_cites(cite_function=cite_function)
    def simple_function(a, b):
        pass

    simple_function(0, 0)
    assert len(bibliography.citations) == 0

    simple_function(1, 0)
    assert len(bibliography.citations) == 1
    assert {"key1"} in bibliography.citations.values()
    assert any("a=1" in signature for signature in bibliography.citations)
    assert not any("b=1" in signature for signature in bibliography.citations)

    simple_function(2, 1)
    assert len(bibliography.citations) == 2
    assert {"key2", "key3"} in bibliography.citations.values()
    assert any("a=2" in signature for signature in bibliography.citations)
    assert any("b=1" in signature for signature in bibliography.citations)


def test_cite_function_must_have_same_number_of_arguments(bibliography):
    with pytest.raises(TypeError):

        def cite_function(a, *, __check_validity__=False):
            return {}

        @bibliography.register_cites(cite_function=cite_function)
        def error_func(a, b):
            pass


def test_c_function_raises_type_error(bibliography):
    with pytest.raises(TypeError):
        bibliography.register_cites("key1")(min)


def test_class_raises_type_error(bibliography):
    with pytest.raises(TypeError):

        class F:
            pass

        bibliography.register_cites("key1")(F)
        bibliography.register_cites("key1")(range)
