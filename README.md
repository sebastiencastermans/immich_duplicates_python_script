# 🧹 Immich Duplicate Cleaner

Script Python pour détecter et supprimer intelligemment les **doublons photo/vidéo** sur un serveur [Immich](https://github.com/immich-app/immich), en **donnant la priorité aux fichiers HEIC (Apple)**.

---

## ✨ Fonctionnalités principales

- 🔍 Détection automatique des doublons via l’API Immich
- 📸 Tri intelligent des fichiers par :
  - **Format préféré** : `.HEIC` en priorité
  - **Date de capture** (`exif.dateTimeOriginal`)
  - **Taille du fichier** (on garde le plus lourd)
  - **Richesse des métadonnées EXIF**
- 🧪 **Mode simulation** pour tester sans supprimer
- 🗑️ Option de suppression dans la corbeille ou définitive
- 📄 Journalisation automatique dans un fichier `.log` (optionnelle)

---

## ⚙️ Pré-requis

- Serveur Immich opérationnel (auto-hébergé ou public)
- Une **clé API** valide
- Python ≥ 3.7
