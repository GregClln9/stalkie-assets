#!/usr/bin/env python3
"""Détecte les images générées par IA d'une histoire et les regénère via l'API OpenAI.

Usage:
    python3 regenerate_ai_images.py scan  [--story parisAffair]
    python3 regenerate_ai_images.py regen [--story parisAffair] [--limit N] [--quality high|medium|low] [--workers 3]

`scan` écrit <story>/ai_images.txt (une ligne par image, éditable à la main).
`regen` lit ce manifeste et écrit les nouvelles versions dans <story>_regen/
en gardant la même arborescence. Les fichiers déjà régénérés sont sautés
(relancer la commande reprend où ça s'était arrêté).

Nécessite: export OPENAI_API_KEY=sk-...
Aucune dépendance Python (stdlib uniquement, `sips` de macOS pour lire les dimensions).
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Dimensions de sortie typiques des générateurs IA (gpt-image-1 / DALL-E / Flux).
# Les photos Pinterest sont servies en 736px de large, jamais sur ces tailles exactes.
AI_DIMENSIONS = {
    (1024, 1536), (1536, 1024), (1024, 1024),
    (768, 1376), (1376, 768),
}

IMAGE_EXTS = {".webp", ".avif", ".png", ".jpg", ".jpeg"}

DEFAULT_PROMPT = (
    "Make this look like a genuine unretouched smartphone photo of the same people in "
    "the same scene: same faces, same hair, same outfits, same poses, same background. "
    "Authentic casual photo aesthetic: harsh natural daylight, slightly blown-out sky, "
    "true-to-life muted colors, visible skin texture and small imperfections, ordinary "
    "amateur composition, subtle noise in the shadows. It must be indistinguishable "
    "from a real photo someone posted on their Instagram, not AI art, not a photoshoot."
)

API_URL = "https://api.openai.com/v1/images/edits"


def image_dimensions(path: Path):
    out = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
        capture_output=True, text=True,
    ).stdout
    w = h = None
    for line in out.splitlines():
        if "pixelWidth" in line:
            w = int(line.split()[-1])
        elif "pixelHeight" in line:
            h = int(line.split()[-1])
    return (w, h) if w and h else None


def scan(story_dir: Path) -> Path:
    manifest = story_dir / "ai_images.txt"
    found = []
    for path in sorted(story_dir.rglob("*")):
        if path.suffix.lower() not in IMAGE_EXTS or not path.is_file():
            continue
        dims = image_dimensions(path)
        if dims in AI_DIMENSIONS:
            found.append(path.relative_to(story_dir))
            print(f"  [IA {dims[0]}x{dims[1]}] {path.relative_to(story_dir)}")
    manifest.write_text("\n".join(str(p) for p in found) + "\n")
    print(f"\n{len(found)} images IA détectées -> {manifest}")
    print("Vérifie la liste et supprime les lignes en trop avant de lancer `regen`.")
    return manifest


def target_size(dims):
    w, h = dims
    if w > h:
        return "1536x1024"
    if w < h:
        return "1024x1536"
    return "1024x1024"


def api_edit(image_path: Path, prompt: str, size: str, quality: str, api_key: str,
             model: str) -> bytes:
    """POST multipart vers /v1/images/edits, renvoie les octets webp de l'image."""
    boundary = uuid.uuid4().hex
    mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg",
            "jpeg": "image/jpeg", "avif": "image/avif"}[image_path.suffix.lstrip(".").lower()]

    def field(name, value):
        return (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n').encode()

    body = b"".join([
        field("model", model),
        field("prompt", prompt),
        field("size", size),
        field("quality", quality),
        field("output_format", "webp"),
        field("n", "1"),
        (f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; '
         f'filename="{image_path.name}"\r\nContent-Type: {mime}\r\n\r\n').encode(),
        image_path.read_bytes(),
        f"\r\n--{boundary}--\r\n".encode(),
    ])

    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read())
    return base64.b64decode(data["data"][0]["b64_json"])


def regen_one(story_dir: Path, out_dir: Path, rel: str, prompt: str, quality: str,
              api_key: str, model: str):
    src = story_dir / rel
    dst = (out_dir / rel).with_suffix(".webp")
    if dst.exists():
        return f"skip (déjà fait): {rel}"
    dims = image_dimensions(src)
    if not dims:
        return f"ERREUR dims illisibles: {rel}"

    # L'API n'accepte pas l'avif en entrée -> conversion temporaire en png via sips
    tmp = None
    if src.suffix.lower() == ".avif":
        tmp = dst.parent / f".tmp_{src.stem}.png"
        dst.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["sips", "-s", "format", "png", str(src), "--out", str(tmp)],
                       capture_output=True, check=True)
        src = tmp

    try:
        for attempt in range(4):
            try:
                webp = api_edit(src, prompt, target_size(dims), quality, api_key, model)
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:300]
                if e.code in (429, 500, 502, 503) and attempt < 3:
                    wait = 15 * (attempt + 1)
                    print(f"  retry dans {wait}s ({e.code}) {rel}", flush=True)
                    time.sleep(wait)
                    continue
                return f"ERREUR API {e.code}: {rel} — {detail}"
            except (urllib.error.URLError, TimeoutError) as e:
                if attempt < 3:
                    time.sleep(15)
                    continue
                return f"ERREUR réseau: {rel} — {e}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(webp)
        return f"OK: {rel} -> {dst.relative_to(out_dir.parent)}"
    finally:
        if tmp and tmp.exists():
            tmp.unlink()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=["scan", "regen"])
    ap.add_argument("--story", default="parisAffair")
    ap.add_argument("--limit", type=int, default=0, help="ne traiter que N images (test)")
    ap.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--model", default="gpt-image-2",
                    help="modèle OpenAI (gpt-image-2, gpt-image-1.5, gpt-image-1...)")
    ap.add_argument("--files", nargs="*", default=None,
                    help="chemins relatifs à traiter au lieu du manifeste (ex: photos/photo_3.webp)")
    args = ap.parse_args()

    story_dir = Path(__file__).parent / args.story
    if not story_dir.is_dir():
        sys.exit(f"Dossier introuvable: {story_dir}")

    if args.command == "scan":
        scan(story_dir)
        return

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY manquante. Fais: export OPENAI_API_KEY=sk-...")

    if args.files:
        rels = args.files
        missing = [r for r in rels if not (story_dir / r).is_file()]
        if missing:
            sys.exit(f"Fichiers introuvables dans {story_dir}: {missing}")
    else:
        manifest = story_dir / "ai_images.txt"
        if not manifest.exists():
            sys.exit(f"Manifeste manquant ({manifest}). Lance d'abord: python3 regenerate_ai_images.py scan")
        rels = [l.strip() for l in manifest.read_text().splitlines() if l.strip()]
    out_dir = story_dir.parent / f"{args.story}_regen"
    todo = [r for r in rels if not (out_dir / r).with_suffix(".webp").exists()]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(rels)} images au manifeste, {len(todo)} à générer -> {out_dir}/")

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(regen_one, story_dir, out_dir, r, args.prompt, args.quality,
                               api_key, args.model): r
                   for r in todo}
        for fut in as_completed(futures):
            done += 1
            print(f"[{done}/{len(todo)}] {fut.result()}", flush=True)


if __name__ == "__main__":
    main()
