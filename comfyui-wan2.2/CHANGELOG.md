# Changelog

## [v0.12.0](https://github.com/wagoodman/dive/tree/v0.12.0) (2024-02-02)

[Full Changelog](https://github.com/wagoodman/dive/compare/v0.11.0...v0.12.0)

### Added Features

- Can we do docker layer wise scan for vulnerability detection [[Issue #465](https://github.com/wagoodman/dive/issues/465)]
- How to use Dive in gitlab CI Securely? [[Issue #493](https://github.com/wagoodman/dive/issues/493)]

### Bug Fixes

- Dive always fail when trying to fetch local image [[Issue #462](https://github.com/wagoodman/dive/issues/462)]
- Unable to analyze the image using dive [[Issue #498](https://github.com/wagoodman/dive/issues/498)] [[PR #500](https://github.com/wagoodman/dive/pull/500)] [[tbroyer](https://github.com/tbroyer)]

### Additional Changes

- Bump to more recent go version, remove no longer required overrides [[PR #461](https://github.com/wagoodman/dive/pull/461)] [[SuperSandro2000](https://github.com/SuperSandro2000)]
- docs: Adds instructions for snap installation [[PR #484](https://github.com/wagoodman/dive/pull/484)] [[gruyaume](https://github.com/gruyaume)]
- DIVE_VERSION does not need to be exported [[PR #492](https://github.com/wagoodman/dive/pull/492)] [[ReneNyffenegger](https://github.com/ReneNyffenegger)]
- fix(sec): upgrade golang.org/x/net to 0.17.0 [[PR #503](https://github.com/wagoodman/dive/pull/503)] [[suguds](https://github.com/suguds)]


