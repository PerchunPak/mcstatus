This is a script that we use for integration testing.

You need to write data for generating into `data/for_generating.json` file.
Do not touch the other file, `data/for_testing.json`, it needs to be generated via
`python -m scripts.integration_tests generate` command.

## `data/for_generating.json` syntax

It's a list of objects which will be transformed into `services` property inside
our [CI file](https://github.com/py-mine/mcstatus/blob/master/.github/workflows/integration-tests.yml).

Each object has the following properties:

- `id` (Required) - unique identifier of the service, used as a name of the service.
- `image` (Required) - Docker image to use for the service. There is additional special handling for `itzg/minecraft-server` (like adding `EULA=true` into environment variables).
- `expected` (Required) - Expected output of the service. It's in the same format, as our response classes (see [`mcstatus/status_response.py`](https://github.com/py-mine/mcstatus/blob/master/mcstatus/status_response.py)) but in the JSON form.
- `versions` - List of versions to test. Each version will just create a new service with the same parameters, but set environment variable `VERSION` to the version name. **Only supports `itzg/minecraft-server`**.
- `env` - Environment variables to pass to the service.
- `options` - CLI arguments to pass inside container.
