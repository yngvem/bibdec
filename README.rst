Automatic bibliography generation
=================================

The goal of this project is to provide an easy-to-use tool that autogenerates a bibliography.
Specifically, the code provides a decorator that allows you to add citations to your functions.
Then, if one of the decorated functions is called, their relevant citation keys are added to
a dictionary together with the function signature that generated those citation keys. Once the
program is finished running, you can request a list of used citation keys to see which cites
you used where. Also, you can export the bibliography as a bibtex file containing only the
references that are used at least once.

Installation
------------

The library is available on PyPI, so you can install it with pip:

.. code::

    pip install bibdec


Simple example
--------------

Below is a minimal example demonstrating with only one key. However, you can also decorate a
function with multiple keys, or even have conditional citations based on the function signature.
More complex examples are available in the example section of the documentation.

.. code:: python

    from bibdec import Bibliography

    bibtex = """
    @article{key1,
    author = {Some Author},
    title = {Some paper},
    journal = {Some Journal},
    year = {1999},
    volume = {42},
    number = {100 -- 150}
    }
    """
    bibliography = Bibliography(bibtex)

    @bibliography.register_cites("key1")
    def f(a):
        return a + 2
    
    print("Before calling the function:")
    print(bibliography.citations)
    print(bibliography.active_bibliography)

    f(0)
    print("After calling the function:")
    print(bibliography.citations)
    print(bibliography.active_bibliography)


.. code::

    Before calling the function:
    {}

    After calling the function:
    {'__main__.f()': {'key1'}}
    @article{key1,
    author = {Some Author},
    journal = {Some Journal},
    number = {100 -- 150},
    title = {Some paper},
    volume = {42},
    year = {1999}
    }
