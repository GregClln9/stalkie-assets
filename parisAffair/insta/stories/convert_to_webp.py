import os
from PIL import Image

QUALITY = 80  # qualité webp (0-100)

def convert_folder_to_webp(folder="."):
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                path = os.path.join(root, file)
                name, _ = os.path.splitext(file)
                out_path = os.path.join(root, f"{name}.webp")

                try:
                    with Image.open(path) as img:
                        img.save(out_path, "WEBP", quality=QUALITY, method=6)
                    os.remove(path)  # supprime l’original
                    print(f"✅ {path} -> {out_path}")
                except Exception as e:
                    print(f"❌ Erreur sur {path}: {e}")

if __name__ == "__main__":
    convert_folder_to_webp(".")  # "." = dossier courant
