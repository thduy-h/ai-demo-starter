# Original synthetic gallery

`blue-square.png`, `green-circle.png`, and `red-circle.png` are original generated examples under the repository MIT license. Recreate them with `uv run python scripts/generate_gallery.py`. They demonstrate the indexing/UI workflow, not model accuracy. Supply your own legally usable images for meaningful search.

Rebuilding the same output index updates it atomically; source images must remain at the indexed root. Do not import symlinks that escape that root.
