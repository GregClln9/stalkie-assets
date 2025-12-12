#!/usr/bin/env python3
from pathlib import Path
import re
import uuid

def main():
    # Extensions à traiter
    exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.avif'}

    # Récupère tous les fichiers image, triés par nom
    files = sorted(
        [p for p in Path('.').iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: p.name.lower()
    )

    # Étape 1: renommer en noms temporaires pour éviter les collisions
    temp_names = []
    for i, f in enumerate(files, start=1):
        temp_name = f".__tmp_{uuid.uuid4().hex}{f.suffix.lower()}"
        f.rename(temp_name)
        temp_names.append((temp_name, f.suffix.lower()))

    # Étape 2: renommer en photo_1.ext, photo_2.ext, ...
    for i, (tmp, ext) in enumerate(temp_names, start=1):
        new_name = f"photo_{i}{ext}"
        Path(tmp).rename(new_name)
        print(f"{tmp}  →  {new_name}")

if __name__ == '__main__':
    main()
