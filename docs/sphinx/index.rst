SciTeX Notebook
===============

Jupyter notebook verification, compilation, and DAG-based conversion.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   api

Overview
--------

``scitex-notebook`` provides tools to verify, compile, convert, and check
Jupyter notebooks for reproducibility using the Clew verification system.

Key concept: notebooks can be executed in any cell order. SciTeX records the
actual execution order via timestamps and reconstructs the dependency DAG
afterward — *"do what you want, organize later."*

Quick Example
-------------

.. code-block:: python

   import scitex_notebook as notebook

   compiled = notebook.compile("experiment.ipynb")
   print(compiled.to_mermaid())
   print(compiled.to_script())

Indices
=======

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
