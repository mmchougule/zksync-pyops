=============
zksync-ops
=============

.. image:: https://img.shields.io/pypi/v/zksync-deploy.svg
    :target: https://pypi.python.org/pypi/zksync-deploy

Python cli to deploy zksync contracts.

Installation

`pip install zksync-deploy`

Prerequisites

1. Compile smart contract using zkSync cli
2. It generates zkSync ABI JSON and contract binary
3. Deploy contract using zksync-ops cli
    zksyncops deploy --help
    zksyncops deploy "CONTRACT_HEX_PATH" "CONTRACT_ABI_PATH"

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
