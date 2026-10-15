Codex Universal Orchestrator (CUO)
==================================

:Version: 6.0.0
:Created: 15-10-26 08-24-40 (Europe/Moscow)
:Updated: 15-10-26 08-36-03 (Europe/Moscow)
:Commit: docs(repo): license CUO Kit under MIT

CUO provides a Codex orchestration skill, agent presets, installation and
migration tools, examples, and validation tests. It supports local Codex clients
using ChatGPT Pro login, with no product-runtime model routing.

Start with the `original Kit README <README__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md>`_
and the `installation and migration guide <INSTALL_AND_MIGRATION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md>`_.

Source and verification
-----------------------

The 50 original Kit files, including MANIFEST.json and the legacy test fixture,
are preserved byte-for-byte from this locally available archive::

  codex_universal_orchestration_created_12_10_26_04_26_07_updated.zip

Archive SHA-256::

  96420137c9f797860607ae30d618845fbdd063fc616550de574d3a8de5b930ae

All 49 manifest entries matched their SHA-256 hashes. The supplied unittest
suite passed 60 tests on Python 3.14.3 on 15-10-26. The import scan found no
matches for common credential patterns, including inside the test fixture ZIP.
The local archive is the source of this import; the referenced chat attachment
was not available for a direct comparison.

The original documentation retains its proposed status. This import does not
establish model entitlement or verify orchestration behavior in a live session.

License and provenance
----------------------

The files in this repository are licensed under the `MIT License <LICENSE>`_.
Copyright (c) 2026 Igor Pastin. CUO is an independent project for Codex and is
not affiliated with OpenAI.

The Kit was produced in the owner's ChatGPT project. The source archive and
the nested legacy test fixture were inspected for third-party copyright notices,
personal paths, and common secret patterns; none were found. This inspection
cannot establish provenance beyond the available archive.

This README, .gitignore, and LICENSE were added to the original Kit. Local
machine metadata, credentials, and generated test files are excluded.
