# Toy Robot

An example robot producing toy enhancements against destiny repository.

## Setup

### Requirements

[Poetry](https://python-poetry.org) is used for dependency management and managing virtual environments. You can install poetry either using pipx or the poetry installer script:

```sh
curl -sSL https://install.python-poetry.org | python3 -
```

### Installing Dependencies

We install the desitny_sdk directly from github, so you will need to have a github ssh key set up to be able to run poetry install.

Once Poetry is installed, install dependencies:

```sh
poetry install
```

## Development

Before commiting any changes, please run the pre-commit hooks. This will ensure that the code is formatted correctly and minimise diffs to code changes when submitting a pull request.

Install the pre-commit hooks:

```sh
poetry run pre-commit install
```

pre-commit hooks will run automatically when you commit changes. To run them manually, use:

```sh
poetry run pre-commit run --all-files
```

See [.pre-commit-config.yaml](.pre-commit-config.yaml) for the list of pre-commit hooks and their configuration.

## Application

Run the development server:

```sh
poetry run fastapi dev --port 8001
```

## Container Image

When building the docker image

```sh
docker buildx build --no-cache --ssh default=$SSH_AUTH_SOCK --tag toy-robot .
```

This [mounts your github ssh key](https://docs.docker.com/reference/dockerfile/#example-access-to-gitlab) in the builder step so that poetry can install destiny_sdk from github.

If you run into trouble you might need to start the ssh agent.

### Manual push

If you want to deploy the toy robot into Azure using the provided terraform infrastructure, you'll need to manually push the docker image to a container registry. We're using destiny-shared-infra for this.

```sh
az login
docker buildx build --no-cache --ssh default=$SSH_AUTH_SOCK --platform linux/amd64 --tag destinyevidenceregistry.azurecr.io/toy-robot .
az acr login --name destinyevidenceregistry
docker push destinyevidenceregistry.azurecr.io/toy-robot:YOUR_TAG
```

Then you can update the container app image with the following command

```sh
az containerapp update -n toy-robot-stag-app -g rg-toy-robot-staging --image destinyevidenceregistry.azurecr.io/toy-robot:latest
```
