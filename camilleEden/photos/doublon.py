#!/usr/bin/env python3
from pathlib import Path
import hashlib

def file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Retourne le hash MD5 du fichier."""
    h = hashlib.md5()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    # Extensions à traiter
    exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.avif'}

    # Tous les fichiers image du dossier courant, triés par nom
    files = sorted(
        [p for p in Path('.').iterdir() if p.is_file() and p.suffix.lower() in exts],
        key=lambda p: p.name.lower()
    )

    print(f"{len(files)} fichiers trouvés.\n")

    seen_hashes = {}
    duplicates = []

    # Étape 1 : calcul des hash pour chaque fichier
    for f in files:
        h = file_hash(f)
        if h in seen_hashes:
            # Doublon trouvé
            duplicates.append((f, seen_hashes[h]))
        else:
            seen_hashes[h] = f

    # Étape 2 : suppression des doublons
    if not duplicates:
        print("Aucun doublon trouvé.")
        return

    print(f"{len(duplicates)} doublons trouvés :\n")

    for dup, original in duplicates:
        print(f"❌ Doublon : {dup.name}  (identique à {original.name})")
        dup.unlink()  # suppression
        print(f"🗑️  {dup.name} supprimé.\n")

    print("✔️ Nettoyage terminé.")


if __name__ == "__main__":
    main()
