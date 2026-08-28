# woolroom-packs

The community pack index for [woolroom](https://github.com/minglong51/woolroom) —
the self-hostable shared ambient pet.

A pack adds a species to a woolroom — figure, coats, temperament, voice, habits —
as **data, never code**. Packs live in their authors' own repositories. This repo
is just the list.

## The list

| Pack | Figure | Species | Author | One-liner |
|---|---|---|---|---|
| [pebble](https://github.com/minglong51/woolroom/tree/fd9574babacad8a356d979fbbe956f91681d9e8b/packs/pebble) | <img src="https://raw.githubusercontent.com/minglong51/woolroom/fd9574babacad8a356d979fbbe956f91681d9e8b/.github/assets/pebble.png" width="72" alt="a smooth gray rock with dot eyes, sitting on the room floor" /> | rock | woolroom | the shipped example — deliberately minimal |

## Add your pack

The standalone [Woolpack 0.1.1 package on PyPI](https://pypi.org/project/woolpack/0.1.1/)
scaffolds, renders, and validates packs without a Woolroom checkout:

Prerequisites: Python 3.11+ and
[`uv`](https://docs.astral.sh/uv/getting-started/installation/). The explicit
Woolpack version is the same compatibility contract used by this index's CI;
the authoring commands and verifier pin move together when a release changes.

```sh
uvx --from 'woolpack==0.1.1' woolpack new mole --author YOUR_HANDLE --license MIT
```

1. Build it in `packs/mole`, following the
   [Woolpack quick start](https://github.com/minglong51/woolroom/blob/main/packages/woolpack/README.md)
   and [pack format reference](https://github.com/minglong51/woolroom/blob/main/docs/packs.md).
2. Render and check it. Strict lint must pass, and attach the render board (or
   a screenshot of it) so reviewers can see the figure:

   ```sh
   uvx --from 'woolpack==0.1.1' woolpack render packs/mole -o mole-board.html
   uvx --from 'woolpack==0.1.1' woolpack lint packs/mole --strict
   ```

3. Open a PR here adding **one line** to the table above: pack name (linking to
   your public GitHub repo — a plain repo URL when the pack is at its root, or
   a `/tree/<full-commit-sha>/<dir>` link when it lives in a subdirectory), a small
   figure thumbnail (a crop of your Woolpack render board, hosted in your own
   repo), species, your handle, one honest line. Branch and tag tree links are
   rejected because their ref/path boundary is ambiguous; update the pinned
   commit when a subdirectory pack changes.

CI re-runs step 2 with Woolpack 0.1.1 on the linked repo automatically, so the
PR check is the review of standalone well-formedness. Woolroom revalidates all
configured packs together at boot, where cross-pack collisions can still fail.
Review is of the link line, not your taste — the loader gates and the rig decide
what's safe. Keep it quiet, keep it kind: the room is somebody's home. Packs
that are gamified meters, harassment, or adware will have their links removed.

Your pack is yours: your repo, your license (state it in your pack.yaml).

## Install a pack

Point your woolroom at the pack directory (clone the author's repo, then set
`PACK_PATHS` to the local path) and restart. The loader validates and sanitizes
every pack at boot — a pack that fails a gate keeps the server down with a named
error, never a half-loaded pet.
