# woolroom-packs

The community pack index for [woolroom](https://github.com/minglong51/woolroom) —
the self-hostable shared ambient pet.

A pack adds a species to a woolroom — figure, coats, temperament, voice, habits —
as **data, never code**. Packs live in their authors' own repositories. This repo
is just the list.

## The list

| Pack | Figure | Species | Author | One-liner |
|---|---|---|---|---|
| [pebble](https://github.com/minglong51/woolroom/tree/main/packs/pebble) | <img src="https://raw.githubusercontent.com/minglong51/woolroom/main/.github/assets/pebble.png" width="72" alt="a smooth gray rock with dot eyes, sitting on the room floor" /> | rock | woolroom | the shipped example — deliberately minimal |

## Add your pack

The authoring tools currently run from a woolroom checkout; a standalone
`uvx woolpack` command is not shipped yet. This setup installs woolroom's server
environment as well as the pack tools:

```sh
git clone --depth 1 https://github.com/minglong51/woolroom.git woolroom-tools
cd woolroom-tools
uv sync --locked
.venv/bin/python scripts/pack_new.py mole --dest ../mole --author YOUR_HANDLE
```

1. Build it in `../mole`, following
   [docs/packs.md](https://github.com/minglong51/woolroom/blob/main/docs/packs.md).
2. Check it from `woolroom-tools`; strict lint must pass, and attach the render
   board (or a screenshot of it) so reviewers can see the figure:

   ```sh
   .venv/bin/python scripts/pack_render.py ../mole
   .venv/bin/python scripts/pack_lint.py ../mole --strict
   ```

3. Open a PR here adding **one line** to the table above: pack name (linking to
   your repo — a plain repo URL, or a `/tree/<branch>/<dir>` link if the pack
   lives in a subdirectory), a small figure thumbnail (a crop of your
   `pack_render` board, hosted in your own repo), species, your handle, one
   honest line.

CI re-runs step 2 on the linked repo automatically, so the PR check IS the
review of well-formedness. Review is of the link line, not your taste — the
loader gates and the rig decide what's safe, and `pack lint` decides what's
well-formed. Keep it quiet, keep it kind: the room is somebody's home. Packs
that are gamified meters, harassment, or adware will have their links removed.

Your pack is yours: your repo, your license (state it in your pack.yaml).

## Install a pack

Point your woolroom at the pack directory (clone the author's repo, then set
`PACK_PATHS` to the local path) and restart. The loader validates and sanitizes
every pack at boot — a pack that fails a gate keeps the server down with a named
error, never a half-loaded pet.
