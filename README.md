Kerro kantasi
=============
Kerro kantasi is an implementation of the eponymous REST API for publishing and participating in public hearings.
It has been built to be used together with participatory democrary UI (https://github.com/City-of-Helsinki/kerrokantasi-ui). Nothing should prevent it from being used with other UI implementations.

Kerro kantasi supports hearings with rich metadata and complex structures. Citizens can be asked for freeform input,
multiple choice polls and map based input. See the Helsinki instance of the UI for examples: https://kerrokantasi.hel.fi/. In addition to gathering citizen input, kerrokantasi-ui is also the primary editor
interface for hearings.

If you wish to see the raw data used by hearings, you may examine the API instance serving the UI: https://api.hel.fi/kerrokantasi/v1/

Technology
----------
Kerro kantasi is implemented using the Python programming language, with Django and Django Rest Framework as the
main structural components.

The API allows for both publishing and editing hearings. Kerrokantasi-ui contains the primary hearing editor.

Kerro kantasi has been designed to allow for anonymous participation in hearings, although that is up to the hearing designer. Citizens may also login to the platform, which allows them to use same identity for multiple hearings and participate in hearings requiring login. Creating and editing hearings always requires a login.

Authentication is handled using JWT tokens. All API requests requiring a login must include `Authorization` header containing a signed JWT token. A request including a JWT token with valid signature is processed with the permissions of the user indicated in the token. If the user does not yet exist, an account is created for them. This means that Kerro kantasi is only loosely coupled to the authentication provider.

Docker Installation
-------------------

### Development

The easiest way to develop is

```
git clone https://github.com/City-of-Helsinki/kerrokantasi.git
cd kerrokantasi
```

Uncomment line https://github.com/City-of-Helsinki/kerrokantasi/blob/main/compose.yaml#L27-L28 to activate
configuring the dev environment with a local file.

Copy the development config file example `config_dev.toml.example`
to `config_dev.toml` (read [Configuration](#configuration) below):
```
cp config_dev.toml.example config_dev.toml
docker compose up dev
```

and open your browser to http://127.0.0.1:8000/.

Run tests with

```
docker compose run dev test
```

### Production

Production setup will require a separate PostGIS database server (see [Prepare database](#prepare-database) below) and file storage for
uploaded files. Once you have a
PostGIS database server running,

```
docker run kerrokantasi
```

In production, configuration is done with corresponding environment variables. See `config_dev.env.example`
for the environment variables needed to set in production and read [Configuration](#configuration) below.


Using local Tunnistamo instance for development with docker
-----------------------------------------------------------

### Set tunnistamo hostname

Add the following line to your hosts file (`/etc/hosts` on mac and linux):

    127.0.0.1 tunnistamo-backend

### Create a new OAuth app on GitHub

Go to https://github.com/settings/developers/ and add a new app with the following settings:

- Application name: can be anything, e.g. local tunnistamo
- Homepage URL: http://tunnistamo-backend:8000
- Authorization callback URL: http://tunnistamo-backend:8000/accounts/github/login/callback/

Save. You'll need the created **Client ID** and **Client Secret** for configuring tunnistamo in the next step.

### Install local tunnistamo

Clone https://github.com/City-of-Helsinki/tunnistamo/.

Follow the instructions for setting up tunnistamo locally. Before running `docker compose up` set the following settings in tunnistamo roots `docker-compose.env.yaml`:

- SOCIAL_AUTH_GITHUB_KEY: **Client ID** from the GitHub OAuth app
- SOCIAL_AUTH_GITHUB_SECRET: **Client Secret** from the GitHub OAuth app

After you've got tunnistamo running locally, ssh to the tunnistamo docker container:

`docker compose exec django bash`

and execute the following four commands inside your docker container:

```bash
./manage.py add_oidc_client -n kerrokantasi-ui -t "id_token token" -u "http://localhost:8086/callback" "http://localhost:8086/silent-renew" -i https://api.hel.fi/auth/kerrokantasi-ui -m github -s dev
./manage.py add_oidc_client -n kerrokantasi-api -t "code" -u http://localhost:8080/complete/tunnistamo/ -i https://api.hel.fi/auth/kerrokantasi -m github -s dev -c
./manage.py add_oidc_api -n kerrokantasi -d https://api.hel.fi/auth -s email,profile -c https://api.hel.fi/auth/kerrokantasi
./manage.py add_oidc_api_scope -an kerrokantasi -c https://api.hel.fi/auth/kerrokantasi -n "Kerrokantasi" -d "Lorem ipsum"
./manage.py add_oidc_client_to_api_scope -asi https://api.hel.fi/auth/kerrokantasi -c https://api.hel.fi/auth/kerrokantasi-ui
```

### Configure Tunnistamo to backend

Change the following configuration in `config_dev.toml`

```
OIDC_API_AUDIENCE=https://api.hel.fi/auth/kerrokantasi
OIDC_API_SCOPE_PREFIX=kerrokantasi
OIDC_API_REQUIRE_SCOPE_FOR_AUTHENTICATION=True
OIDC_API_ISSUER=http://tunnistamo-backend:8000/openid
OIDC_API_AUTHORIZATION_FIELD=https://api.hel.fi/auth

SOCIAL_AUTH_TUNNISTAMO_KEY=https://api.hel.fi/auth/kerrokantasi
SOCIAL_AUTH_TUNNISTAMO_SECRET=<kerrokantasi-api client secret from Tunnistamo here>
SOCIAL_AUTH_TUNNISTAMO_OIDC_ENDPOINT=http://tunnistamo-backend:8000/openid
```


Local development quickstart
----------------------
0. Check you have "Prequisites" listed below
1. Create database `kerrokantasi` with PostGIS (see "Prepare database" below)
2. copy `config_dev.toml.example` to `config_dev.toml`. Check the contents (see "Configuration" below)
3. prepare and activate virtualenv (See "Install" below)
4. `pip install -r requirements.txt`
4. `python manage.py compilemessages`
4. `python manage.py collectstatic` (See "Choose directories for transpiled files" below)
5. `python manage.py runserver` (See "Running in development" below)

Installation
------------
This applies to both development and simple production scale. Note that you won't need to follow this approach to the letter if you have your own favorite Python process.

### Prerequisites

* Python 3.9 or later
* PostgreSQL with PostGIS extension
* Application server implementing WSGI interface (fe. Gunicorn or uwsgi), not needed for development

### Prepare database

Kerro kantasi requires full access to the database, as it will need to create database structures before
first run (and if you change the structures). Easiest way to accomplish this is to create a database user and make this user the owner of the Kerro kantasi database. Example:

     createuser kerrokantasi
     createdb -l fi_FI -E utf8 -O kerrokantasi -T template0 kerrokantasi

Both of these commands must be run with database superuser permissions or similar. Note the UTF8 encoding for the database. Locale does not need to be finnish.

After creating the database, PostGIS extension must be activated:

     psql kerrokantasi
     create extension postgis;

This too requires superuser permissions, database ownership is not enough. PostGIS extension can also require the installation of package ending in -scripts, which might not be marked as mandatory.

### Choose directories for transpiled files and user uploaded files

Kerro kantasi has several files that need to be directly available using HTTP. Mostly they are used for the
internal administration interface, which allows low level access to the data. The files include a browser based editor and map viewer among others. Django calls such artifacts "static files".  The "collectstatic" command gathers all these to a single directory, which can then be served using any HTTP server software (for development, Django runserver will work). You will need to choose this directory. Conventional choices would be:

     /home/kerrokantasi-api/static or
     /srv/kerrokantasi-api/static or even
     /var/www/html/static

Kerro kantasi also allows hearing creators to upload images and other materials relevant to the hearings. These are usually called "media" in Django applications. Access to media is controlled by Kerro kantasi code, because material belonging to unpublished hearing must by hidden. This means that the media directory must NOT be shared using an HTTP server.

Location examples:

     /home/kerrokantasi-api/media
     /srv/kerrokantasi-api/media

For development you probably want to have a common parent directory, which contains directories for static files, media files and code. Having media directory among the code might get messy.

### Choose a directory for the code

Kerro kantasi code files can reside anywhere in the file system. Some conventional places might be:

     /home/kerrokantasi/kerrokantasi-api (data directories would be in the home directory)
     /opt/kerrokantasi-api, with data in /srv/kerrokantasi-api

For development a directory among your other projects is naturally a-ok. You probably already have this code in such a directory.

### Prepare virtualenv

Note that virtualenv can be created in many ways. `virtualenv` command shown here is old-fashioned but generally works well. See here for Python 3 native instructions: https://docs.python.org/3/tutorial/venv.html

     virtualenv -p python3 venv
     source venv/bin/activate

### Install required packages

Install all required packages with pip command:

     pip install -r requirements.txt

### Compile translation .mo files

     python manage.py compilemessages

You will now need to configure Kerro kantasi. Read on.

Configuration
-------------
Kerro kantasi can be configured using either `config_dev.toml` file or environment variables. For production use we recommend using environment variables, especially if you are using containers. WSGI-servers typically allow setting
environment variables from their own configuration files.

Kerro kantasi source code contains heavily commented example configuration file `config_dev.toml.example`. It serves both as a configuration file template and the documentation for configuration options.

### Configuration using `config_dev.toml` directly, for development

Directly using config_dev.toml is quite nice for development. Just `cp config_dev.toml.example config_dev.toml`. If you have created a database called `kerrokantasi` you will be almost ready to start developing. (Some `config_dev.toml` editing may be needed, overindulgence may cause laxative effects).

### Configuration using environment variables, recommended for production

Read through `config_dev.toml.example` and set those environment variables your configuration needs. The environment variables are named exactly the same as the variables in `config_dev.toml.example`. In fact, you could make a copy of the file, edit the copy and source it using the shell mechanisms. This would set all uncommented variables in the file. Many application servers (and `docker compose`) can also read the KEY=VALUE format used in the file and set environment variables based on that.

Do note that nothing prevents you from using config_dev.toml in production if you so wish.

### Running using development server

Just execute the normal Django development server:
`python manage.py runserver`

runserver will reload if you change any files in the source tree. No need to restart it (usually).

### Running using WSGI server ("production")

Kerro kantasi is a Django application and can thus be run using any WSGI implementing server. Examples include gunicorn and uwsgi.

WSGI requires a `callable` for running a service. For kerrokantasi this is:
`kerrokantasi.wsgi:application`
The syntax varies a bit. Some servers might want the file `kerrokantasi/wsgi.py` and `application` as callable.

In addition you will need to server out static files separately. Configure your HTTP server to serve out the files in directory specified using STATIC_ROOT setting with the URL specified in STATIC_URL setting.

Development processes
---------------------

### Updating requirements

Kerrokantasi uses two files for requirements. The workflow is as follows.

`requirements.txt` is not edited manually, but is generated
with `pip-compile`.

`requirements.txt` always contains fully tested, pinned versions
of the requirements. `requirements.in` contains the primary, unpinned
requirements of the project without their dependencies.

In production, deployments should always use `requirements.txt`
and the versions pinned therein. In development, new virtualenvs
and development environments should also be initialised using
`requirements.txt`. `pip-sync` will synchronize the active
virtualenv to match exactly the packages in `requirements.txt`.

In development and testing, to update to the latest versions
of requirements, use the command `pip-compile`. You can
use [requires.io](https://requires.io) to monitor the
pinned versions for updates.

To remove a dependency, remove it from `requirements.in`,
run `pip-compile` and then `pip-sync`. If everything works
as expected, commit the changes.

### Testing

To run all tests, execute command in application root directory.

     py.test democracy/ kerrokantasi/

Run test against particular issue.

    py.test -k test_7 -v

Integration and unit tests are in separate folders, to run only specific type of tests use foldername in path.

     py.test democracy/tests/unittests
     py.test democracy/tests/integrationtests

### Internationalization

Translations are maintained on [Transifex][tx].

* To pull new translations from Transifex, run `npm run i18n:pull`
* As a translation maintainer, run `npm run i18n:extract && npm run i18n:push` to push new source files.

[tx]: https://www.transifex.com/city-of-helsinki/kerrokantasi/dashboard/

### Code format

This project uses
[`black`](https://github.com/ambv/black),
[`flake8`](https://github.com/pycqa/flake8) and
[`isort`](https://github.com/pycqa/isort)
for code formatting and quality checking.

[`pre-commit`](https://pre-commit.com/) can be used to install and
run all the formatting tools as git hooks automatically before a
commit.

## Commit message format

New commit messages must adhere to the [Conventional Commits](https://www.conventionalcommits.org/)
specification, and line length is limited to 72 characters.

When [`pre-commit`](https://pre-commit.com/) is in use, [`commitlint`](https://github.com/conventional-changelog/commitlint)
checks new commit messages for the correct format.

### Git blame ignore refs

Project includes a `.git-blame-ignore-revs` file for ignoring certain commits from `git blame`.
This can be useful for ignoring e.g. formatting commits, so that it is more clear from `git blame`
where the actual code change came from. Configure your git to use it for this project with the
following command:

```shell
git config blame.ignoreRevsFile .git-blame-ignore-revs
```
