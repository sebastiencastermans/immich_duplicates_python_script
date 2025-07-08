"""
🧹 Script de nettoyage de doublons Immich
-----------------------------------------

Ce script a été développé par Sébastien Castermans, aidé par l'IA, pour identifier et conserver
la meilleure version de fichiers doublons (photos/vidéos) sur un serveur Immich via son API.
Il permet de supprimer efficacement les doublons en se basant sur des critères tels que la date
de création, le format HEIC (original d'Apple), la taille du fichier et les métadonnées EXIF.
Le paramètre de détection des doublons est propre à votre installation Immich et peut être
modifié dans les paramètres d'administration du serveur.

💡 Fonctionnalités :
- Tri intelligent pour conserver la meilleure version d’un fichier, d'abord les plus anciens puis 
priorité aux fichiers HEIC (originaux d'apple), sinon selon la taille et enfin les métadonnées EXIF
- Option de simulation (dry-run) pour tester sans supprimer
- Suppression vers corbeille ou définitive
- Journalisation détaillée dans un fichier .log si activée
- Possibilité de visualiser les fichiers avec leur URL dans les logs

Améliorations bienvenues ! Partage libre avec attribution.
"""


import requests
import json
from datetime import datetime
import sys

# Configuration pour l'utilisateur :
ENABLE_LOG_FILE = True # True = crée un fichier immich_duplicates.log, False = pas de fichier log
SERVER = "https://immich.example.com"  # Remplacez par l'URL de votre serveur Immich ou à défaut, l'adresse IP
API_KEY = "ENTER_YOUR_API_KEY_HERE" # Remplacez par votre clé API Immich
DRY_RUN = True  # True = ne fait que simuler pour voir les fichiers choisis en sortie, ne supprime pas réellement
# Mettre à False pour supprimer réellement les doublons
DEFINITELY = False  # True = suppression définitive, False = dans la corbeille



if ENABLE_LOG_FILE:
    log_filename = f"immich_duplicates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    class Tee:
        def __init__(self, *streams):
            self.streams = streams
        def write(self, message):
            for stream in self.streams:
                stream.write(message)
                stream.flush()
        def flush(self):
            for stream in self.streams:
                stream.flush()
    logfile = open(log_filename, 'w', encoding='utf-8')
    sys.stdout = Tee(sys.stdout, logfile)
    sys.stderr = Tee(sys.stderr, logfile)

# Étape 1 : Récupérer les doublons
HEADERS = {
    'Accept': 'application/json',
    'x-api-key': API_KEY
}
try:
    response = requests.get(f"{SERVER}/api/duplicates", headers=HEADERS)
    response.raise_for_status()
    duplicates = response.json()
except requests.RequestException :
    print(f"[ERROR] Échec lors de la récupération des doublons, serveur {SERVER} injoignable ou clé API invalide.")
    exit(1)
if not duplicates:
    print("[INFO] Aucun doublon trouvé. Rien à supprimer.")
    exit(0)


# Étape 2 : Préparer les fichiers à supprimer
def get_asset_info(asset):
    exif = asset.get('exifInfo', {})
    try:
        date = datetime.fromisoformat(exif.get('dateTimeOriginal'))
    except (ValueError, TypeError):
        date = datetime.max  # Pire date si absente
    is_heic = 1 if asset['originalFileName'].lower().endswith('.heic') else 0
    size = exif.get('fileSizeInByte')
    exif_count = sum(1 for v in exif.values() if v is not None and (not isinstance(v, str) or v.strip() != ""))
    return (date, is_heic, size, exif_count)

def select_best_asset(assets):
    remaining = assets[:]
    length = len(remaining)
    reason = "fichiers identiques avec les critères (date, heic, taille, exif)"

    # Étape 1 : date la plus ancienne
    min_date = min(get_asset_info(a)[0] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[0] == min_date]
    if len(remaining) == 1:
        reason = "plus ancien"
        return remaining[0], reason
    if length != len(remaining):
        reason = "plus ancien"
        length = len(remaining)

    # Étape 2 : priorité au .heic
    heic = max(get_asset_info(a)[1] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[1] == heic]
    if len(remaining) == 1:
        reason = "extension heic"
        return remaining[0], reason
    if length != len(remaining):
        reason = "extension heic"
        length = len(remaining)

    # Étape 3 : plus grande taille
    max_size = max(get_asset_info(a)[2] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[2] == max_size]
    if len(remaining) == 1:
        reason = "taille plus grande"
        return remaining[0], reason
    if length != len(remaining):
        reason = "taille plus grande"
        length = len(remaining)

    # Étape 4 : plus de champs EXIF
    max_exif = max(get_asset_info(a)[3] for a in remaining)
    remaining = [a for a in remaining if get_asset_info(a)[3] == max_exif]
    if len(remaining) == 1:
        reason = "exif en plus grand nombre"
        return remaining[0], reason
    if length != len(remaining):
        reason = "exif en plus grand nombre"
        length = len(remaining)

    # Égalité finale
    return remaining[0], reason


ids_to_delete = []
i = 0
for group in duplicates:
    i = i + 1
    assets = group.get('assets')
    kept, reason = select_best_asset(assets)
    date, is_heic, size, exif_count = get_asset_info(kept)
    date_str = date.strftime('%d/%m/%y - %H:%M:%S') if date != datetime.max else "??/??/??"
    print(f"\n[INFO] Doublons n°{i} ({len(assets)} fichiers), raison de conservation : '{reason}'")
    print(f"[GARDÉ]\t\tDate : {date_str}\tTaille : {round(size/1024/1024,2)}MB\t\tNombre d'exif : {exif_count}\t{kept['originalFileName']} --> {SERVER}/api/assets/{kept['id']}/thumbnail?size=preview")
    for asset in assets:
        if asset['id'] != kept['id']:
            date, is_heic, size, exif_count = get_asset_info(asset)
            date_str = date.strftime('%d/%m/%y - %H:%M:%S') if date != datetime.max else "??/??/??"
            print(f"[SUPPRIMÉ]\tDate : {date_str}\tTaille : {round(size/1024/1024,2)}MB\t\tNombre d'exif : {exif_count}\t{asset['originalFileName']} --> {SERVER}/api/assets/{asset['id']}/thumbnail?size=preview")
            ids_to_delete.append(asset['id'])


# Étape 3 : Supprimer les doublons via l'API
if DRY_RUN:
    print("\n[INFO] Mode simulation activé. Aucune suppression réelle effectuée.")
    exit(0)

HEADERS = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY
}
PAYLOAD = json.dumps({"force": DEFINITELY, "ids": ids_to_delete})
try:
    delete_response = requests.delete(f"{SERVER}/api/assets", headers=HEADERS, data=PAYLOAD)
    delete_response.raise_for_status()
    print(f"\n[SUCCESS] Suppression réussie.")
except requests.RequestException:
    print(f"\n[ERROR] Échec de la suppression : {delete_response.status_code} est le code de statut HTTP renvoyé.")
    print(f"[DEBUG] Réponse API : {delete_response.text if 'delete_response' in locals() else 'aucune'}")
