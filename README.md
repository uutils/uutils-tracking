# uutils tracking

Common code of the uutils/*-tracking repositories:
[awk](https://github.com/uutils/awk-tracking),
[diffutils](https://github.com/uutils/diffutils-tracking),
[findutils](https://github.com/uutils/findutils-tracking),
[grep](https://github.com/uutils/grep-tracking) and
[sed](https://github.com/uutils/sed-tracking).

## Reusable workflow

[`gnu-tracking.yml`](.github/workflows/gnu-tracking.yml) fetches the date-keyed
summary and the full report that a project's `GnuTests.yml` publishes as
artifacts, appends the summary to `gnu-result.json`, keeps the report as
`aggregated-result.json`, then refreshes `gnu-results.svg`, committing each step
to the calling repository.

```yaml
name: CI

on:
  push:
    branches:
    - main
  schedule:
  - cron: "0 2,14 * * *"

jobs:
  gnu:
    permissions:
      contents: write
    uses: uutils/uutils-tracking/.github/workflows/gnu-tracking.yml@main
    with:
      repo: uutils/sed
      summary-file: sed-gnu-result.json
      full-result-artifact: sed-gnu-full-result
      full-result-file: sed-gnu-full-result.json
```

See the `inputs` of the workflow for the other settings (source workflow,
branch, artifact names, testsuite title).

## Graph action

[`render-graph`](render-graph/action.yml) plots a date-keyed result file, for
repositories that collect their data in their own way:

```yaml
    - uses: uutils/uutils-tracking/render-graph@main
      with:
        json: bfs-result.json
        title: BFS
        project: findutils
```

## Running the graph locally

```sh
python3 graph.py tests/gnu-result.json GNU --project awk --output tests/gnu-results.svg
```

It needs pandas, matplotlib and seaborn.
