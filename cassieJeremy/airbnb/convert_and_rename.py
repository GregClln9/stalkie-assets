#!/usr/bin/env python3
import os
import subprocess
from pathlib import Path

# Dossier de base
base_dir = Path(__file__).parent

# Parcourir tous les dossiers logement_*
for logement_dir in sorted(base_dir.glob("logement_*")):
    if not logement_dir.is_dir():
        continue

    print(f"\nTraitement de {logement_dir.name}...")

    # Trouver tous les fichiers .avif
    avif_files = sorted(logement_dir.glob("*.avif"))

    if not avif_files:
        print(f"  Aucun fichier .avif trouvé")
        continue

    # Convertir et renommer chaque fichier
    for index, avif_file in enumerate(avif_files, start=1):
        try:
            # Nouveau nom de fichier
            new_name = f"photo_{index}.webp"
            new_path = logement_dir / new_name

            # Utiliser ffmpeg pour convertir AVIF en WebP
            result = subprocess.run(
                ["ffmpeg", "-i", str(avif_file), "-q:v", "85", str(new_path), "-y"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print(f"  Converti: {avif_file.name} -> {new_name}")
                # Supprimer l'ancien fichier .avif
                avif_file.unlink()
            else:
                print(f"  Erreur avec {avif_file.name}: {result.stderr}")

        except Exception as e:
            print(f"  Erreur avec {avif_file.name}: {e}")

print("\n✓ Conversion et renommage terminés!")
