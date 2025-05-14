#!/usr/bin/env python3
from pathlib import Path

def main():
    # Extensions d’images que vous acceptez ; ajoutez-en si besoin
    exts = {".jpg", ".avif",".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

    files = [p for p in Path('.').iterdir() if p.is_file() and p.suffix.lower() in exts]

    # Tri facultatif : ici par ordre alphabétique d’origine
    files.sort(key=lambda p: p.name.lower())

    for idx, f in enumerate(files, start=1):
        new_name = f"photo_{idx}{f.suffix.lower()}"
        # Éviter les collisions si le nom existe déjà
        if Path(new_name).exists():
            print(f"[!] {new_name} existe déjà ; je passe {f.name}")
            continue
        f.rename(new_name)
        print(f"{f.name}  →  {new_name}")

if __name__ == "__main__":
    main()
