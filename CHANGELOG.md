# Changelog

All notable changes to `scitex-notebook` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Configure subprocess coverage via coverage.py `patch = ["subprocess"]` in `pyproject.toml`; `tests/conftest.py` no longer writes `.pth` files into site-packages or overwrites `COVERAGE_PROCESS_START` / `COVERAGE_FILE`.

## [0.1.2]

- Initial CHANGELOG entry — see git log for prior history.
