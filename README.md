# Toy Robot

An example robot producing toy enhancements against destiny repository.

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
