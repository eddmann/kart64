# Deploying Kart64

[Back to Kart64](../README.md) · [Build setup](development.md)

Kart64 builds locally and ships as a static site. GitHub Pages serves the
finished files from `gh-pages`; it does not compile the game on GitHub.

## Publish to GitHub Pages

Commit the source changes first. The publishing script requires a clean
working tree, and the site commit records the source commit it was built from.
Run from the repository root:

```sh
make deploy
```

This builds incrementally, assembles the deployable files, and replaces the
`gh-pages` branch on `origin` with a single site commit.

To publish the existing engine build, with the current browser page copied
into it:

```sh
make deploy/no-build
```

The [build guide](development.md) describes the tools and local output directory.

## Use another static host

```sh
make dist
```

Upload the resulting `dist/` directory to an HTTPS host. The assembly script
uses an explicit file list.
ROMs and extracted `mk64.o2r` assets are excluded from deployment.

The Mario Raceway phone showcase under `media/` is presented in the GitHub
READMEs; it is not part of the site's deployment file list.

## Cross-origin isolation

The game needs a cross-origin-isolated page for its threaded WebAssembly build.
GitHub Pages cannot provide the required response headers, so `web/coi-sw.js`
uses a service worker to add them. The page reloads once on a first visit.

The local development server from `make start` supplies the isolation headers
directly. `make start/plain` omits them to exercise the service-worker path
used on Pages.
