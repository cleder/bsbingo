<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents** *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [:technologist: How to set up your local environment for development](#technologist-how-to-set-up-your-local-environment-for-development)
  - [Requirements](#requirements)
  - [Setup your environment](#setup-your-environment)
  - [Run the kubernetes cluster and the BsBingo app to develop the code](#run-the-kubernetes-cluster-and-the-bsbingo-app-to-develop-the-code)
  - [PostgreSQL configuration (local development)](#postgresql-configuration-local-development)
  - [Next steps](#next-steps)
  - [Update dependencies](#update-dependencies)
  - [Resource Limits Consideration](#resource-limits-consideration)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# :technologist: How to set up your local environment for development

## Requirements

To work with Kubernetes, you need to install some additional software packages.
Depending on your operating system, the installation instructions may vary.

The documentation and scripts in the repo are written to work with `kubectl`, `kind` and `Tilt`.

Consult the links below if you prefer to use Minikube or Docker Desktop instead:

- [minikube](https://minikube.sigs.k8s.io/docs/start/).
- [Docker](https://docs.docker.com/get-docker/).

## Setup your environment

1. Get the repository

       $ git clone git@github.com:cleder/bsbingo.git
       $ cd bsbingo
       $ cp -n .envrc.example .envrc

2. Prepare the environment variables.
   Edit the `.envrc` file to work for your environment.

       # Example .envrc.local file
       export DEBUG=true
       export LOG_LEVEL=debug
       export LOCAL_DEV_SETTING=custom_value

## Run the kubernetes cluster and the BsBingo app to develop the code

First load the environment variables, then run:

      $ make setup
      $ tilt up

:information_source: It may take a little bit of time for all the services to start up, and it's possible for the first run to fail because of timing conflicts.
If you do see messages indicating there were errors during the first run, stop all the containers using Ctrl-C, and then try it again.

You are now ready to edit the code.
The app will be automatically reloaded when its files change.

To delete resources created by Tilt once you are done working:

       $ tilt down

This will not delete persistent volumes created by Tilt, and you should be able to start Tilt again with your data intact.

To remove the cluster entirely:

       $ kind delete cluster --name bsbingo

To switch between different Scaf project contexts:

      $ tilt down    # inside the codebase of the previous project
      $ make setup   # inside the codebase of the project you want to work on
      $ tilt up

## PostgreSQL configuration (local development)

The Django backend runs against PostgreSQL only -- there is no SQLite fallback, even locally.
`tilt up` brings up a `postgres:17` StatefulSet (`k8s/local/postgres.yaml`) alongside the backend, which is configured via `config.settings.local` (`DJANGO_SETTINGS_MODULE` is set to this automatically by the base `app-config` ConfigMap).
The connection details are supplied by the following environment variables, already exported by `.envrc` once you've run `cp -n .envrc.example .envrc` and `direnv allow`:

| Env var | Required | Notes |
|---|---|---|
| `DATABASE_URL` | Yes (canonical) | Full DSN, e.g. `postgresql://bsbingo:<password>@postgres/bsbingo`. |
| `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | No | Only consulted as a fallback if `DATABASE_URL` is unset. |

If PostgreSQL is unreachable or these variables are missing, the app fails fast with an explicit `ImproperlyConfigured` error rather than silently using a local file.

If you have a `backend/db.sqlite3` file left over from before this project moved to PostgreSQL, delete it -- it is no longer used or read by any settings module.

## Next steps

Creating a superuser account in the backend is useful so you have access to Django Admin that will be accessible at [http://localhost:8000/admin](http://localhost:8000/admin)

To create a superuser use the following commands:

    $ make shell-backend
    $ ./manage.py createsuperuser

## Update dependencies

To update the backend app dependencies, you must edit the `backend/requirements/*.in` files.
Once you have made your changes, you need to regenerate the `backend/requirements/*.txt` files using:

       $ make compile

## Resource Limits Consideration

Resource limits have been predefined for both Django and NextJS services to ensure optimal performance and efficient resource utilization:

- **Django**:
  - Requests: `cpu: 200m`, `memory: 300Mi`
  - Limits: `cpu: 250m`, `memory: 400Mi`

Ensure these values are appropriate for your environment.
If needed, adjust them based on real workload observations in a staging or production environment to balance performance and resource consumption.
