# woolroom-packs

The community pack index for [woolroom](https://github.com/minglong51/woolroom) —
the self-hostable shared ambient pet.

A pack adds a species to a woolroom — figure, coats, temperament, voice, habits —
as **data, never code**. Packs live in their authors' own repositories. This repo
is just the list.

## The list

| Pack | Species | Author | One-liner |
|---|---|---|---|
| [pebble](https://github.com/minglong51/woolroom/tree/main/packs/pebble) | rock | woolroom | the shipped example — deliberately minimal |

## Add your pack

1. Build it: copy the example, follow [docs/packs.md](https://github.com/minglong51/woolroom/blob/main/docs/packs.md).
2. Check it: `scripts/pack_lint.py <your-pack> --strict` must pass, and attach a
   `pack_render` board (or a screenshot of it) so reviewers can see the figure.
3. Open a PR here adding **one line** to the table above: pack name (linking to
   your repo), species, your handle, one honest line.

Review is of the link line, not your taste — the loader gates and the rig decide
what's safe, and `pack lint` decides what's well-formed. Keep it quiet, keep it
kind: the room is somebody's home. Packs that are gamified meters, harassment,
or adware will have their links removed.

Your pack is yours: your repo, your license (state it in your pack.yaml).

## Install a pack

Point your woolroom at the pack directory (clone the author's repo, then set
`PACK_PATHS` to the local path) and restart. The loader validates and sanitizes
every pack at boot — a pack that fails a gate keeps the server down with a named
error, never a half-loaded pet.
