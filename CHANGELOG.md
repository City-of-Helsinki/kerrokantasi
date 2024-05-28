# Changelog

## [1.5.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v1.4.0...kerrokantasi-v1.5.0) (2024-05-28)


### Features

* **hearing:** Remove next_closing filter ([5c2f1c0](https://github.com/City-of-Helsinki/kerrokantasi/commit/5c2f1c02796f06b4a95c9635cbe640dcba0ad2ab))


### Bug Fixes

* **hearing:** Change following filter to boolean ([6a42bdb](https://github.com/City-of-Helsinki/kerrokantasi/commit/6a42bdb7b4f880cc1cd56e67804622b612f741e5))
* **hearing:** Count hearings that open exactly at request time as open ([92ad624](https://github.com/City-of-Helsinki/kerrokantasi/commit/92ad62421a9f618bae651bfe0e3e7cc446d5a51f))
* **hearing:** Ignore created_by filter with unauthenticated users ([788edca](https://github.com/City-of-Helsinki/kerrokantasi/commit/788edca81c340940ffb3ee3e7ed3c8e378f523ae))
* **hearing:** Ignore following filter with unauthenticated users ([a924bb4](https://github.com/City-of-Helsinki/kerrokantasi/commit/a924bb4f7840d5daf0ea647bd79a6cf0e6bb91b5))
* **hearing:** Make open filter timezone aware ([84b3084](https://github.com/City-of-Helsinki/kerrokantasi/commit/84b30848712d39516dae586a0a22255645c0062b))


### Performance Improvements

* **hearing:** Optimize open filter ([de0b166](https://github.com/City-of-Helsinki/kerrokantasi/commit/de0b1668e5f5475e25e7613a959d40b1589ab837))


### Dependencies

* Update dependencies ([6f2ae5c](https://github.com/City-of-Helsinki/kerrokantasi/commit/6f2ae5c86696446cab2d8d956b4ae841852d2eeb))

## [1.4.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v1.3.0...kerrokantasi-v1.4.0) (2024-05-07)


### Features

* Create images/files by reference, remove copy logic ([e7117b8](https://github.com/City-of-Helsinki/kerrokantasi/commit/e7117b81bed4611da7091bf658e8e9ced03f657d))


### Bug Fixes

* Copy files in copy_hearing function ([7949619](https://github.com/City-of-Helsinki/kerrokantasi/commit/7949619ba241635114f3af0059a569700d55d39d))
* Return None in get_url if instance has no pk ([54f468d](https://github.com/City-of-Helsinki/kerrokantasi/commit/54f468dcdcdbb452c194d115181a39e0229e0eca))


### Dependencies

* Upgrade django to 4.2 ([474f68c](https://github.com/City-of-Helsinki/kerrokantasi/commit/474f68c42fb8eed1a7b39749ff7759254fb52341))

## [1.3.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v1.2.0...kerrokantasi-v1.3.0) (2024-03-25)


### Features

* Add util function to get model instances translations ([dd1b721](https://github.com/City-of-Helsinki/kerrokantasi/commit/dd1b72126a9d45ca6834ebecffa15c097158d815))
* **gdpr:** Add field translations to gdpr get return data ([dea0395](https://github.com/City-of-Helsinki/kerrokantasi/commit/dea0395978b60533afe80193a27f7435b24c40fe))
* **gdpr:** Add poll text to poll answers ([7c6b3b9](https://github.com/City-of-Helsinki/kerrokantasi/commit/7c6b3b9579982aff426581a76955b73054d451d7))


### Bug Fixes

* Gdpr get user data test fix ([11882ad](https://github.com/City-of-Helsinki/kerrokantasi/commit/11882ad382ecc0722b21320746630116e8773ce3))
