===========
Pajek Tools
===========

.. image:: https://img.shields.io/pypi/v/pajek_tools.svg
        :target: https://pypi.python.org/pypi/pajek_tools

..
        .. image:: https://img.shields.io/travis/h1-the-swan/pajek_tools.svg
                :target: https://travis-ci.com/h1-the-swan/pajek_tools

        .. image:: https://readthedocs.org/projects/pajek-tools/badge/?version=latest
                :target: https://pajek-tools.readthedocs.io/en/latest/?badge=latest
                :alt: Documentation Status




Tools for converting network data to pajek files.

`Pajek`_ is a file format for networks, typically stored in files with a ``.net`` extension. It is used as input for software such as `Infomap`_.

.. _`Pajek`: http://mrvar.fdv.uni-lj.si/pajek/
.. _`Infomap`: https://www.mapequation.org/code.html



Installation
------------

Install from PyPI::

    pip install pajek-tools


Usage
-----

Use the ``PajekWriter`` object to convert a network from an edgelist in pandas DataFrame form, to a Pajek .net file::

        from pajek_tools import PajekWriter
        writer = PajekWriter(dataframe)
        writer.write("output.net")

Example
-------

::

        from pajek_tools import PajekWriter
        import pandas as pd

        df = pd.DataFrame([["a", "b"], ["a", "c"], ["c", "a"], ["c", "d"]], columns=["source", "target"])
        writer = PajekWriter(df, 
                             directed=True, 
                             citing_colname="source", 
                             cited_colname="target")
        writer.write("output.net")

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
