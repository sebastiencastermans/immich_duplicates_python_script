"""
🧹 Script de nettoyage de doublons Immich
-----------------------------------------

Ce script a été développé par Sébastien Castermans, aidé par l'IA, pour identifier et supprimer
automatiquement les fichiers doublons (photos/vidéos) sur un serveur Immich via son API.

💡 Fonctionnalités :
- Tri intelligent pour conserver la meilleure version d’un fichier, d'abord les plus récents puis 
priorité aux fichiers HEIC (originaux d'apple), sinon selon la taille et les métadonnées EXIF
- Option de simulation (dry-run) pour tester sans supprimer
- Suppression vers corbeille ou définitive
- Journalisation automatique dans un fichier .log si activée

Améliorations bienvenues ! Partage libre avec attribution.
"""


import requests
import json
from datetime import datetime
import sys

# Configuration pour l'utilisateur :
ENABLE_LOG_FILE = True # True = crée un fichier immich_duplicates.log, False = pas de log
SERVER = "https://immich.example.com"  # Remplacez par l'URL de votre serveur Immich ou à défaut, l'adresse IP
API_KEY = "INSERT_YOUR_API_KEY_HERE" # Remplacez par votre clé API Immich
DRY_RUN = True  # True = ne fait que simuler pour voir les fichiers choisis en sortie, ne supprime pas réellement
# Mettre à False pour supprimer réellement les doublons
DEFINITIF = False  # False = dans la corbeille, True = suppression définitive



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
    print(f"[ERREUR] Échec lors de la récupération des doublons, serveur {SERVER} injoignable ou clé API invalide.")
    exit(1)

if not duplicates:
    print("[INFO] Aucun doublon trouvé. Rien à supprimer.")
    exit(0)


# Étape 2 : Préparer les fichiers à supprimer
ids_to_delete = []
i = 0
for group in duplicates:
    assets = group.get('assets')
    i = i + 1
    print(f"\n[INFO] Groupe {i} : {len(assets)} doublons trouvés :")
    # Trier selon tes règles :
    def asset_sort_key(asset):
        exif = asset.get('exifInfo', {})
        date_str = exif.get('dateTimeOriginal')
        try:
            date = datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            date = datetime.max  # Classe en dernier s'il manque une date valide
        ext_priority = 0 if asset['originalFileName'].lower().endswith('.heic') else 1 # Priorité pour les HEIC, sinon 1
        size = exif.get('fileSizeInByte')
        exif_count = sum(1 for v in exif.values() if v is not None and (not isinstance(v, str) or v.strip() != ""))
        return (date, ext_priority, size * -1, exif_count * -1)  # Taille et EXIF en négatif pour garder les plus grands
    sorted_assets = sorted(assets, key=asset_sort_key)
    # Garder le premier (meilleur), supprimer le reste
    kept = sorted_assets[0]
    print(f"[GARDÉ]\t\t{round(kept.get('exifInfo', {}).get('fileSizeInByte')/1024/1024,2)}MB\t\t(ID: {kept['id']})\t{kept['originalFileName']}")
    for asset in sorted_assets[1:]:
        print(f"[SUPPRIMÉ]\t{round(asset.get('exifInfo', {}).get('fileSizeInByte')/1024/1024,2)}MB\t\t(ID: {asset['id']})\t{asset['originalFileName']}")
        ids_to_delete.append(asset['id'])

# Étape 3 : Supprimer les doublons via l'API
if DRY_RUN:
    print("\n[INFO] Mode simulation activé. Aucune suppression réelle effectuée.")
    exit(0)

HEADERS = {
  'Content-Type': 'application/json',
  'x-api-key': API_KEY
}
PAYLOAD = json.dumps({"force": DEFINITIF, "ids": ids_to_delete})
try:
    delete_response = requests.delete(f"{SERVER}/api/assets", headers=HEADERS, data=PAYLOAD)
    delete_response.raise_for_status()
    print(f"\n[SUCCESS] Suppression réussie.")
except requests.RequestException:
    print(f"\n[ERREUR] Échec de la suppression : {delete_response.status_code} est le code de statut HTTP renvoyé.")
    print(f"[DEBUG] Réponse API : {delete_response.text if 'delete_response' in locals() else 'aucune'}")