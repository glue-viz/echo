# Full changelog

## v0.7 - 2022-09-27

### What's Changed

#### Bug Fixes

- Fix compatibility with PyQt6 by @astrofrog in https://github.com/glue-viz/echo/pull/29

#### Other Changes

- Migrate CI tests and publishing task to GitHub Actions by @dhomeier in https://github.com/glue-viz/echo/pull/33
- Add PySide6 test envs to CI by @dhomeier in https://github.com/glue-viz/echo/pull/34

### New Contributors

- @dhomeier made their first contribution in https://github.com/glue-viz/echo/pull/33

**Full Changelog**: https://github.com/glue-viz/echo/compare/v0.5...v0.6

## 0.6 (2021-12-14)

- Fixed compatibility with recent PyQt5 versions.

## 0.5 (2020-11-08)

- Add the ability to specify for `SelectionCallbackProperty` whether to
  compare choices using equality or identity. [#26]

- Fixed an issue that could lead to `CallbackContainer` returning dead
  weak references during iteration. [#27]

## 0.4 (2020-05-04)

- Added the ability to add arbitrary callbacks to `CallbackDict` and
  `CallbackList` via the `.callbacks` attribute. [#25]

## 0.3 (2020-05-04)

- Fix setting of defaults in callback list and dict properties. [#24]

## 0.2 (2020-04-11)

- Python 3.6 or later is now required. [#20]
  
- Significant refactoring of the package. [#20]

## 0.1 (2014-03-13)

- Initial version
