# 🧹 Immich Duplicate Cleaner (english, french below)

Python script to intelligently detect and delete **duplicate photos/videos** on a [Immich](https://github.com/immich-app/immich) server, prioritizing heic (Apple) files over size.

---

## ✨ Main features

- 🔍 Automatic recovery of duplicates via the Immich API
- 📸 Intelligent file sorting by :
  1. **Date taken** (`exif.dateTimeOriginal`)
  2. **Preferred format** : `.heic` in priority
  3. **File's size** (we keep the largest)
  4. **Richness of EXIF metadata**
- 🧪 **Simulation mode** to test without deleting, useful for viewing logs
- 🗑️ Option to delete to the recycle bin or permanently
- 📄 Automatic logging to a `.log` file (optional)

---

## ⚙️ Prerequisites

- Immich server operational (self-hosted or public)
- A valid **API key**
- Python ≥ 3.7
- Requests module, simply install it with `pip install requests` in the terminal

---

# 🧹 Nettoyeur de doublons Immich (français)

Script Python pour détecter et supprimer intelligemment les **doublons photos/vidéos** sur un serveur [Immich](https://github.com/immich-app/immich), en **donnant la priorité aux fichiers heic (Apple)** par rapport à la taille.

---

## ✨ Fonctionnalités principales

- 🔍 Récupération automatique des doublons via l’API Immich
- 📸 Tri intelligent des fichiers par :
  - **Date de capture** (`exif.dateTimeOriginal`)
  - **Format préféré** : `.heic` en priorité
  - **Taille du fichier** (on garde le plus lourd)
  - **Richesse des métadonnées EXIF**
- 🧪 **Mode simulation** pour tester sans supprimer, utile pour voir les logs
- 🗑️ Option de suppression dans la corbeille ou définitive
- 📄 Journalisation automatique dans un fichier `.log` (optionnelle)

---

## ⚙️ Pré-requis

- Serveur Immich opérationnel (auto-hébergé ou public)
- Une **clé API** valide
- Python ≥ 3.7
- Module requests, installez-le simplement en exécutant la commande `pip install request` dans le terminal
