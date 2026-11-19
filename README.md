# Personal Framework CLI

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Ubuntu%20Linux%20%7C%20Windows-lightgrey.svg)](#compatibilité)

**Personal Framework CLI** est un outil en ligne de commande modulaire destiné aux administrateurs réseau, étudiants en réseaux et télécommunications et techniciens système. Il permet de réaliser des diagnostics réseau, d'analyser la configuration locale, de découvrir des équipements autorisés et de produire des rapports structurés.

---

## 🚀 Fonctionnalités prévues (v2.0.0)

- [x] **Architecture modulaire & Moteur de commandes** (pattern Command avec séparation stricte des responsabilités)
- [x] **Système de journalisation centralisé** (logs tournants dans `logs/`)
- [ ] **Diagnostic ICMP (Ping)** enrichi (RTT min/avg/max, taux de pertes, non-bloquant)
- [ ] **Scanner de ports TCP** avec contrôle d'évitement de charge et détection prudente de services
- [ ] **Inspection des interfaces réseau & adressage IP / CIDR**
- [ ] **Résolution DNS** (A, AAAA, MX, PTR, CNAME, NS)
- [ ] **Analyse des tables de routage** locales et passerelle par défaut
- [ ] **Découverte réseau (ARP / LAN)** sur réseaux autorisés
- [ ] **Traceroute & estimation contrôlée du débit**
- [ ] **Surveillance des ressources système** (CPU, RAM, Disque, Processus)
- [ ] **Historique persistant & Rapports exportables** (JSON, CSV, texte brut)

---

## 🛠️ Installation & Prérequis

### Prérequis
* **Système d'exploitation** : Ubuntu Linux (recommandé) ou Windows 10/11
* **Python** : Version 3.10 ou supérieure
* Le cœur du framework utilise **exclusivement la bibliothèque standard Python** (aucun package tiers obligatoire pour démarrer).

### Cloner le projet
```bash
git clone https://github.com/Paterson-web/Projet-CLI.git
cd Projet-CLI
```

### Environnement de développement (optionnel pour les tests)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 🧪 Exécution des tests unitaires

Les tests unitaires sont exécutables sans aucune dépendance externe grâce au module `unittest` de Python :

```bash
python3 -m unittest discover -s tests
```

---

## 📖 Utilisation

### Version v1.1.0 (Historique conservé)
```bash
python3 paterson-cli.py
```

### Version v2.0.0 (En cours de développement)
```bash
python3 main.py
```

---

## 🛡️ Règles d'usage et éthique

Toutes les opérations d'audit, de scan ou de diagnostic réseau menées avec ce framework doivent impérativement être réalisées sur des équipements, des systèmes et des réseaux pour lesquels vous disposez d'une **autorisation explicite**.

---

## 📄 Licence

Ce projet est distribué sous licence MIT. Consultez le fichier [LICENSE](LICENSE) pour plus de détails.
