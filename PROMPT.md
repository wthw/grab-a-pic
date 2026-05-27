# Task prompt

Start a pixi project using **Python 3.14** for extracting a number of pictures
from <https://liberated.school/team>.

I need the **colour photos** — the one shown by default, i.e. when the mouse
pointer is **not** hovering above the photo.

The script should take a surname, e.g. `Тобенгауз`, and save `Тобенгауз.jpg`
(or whatever extension the source file has).

**The catch:** do not save the young `Тобенгауз` boy photo (the childhood
picture) that appears when the mouse is hovering over the portrait.

When run **without an argument**, the script should look for `list.txt` and
process it line-by-line (one surname per line).

## Notes from implementation

- The page is a Tilda `t857` block. Each card stacks two images that swap on
  hover; the default-visible one carries the CSS class
  `t857__bgimg_first_hover`, the hover one carries `t857__bgimg_second`.
  Selection is by class, which is the reliable signal.
- The "hover photo is black & white" assumption does not always hold: some
  childhood photos are vintage **colour** and can be more saturated than the
  studio portrait (e.g. Ованесян). Picking by colour would be wrong; picking by
  the hover/default class is correct.

See [README.md](README.md) for usage.
