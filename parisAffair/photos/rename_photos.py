#!/usr/bin/env python3
from pathlib import Path
import re

def main():
    exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".avif"}
    photo_re = re.compile(r"photo_(\d+)\.\w+$", re.I)

    files = [p for p in Path('.').iterdir() if p.is_file() and p.suffix.lower() in exts]

    # Indices déjà utilisés (photo_12.png, photo_99.jpg, …)
    used = {int(m.group(1)) for p in files if (m := photo_re.fullmatch(p.name))}
    max_used = max(used) if used else 0

    # On renomme uniquement ce qui N’EST PAS déjà un « photo_X.ext »
    to_rename = [p for p in files if not photo_re.fullmatch(p.name)]
    to_rename.sort(key=lambda p: p.name.lower())   # facultatif

    next_idx = max_used + 1
    for f in to_rename:
        while Path(f"photo_{next_idx}{f.suffix.lower()}").exists():
            next_idx += 1            # saute les trous éventuels
        new_name = f"photo_{next_idx}{f.suffix.lower()}"
        f.rename(new_name)
        print(f"{f.name}  →  {new_name}")
        next_idx += 1

if __name__ == "__main__":
    main()
