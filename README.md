# Génération auto de quittances de loyer

Génération automatique des quittances PDF via LaTeX.

## Prérequis

- [BasicTeX](https://www.tug.org/mactex/morepackages.html)
- Python 3

Ajouter xelatex au PATH :
```bash
export PATH="$PATH:/Library/TeX/texbin"
```

## Fichiers

- `generate_quittance.py` -> Script de génération
- `signature.png` -> Signature du proprio (vous)

## Utilisation du script

```bash
# Quittance du mois courant (paiement au 12, date de signature du jour)
python3 generate_quittance.py --mois 6 --annee 2026

# Avec dates personnalisées
python3 generate_quittance.py --mois 6 --annee 2026 --date-paiement 18/06/2026 --date-document 19/06/2026
```

Le PDF est créé dans ce dossier : `2026-06_quittance_nom-du-locataire.pdf`
