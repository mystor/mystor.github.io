This is the source for my personal blog:
[mystor.github.io](https://mystor.github.io)

The site is published to the `master` branch, and served using GitHub pages
when I add new content. The `source` branch contains the current source
working state.

I use [poetry](https://poetry.eustace.io) for dependencies.

```sh
$ poetry install     # Install Dependencies
$ poetry run server  # Run a local development server at https://localhost:8000
$ poetry run publish # Publish changes to master (doesn't push)
```
