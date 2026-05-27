# grab-a-pic

Download a team member's **default colour portrait** from
[liberated.school/team](https://liberated.school/team) by surname.

Each card on that page stacks two images that swap on hover (a Tilda `t857`
block): the colour studio portrait shown by default, and a childhood photo
shown while the pointer hovers. This tool always saves the **default-visible**
one and skips the hover photo.

## Setup

Requires [pixi](https://pixi.sh). The environment pins **Python 3.14**.

```bash
pixi install
```

## Usage

```bash
# Save Тобенгауз.png into the current directory
pixi run grab Тобенгауз

# Pick the output directory
pixi run grab Тобенгауз -o ./photos

# Batch: with no surname, read list.txt (one surname per line)
pixi run grab
pixi run grab -o ./photos

# List every team member (to find the exact spelling)
pixi run list
```

The output file is named after the surname you pass, using the source image's
extension (e.g. `Тобенгауз.png`).

### Batch mode (`list.txt`)

Run with **no surname** and the script reads `list.txt` from the current
directory — one surname per line. Blank lines and `#` comments are ignored, a
leading byte-order mark is tolerated, and an unmatched name is skipped (with a
`[skip]` note) so the rest still run. Example `list.txt`:

```
# math department
Тобенгауз
Ованесян
```

### Options

| Flag | Meaning |
|------|---------|
| `-o, --outdir DIR` | Directory to save into (default: current). |
| `--list` | Print all team members and exit. |
| `--page FILE` | Parse a local HTML file instead of fetching the site. |
| `--no-verify` | Skip the colour sanity check (one fewer download). |

## How the right image is chosen

Selection is by CSS class, not by colour:

* `t857__bgimg_first_hover` — visible when **not** hovering → **saved**
* `t857__bgimg_second` — visible on hover → skipped

By default the tool also downloads the hover image and compares HSV saturation
as a sanity check. Note this is only a *check*, not the selection rule: some
childhood photos are vintage **colour** and can score *more* saturated than the
muted studio portrait (e.g. Ованесян). The class-based rule still picks the
correct default-visible portrait; a mismatch only prints a warning.
