import os
from PIL import Image, ImageOps

# Extensions d'images prises en charge
EXTS = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif')

def convert_and_rename_images(folder_path):
    # Liste initiale figée pour ne pas re-traiter ce qu'on crée pendant la boucle
    entries = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder_path, f))
    ]
    entries.sort()  # ordre stable (alphabétique)

    for idx, name in enumerate(entries, start=1):
        src_path = os.path.join(folder_path, name)
        target_name = f"profile_{idx}.png"
        target_path = os.path.join(folder_path, target_name)

        # Si la cible existe déjà (ex: ancien run), on l'écrase volontairement
        # pour garantir une séquence propre search_1..N à chaque exécution.
        try:
            if name.lower().endswith('.png'):
                # PNG → juste renommer (pas de conversion)
                if os.path.abspath(src_path) == os.path.abspath(target_path):
                    print(f"↪️  Déjà OK : {name}")
                    continue
                os.replace(src_path, target_path)  # overwrite si existe
                print(f"✅ {name} → {target_name}")
            else:
                # Non-PNG → convertir en PNG puis supprimer l'original
                with Image.open(src_path) as img:
                    # Respecte l'orientation EXIF si présente
                    img = ImageOps.exif_transpose(img)
                    # Convertit en mode compatible PNG
                    if img.mode not in ("RGB", "RGBA"):
                        img = img.convert("RGBA")
                    img.save(target_path, "PNG")
                os.remove(src_path)
                print(f"✅ {name} (converti) → {target_name}")
        except Exception as e:
            print(f"❌ Erreur avec {name} : {e}")

if __name__ == "__main__":
    # Dossier où se trouve ce script .py
    base_folder = os.path.dirname(os.path.abspath(__file__))
    convert_and_rename_images(base_folder)
