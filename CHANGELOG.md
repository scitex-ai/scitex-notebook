# Changelog

All notable changes to `scitex-notebook` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

- refactor: migrate `get_notebook_path` import in `_magic.py` from
  `scitex_gen` to `scitex_context` (Phase B of the scitex-gen full
  retirement wave). `get_notebook_path` is the public API; the private
  `scitex_gen._detect_notebook_path` path has never been the intended
  consumer surface. Adds `scitex-context>=0.1.0` to runtime deps.

## [0.1.2]

- Initial CHANGELOG entry — see git log for prior history.
