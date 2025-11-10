# Changelog

## [2.7.1](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.7.0...kerrokantasi-v2.7.1) (2025-11-10)


### Dependencies

* Bump django from 5.2.7 to 5.2.8 ([c248f52](https://github.com/City-of-Helsinki/kerrokantasi/commit/c248f52bb54217d9fdbcec6dcae2ce6bcc36f570))

## [2.7.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.6.0...kerrokantasi-v2.7.0) (2025-10-30)


### Features

* Adapt resilient logger for audit logs ([#567](https://github.com/City-of-Helsinki/kerrokantasi/issues/567)) ([c10e389](https://github.com/City-of-Helsinki/kerrokantasi/commit/c10e3893c8de55f34dfdcb09a54b8d8e49cd5aed))
* Change logging format to json ([#559](https://github.com/City-of-Helsinki/kerrokantasi/issues/559)) ([05421bb](https://github.com/City-of-Helsinki/kerrokantasi/commit/05421bbb6a135436c158cbb3193c2e16877f7d5e))
* Configure uwsgi for json logging ([#560](https://github.com/City-of-Helsinki/kerrokantasi/issues/560)) ([ab13745](https://github.com/City-of-Helsinki/kerrokantasi/commit/ab137457f3d72d427391e13266889b0a5e184ae2))

## [2.6.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.5.1...kerrokantasi-v2.6.0) (2025-10-29)


### Features

* Allow dynamic sentry trace ignore paths ([9fe314d](https://github.com/City-of-Helsinki/kerrokantasi/commit/9fe314d7142cbb55b03c03ecdfbd5d9b232dadc5))

## [2.5.1](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.5.0...kerrokantasi-v2.5.1) (2025-10-28)


### Bug Fixes

* **docker:** Mount volume to correct folder ([c32d2a0](https://github.com/City-of-Helsinki/kerrokantasi/commit/c32d2a0b4035bcc77b2a9c9d5c813692c3a9a064))
* Update uwsgi-config for Sentry ([4c6e5b4](https://github.com/City-of-Helsinki/kerrokantasi/commit/4c6e5b4c26b89270689061b185c1ad390508245b))


### Dependencies

* Bump bunch of dependencies ([cd6f5d2](https://github.com/City-of-Helsinki/kerrokantasi/commit/cd6f5d2afae09f0bfe8dd1bc908782bf4b0a16ea))
* Bump requirements ([0fb6465](https://github.com/City-of-Helsinki/kerrokantasi/commit/0fb6465b8315767a77bee7b9b451ddbbafb97061))
* **compose:** Bump postgis version ([fc2a717](https://github.com/City-of-Helsinki/kerrokantasi/commit/fc2a7176b8c71e674f3cc1a89b17aabb39a9cda1))
* Move uwsgi from Dockerfile to requirements ([5cddffe](https://github.com/City-of-Helsinki/kerrokantasi/commit/5cddffe67140bb2daeacbaaa8715b92c58b58b97))
* Remove Babel ([6588988](https://github.com/City-of-Helsinki/kerrokantasi/commit/6588988928e6562f26fbbdab7a3a94ae84de30f2))
* Remove djangoenumfields2 ([d7020e0](https://github.com/City-of-Helsinki/kerrokantasi/commit/d7020e0c84467ea0e4915c9d4e644a7591494189))
* Remove pytz ([867085f](https://github.com/City-of-Helsinki/kerrokantasi/commit/867085f61e9cd0ff85f2fe1a2dfaa5f856879a84))
* Replace django-sendfile with django-sendfile2 ([13fe7aa](https://github.com/City-of-Helsinki/kerrokantasi/commit/13fe7aad6aeb716f0c74f1aa140eb6c10986592b))
* Upgrade to django 5.2 ([7b80881](https://github.com/City-of-Helsinki/kerrokantasi/commit/7b808814cc0a9411768f31f0fca4c9971be2024d))
* Upgrade to python 3.12 ([98ccbd7](https://github.com/City-of-Helsinki/kerrokantasi/commit/98ccbd7ea739f2fe42a06c0105fe7936a0bbb02f))

## [2.5.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.5...kerrokantasi-v2.5.0) (2025-10-09)


### Features

* Add endpoints for liveness and readiness probes ([16708f9](https://github.com/City-of-Helsinki/kerrokantasi/commit/16708f92506e55ed1a45298d2feae77713d22bfe))
* **sentry:** Update sentry configuration ([98d37ee](https://github.com/City-of-Helsinki/kerrokantasi/commit/98d37ee610500ea6edf13cea145523edadf6b6a9))

## [2.4.5](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.4...kerrokantasi-v2.4.5) (2025-09-16)


### Bug Fixes

* Change TIME_ZONE from UTC to Europe/Helsinki ([37f12ad](https://github.com/City-of-Helsinki/kerrokantasi/commit/37f12ad06ea143bf5e8f3dc2c006ee82ec588fb4))


### Dependencies

* Bump django-helsinki-notification from 0.3.0 to 0.4.0 ([8aa6967](https://github.com/City-of-Helsinki/kerrokantasi/commit/8aa6967a2e32616d52a8dcecac0f3b3cd217396d))

## [2.4.4](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.3...kerrokantasi-v2.4.4) (2025-09-10)


### Dependencies

* Bump django from 4.2.23 to 4.2.24 ([fc2b361](https://github.com/City-of-Helsinki/kerrokantasi/commit/fc2b361638cef7dce794e5a5ab22015fbe6e94c9))

## [2.4.3](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.2...kerrokantasi-v2.4.3) (2025-06-13)


### Bug Fixes

* Make LOGIN_REDIRECT_URL an env var and default to /admin/ ([ac53cc9](https://github.com/City-of-Helsinki/kerrokantasi/commit/ac53cc981bedfd3e49506609521f5a3d4b0424c8))

## [2.4.2](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.1...kerrokantasi-v2.4.2) (2025-06-12)


### Dependencies

* Bump django from 4.2.22 to 4.2.23 ([57e0a3c](https://github.com/City-of-Helsinki/kerrokantasi/commit/57e0a3ca0ea3060aeab2a682fbf5a3f9920d9feb))
* Bump requests from 2.32.2 to 2.32.4 ([f65af19](https://github.com/City-of-Helsinki/kerrokantasi/commit/f65af19d04311e635d43d81bb6debec462c08568))

## [2.4.1](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.4.0...kerrokantasi-v2.4.1) (2025-06-10)


### Dependencies

* Bump django from 4.2.21 to 4.2.22 ([aeead22](https://github.com/City-of-Helsinki/kerrokantasi/commit/aeead22118a9faeb0c504de504cfae2db9851ade))

## [2.4.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.3.3...kerrokantasi-v2.4.0) (2025-06-05)


### Features

* Setting to disable password login in admin site ([0d9cf96](https://github.com/City-of-Helsinki/kerrokantasi/commit/0d9cf96405c34a98070f559f9358268025750adc))

## [2.3.3](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.3.2...kerrokantasi-v2.3.3) (2025-05-13)


### Dependencies

* Use hashable django-helsinki-notification requirement ([7f3f5c8](https://github.com/City-of-Helsinki/kerrokantasi/commit/7f3f5c84cd9818b25c18974147f56626a2ca0ae1))
* Use hashes in requirements ([36d754a](https://github.com/City-of-Helsinki/kerrokantasi/commit/36d754a606f20abaf41a0fdaef10075ce4e4fe6a))

## [2.3.2](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.3.1...kerrokantasi-v2.3.2) (2025-05-12)


### Dependencies

* Bump django from 4.2.20 to 4.2.21 ([624cad3](https://github.com/City-of-Helsinki/kerrokantasi/commit/624cad318e205d72f97f44babef09ae9c76e27cc))

## [2.3.1](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.3.0...kerrokantasi-v2.3.1) (2025-04-23)


### Dependencies

* Update django-helsinki-notification to v0.3.0 ([a41cb45](https://github.com/City-of-Helsinki/kerrokantasi/commit/a41cb45179b610a94d21432f50a2e79c38e25206))

## [2.3.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.2.0...kerrokantasi-v2.3.0) (2025-03-31)


### Features

* Add missing fields in HearingCreateUpdateSerializer ([64b85f4](https://github.com/City-of-Helsinki/kerrokantasi/commit/64b85f408138ebeb565e435cbfd22061e9540876))


### Dependencies

* Update django-helsinki-notification ([e0e9347](https://github.com/City-of-Helsinki/kerrokantasi/commit/e0e93471fca58fe92d2a3eb04bbfda64251cee1b))

## [2.2.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.1.1...kerrokantasi-v2.2.0) (2025-03-10)


### Features

* Add django-helsinki-notification ([d08d796](https://github.com/City-of-Helsinki/kerrokantasi/commit/d08d7962727362f2efc793a9d7fb171c462507a6))


### Dependencies

* Bump django from 4.2.18 to 4.2.20 ([c7f6170](https://github.com/City-of-Helsinki/kerrokantasi/commit/c7f61701ae2914cfb2a83571728772e4e1d77e02))
* Bump python-jose from 3.3.0 to 3.4.0 ([90857c0](https://github.com/City-of-Helsinki/kerrokantasi/commit/90857c0c7d725bd4cff458c73685dab4e2c9cdf6))

## [2.1.1](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.1.0...kerrokantasi-v2.1.1) (2025-02-19)


### Dependencies

* Bump cryptography from 43.0.1 to 44.0.1 ([6edb048](https://github.com/City-of-Helsinki/kerrokantasi/commit/6edb048fb9e052a8fcc8261b935fad5992c0669d))
* Bump django from 4.2.16 to 4.2.17 ([e735d7e](https://github.com/City-of-Helsinki/kerrokantasi/commit/e735d7e4321d0e1e13d4541a4861c82cfe487426))
* Bump django from 4.2.17 to 4.2.18 ([dc74287](https://github.com/City-of-Helsinki/kerrokantasi/commit/dc74287c65fd02720eebb616261ae3bea412ff4a))

## [2.1.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v2.0.0...kerrokantasi-v2.1.0) (2024-12-03)


### Features

* Add command for removing old user data ([9bda14b](https://github.com/City-of-Helsinki/kerrokantasi/commit/9bda14bfdf093e07b3d404bdc784125976c44581))
* Add user data removal util functions ([3e439f8](https://github.com/City-of-Helsinki/kerrokantasi/commit/3e439f8ff75ee29d2f7848d9e4a3b97c46b70428))


### Bug Fixes

* Uwsgi parameter typo ([131216f](https://github.com/City-of-Helsinki/kerrokantasi/commit/131216f6f683f898fea70658001593c168830807))

## [2.0.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v1.6.0...kerrokantasi-v2.0.0) (2024-10-29)


### ⚠ BREAKING CHANGES

* Remove convert_ckeditor_uploads command ([e129e99](https://github.com/City-of-Helsinki/kerrokantasi/commit/e129e9924ed4ef17861b5146e5a66a0323a6187f))
* Remove django-ckeditor and related views ([3c59452](https://github.com/City-of-Helsinki/kerrokantasi/commit/3c5945227de15758043b310287cad395d15d2237))

### Features

* Add application for audit logging ([64ecc66](https://github.com/City-of-Helsinki/kerrokantasi/commit/64ecc66fc4932290593a0ef6da78ed66a105e6ec))
* Add audit logging for BaseCommentViewSet ([c09d2d9](https://github.com/City-of-Helsinki/kerrokantasi/commit/c09d2d989e08e35bf4e83472206e97cfac5e1dfb))
* Add audit logging to ContactPersonViewSet ([3e4b929](https://github.com/City-of-Helsinki/kerrokantasi/commit/3e4b9293fa5e65479bd3ed867db6dac959c22c1d))
* Add audit logging to FileViewSet ([842fc05](https://github.com/City-of-Helsinki/kerrokantasi/commit/842fc0586d109383c3f5c9141ae2e29706e24130))
* Add audit logging to HearingViewSet ([49d8ac2](https://github.com/City-of-Helsinki/kerrokantasi/commit/49d8ac29f1971db8cc73019e67dc6023772093d4))
* Add audit logging to ImageViewSet ([920e80e](https://github.com/City-of-Helsinki/kerrokantasi/commit/920e80e0d7eda9a96d3e446764cdeb5609bc4cb6))
* Add audit logging to LabelViewSet ([005aa8c](https://github.com/City-of-Helsinki/kerrokantasi/commit/005aa8ca8160e82451c5aa341200466b7edaa829))
* Configure audit logging for kerrokantasi ([89aa789](https://github.com/City-of-Helsinki/kerrokantasi/commit/89aa789ef9879815ede1f70d79ffcdffc02ad1df))
* Remove convert_ckeditor_uploads command ([e129e99](https://github.com/City-of-Helsinki/kerrokantasi/commit/e129e9924ed4ef17861b5146e5a66a0323a6187f))
* Remove django-ckeditor and related views ([3c59452](https://github.com/City-of-Helsinki/kerrokantasi/commit/3c5945227de15758043b310287cad395d15d2237))


### Bug Fixes

* Missing filter in ProjectPhaseSerializer.get_has_hearings ([7d2e515](https://github.com/City-of-Helsinki/kerrokantasi/commit/7d2e515b200f11838ad88f1b500b45c477123b70))


### Performance Improvements

* Apply sufficient prefetching in HearingViewSet ([13701fd](https://github.com/City-of-Helsinki/kerrokantasi/commit/13701fd7c2ccdb1e6f40ec4c39d28a04f5a56772))
* Cache hearing for SectionViewSet and prefetch translations ([a958fd9](https://github.com/City-of-Helsinki/kerrokantasi/commit/a958fd9163131a9699813a098b99f6f4ed06ebbe))
* Optimize TranslatableSerializer translations access via cache ([e37ed03](https://github.com/City-of-Helsinki/kerrokantasi/commit/e37ed03c60360145de48e3935444b226f81166ca))
* Prefetch translations in FileViewSet ([724e915](https://github.com/City-of-Helsinki/kerrokantasi/commit/724e9155d004bc105d08e92e11258f60d82ba582))
* Prefetch translations in LabelViewSet ([57b858a](https://github.com/City-of-Helsinki/kerrokantasi/commit/57b858a98a56a1586469d40624b5eefa1f12e620))
* Use prefetched results in  ProjectPhaseSerializer.get_has_hearings ([09f1e60](https://github.com/City-of-Helsinki/kerrokantasi/commit/09f1e60d0c3ff6467acbdcfa1fd741ee2522071f))
* Use prefetched results in ProjectPhaseSerializer.get_hearings ([bb63c06](https://github.com/City-of-Helsinki/kerrokantasi/commit/bb63c068851b573af5f0c2dd4b810efc72385092))


### Dependencies

* Sync pre-commit and development requirements ([c3a8d00](https://github.com/City-of-Helsinki/kerrokantasi/commit/c3a8d0057f3993af062506529b0d77a3c228c839))
* Upgrade dependencies ([ceaa041](https://github.com/City-of-Helsinki/kerrokantasi/commit/ceaa04174d5b455c591b1f811cce65b1dce8070b))


### Documentation

* **readme:** Update isort url ([0490fbf](https://github.com/City-of-Helsinki/kerrokantasi/commit/0490fbf150c8d2413b809a3f775ef6601ab9b25e))


### Build
* Upgrade python to version 3.9 ([62e957](https://github.com/City-of-Helsinki/kerrokantasi/pull/520/commits/62e95786728acf6aed72128b47fac1c800d19179))

## [1.6.0](https://github.com/City-of-Helsinki/kerrokantasi/compare/kerrokantasi-v1.5.0...kerrokantasi-v1.6.0) (2024-08-13)


### Features

* Add admin in organizations field in user admin ([4762dda](https://github.com/City-of-Helsinki/kerrokantasi/commit/4762dda64ddb128cdaad1a71bbf73e593d45942a))


### Bug Fixes

* Hide geojson data from deleted comments ([0867749](https://github.com/City-of-Helsinki/kerrokantasi/commit/086774909b472faf3b043e03b7a18d51d117315c))


### Dependencies

* Add pytest-factoryboy ([ea9c394](https://github.com/City-of-Helsinki/kerrokantasi/commit/ea9c394be5aa5444dee07b14528856d25fdc8220))

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
