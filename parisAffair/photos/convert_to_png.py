#!/usr/bin/env python3
"""
Convertit toutes les images du dossier courant en PNG
(et laisse intacte chaque image déjà au format .png).
"""

from pathlib import Path
from PIL import Image

# Ajoutez d'autres extensions si nécessaire
EXTS = {".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}

def main():
    images = [p for p in Path(".").iterdir()
              if p.is_file() and p.suffix.lower() in EXTS | {".png"}]

    for img_path in images:
        if img_path.suffix.lower() == ".png":
            print(f"✓ {img_path.name} est déjà en PNG")
            continue

        # Ouvre l’image et force la conversion en mode RGBA (PNG gère l’alpha)
        with Image.open(img_path) as im:
            im = im.convert("RGBA")

            # Même nom, extension .png
            new_path = img_path.with_suffix(".png")
            if new_path.exists():
                print(f"⚠️  {new_path.name} existe déjà ! Je saute ce fichier.")
                continue

            im.save(new_path, format="PNG", optimize=True)
            print(f"{img_path.name}  →  {new_path.name}")

if __name__ == "__main__":
    main()
