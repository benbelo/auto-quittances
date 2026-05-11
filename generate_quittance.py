#!/usr/bin/env python3
"""Génère une quittance de loyer PDF."""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date

# ── Configuration ──────────────────────────────────────────────────────────────
PROPRIETAIRE     = "M. Vendeur de sommeil"
LOCATAIRE        = "M. Mauvais payeur"
ADRESSE_LOGEMENT = "10 Avenue des Champs Elysées, 75000 Paris"
LOYER_HC         = 550
CHARGES          = 50
TOTAL_CC         = 600
TOTAL_EN_LETTRES = "six cents"
JOUR_PAIEMENT    = 12
VILLE_SIGNATURE  = "Paris"

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
SIGNATURE_IMG = os.path.join(SCRIPT_DIR, "signature.png")

MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars",    4: "avril",
    5: "mai",     6: "juin",    7: "juillet",  8: "août",
    9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

# ── LaTeX template ─────────────────────────────────────────────────────────────
# Les placeholders évitent délibérément les underscores (caractère spécial LaTeX).
TEMPLATE = r"""
\documentclass[a4paper,11pt]{article}
\usepackage{fontspec}
\usepackage[top=2.2cm,bottom=2.2cm,left=2.8cm,right=2.8cm]{geometry}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{parskip}
\usepackage{setspace}
\usepackage{microtype}

\setmainfont{Helvetica Neue}

\definecolor{accentblue}{HTML}{12a6d0}
\definecolor{lightgray}{HTML}{f2f2f2}

\pagestyle{empty}
\setlength{\parindent}{0pt}

\begin{document}

%% ── En-tête ───────────────────────────────────────────────────────────────────
\begin{center}
  {\fontsize{28}{34}\selectfont\bfseries QUITTANCE DE LOYER}\par
  \vspace{6pt}
  {\large\color{accentblue} Quittance de loyer du mois de TMOISNOM TANNEE}
\end{center}

\vspace{8pt}
{\color{accentblue}\hrule height 1.5pt}
\vspace{14pt}

%% ── Logement ──────────────────────────────────────────────────────────────────
\textbf{Logement concerné :} TADRESSE

\vspace{14pt}

%% ── Corps ─────────────────────────────────────────────────────────────────────
\begin{spacing}{1.5}
Je soussigné \textbf{TPROPRIETAIRE}, propriétaire du logement désigné
ci-dessus, déclare avoir reçu de \textbf{TLOCATAIRE},
la somme de \textbf{TTOTALLETTRES} (\textbf{TTOTALCC~euros})
au titre du paiement du loyer et des charges pour la période de location
du \textbf{TDATEDEBUT} au \textbf{TDATEFIN}
et lui en donne quittance, sous réserve de tous mes droits.
\end{spacing}

\vspace{14pt}

%% ── Détail ────────────────────────────────────────────────────────────────────
\textbf{Détail du règlement :}

\vspace{6pt}
\colorbox{lightgray}{%
  \begin{tabularx}{0.55\textwidth}{X r}
    Loyer H.C.           & TLOYERHC~euros \\[4pt]
    Charges              & TCHARGES~euros \\[4pt]
    \midrule
    \textbf{Total C.C.}  & \textbf{TTOTALCC~euros} \\
  \end{tabularx}%
}

\vspace{14pt}
Date du paiement : le \textbf{TDATEPAIEMENT}

\vspace{24pt}

%% ── Signature ─────────────────────────────────────────────────────────────────
\begin{flushright}
  Fait à TVILLE, le TDATEDOC\par
  \vspace{6pt}
  \includegraphics[width=4.5cm]{TSIGNATURE}
\end{flushright}

\vspace{16pt}
{\color{accentblue}\hrule height 0.5pt}
\vspace{6pt}

%% ── Mention légale ────────────────────────────────────────────────────────────
{\fontsize{7}{9}\selectfont\itshape
Cette quittance annule tous les reçus qui auraient pu être établis
précédemment en cas de paiement partiel du montant du présent terme.
Elle est à conserver pendant trois ans par le locataire
(article 7-1 de la loi n\textsuperscript{o}~89-462 du 6~juillet~1989).}

\end{document}
"""


def build_tex(mois: int, annee: int, date_paiement: str, date_document: str) -> str:
    debut = f"01/{mois:02d}/{annee}"
    mois_suivant, annee_suivante = (1, annee + 1) if mois == 12 else (mois + 1, annee)
    fin = f"01/{mois_suivant:02d}/{annee_suivante}"
    sig_path = SIGNATURE_IMG.replace("\\", "/")

    replacements = {
        "TMOISNOM":      MOIS_FR[mois],
        "TANNEE":        str(annee),
        "TADRESSE":      ADRESSE_LOGEMENT,
        "TPROPRIETAIRE": PROPRIETAIRE,
        "TLOCATAIRE":    LOCATAIRE,
        "TTOTALLETTRES": TOTAL_EN_LETTRES,
        "TTOTALCC":      str(TOTAL_CC),
        "TDATEDEBUT":    debut,
        "TDATEFIN":      fin,
        "TLOYERHC":      str(LOYER_HC),
        "TCHARGES":      str(CHARGES),
        "TDATEPAIEMENT": date_paiement,
        "TVILLE":        VILLE_SIGNATURE,
        "TDATEDOC":      date_document,
        "TSIGNATURE":    sig_path,
    }

    tex = TEMPLATE
    for placeholder, value in replacements.items():
        tex = tex.replace(placeholder, value)
    return tex


def find_xelatex():
    for candidate in ["xelatex", "/Library/TeX/texbin/xelatex", "/usr/texbin/xelatex"]:
        found = shutil.which(candidate)
        if found:
            return found
    if os.path.isfile("/Library/TeX/texbin/xelatex"):
        return "/Library/TeX/texbin/xelatex"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Génère une quittance de loyer PDF"
    )
    parser.add_argument("--mois",          type=int, required=True,
                        help="Mois (1-12)")
    parser.add_argument("--annee",         type=int, required=True,
                        help="Année (ex: 2026)")
    parser.add_argument("--date-paiement", default=None,
                        help="Date de paiement DD/MM/YYYY (défaut : le 12 du mois)")
    parser.add_argument("--date-document", default=None,
                        help="Date du document DD/MM/YYYY (défaut : aujourd'hui)")
    args = parser.parse_args()

    if not 1 <= args.mois <= 12:
        sys.exit("Erreur : --mois doit être entre 1 et 12")

    date_paiement = args.date_paiement or f"{JOUR_PAIEMENT:02d}/{args.mois:02d}/{args.annee}"
    date_document = args.date_document or date.today().strftime("%d/%m/%Y")

    xelatex = find_xelatex()
    if not xelatex:
        sys.exit(
            "xelatex introuvable. Installez BasicTeX :\n"
            "  brew install --cask basictex\n"
            "puis relancez votre terminal."
        )

    tex = build_tex(args.mois, args.annee, date_paiement, date_document)

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "quittance.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex)

        for _ in range(2):  # deux passes pour booktabs
            result = subprocess.run(
                [xelatex, "-interaction=nonstopmode", "-halt-on-error", "quittance.tex"],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

        if result.returncode != 0:
            log_path = os.path.join(tmpdir, "quittance.log")
            if os.path.exists(log_path):
                with open(log_path) as f:
                    print(f.read()[-3000:])
            sys.exit("Erreur de compilation LaTeX (voir log ci-dessus).")

        nom_fichier = f"{args.annee}-{args.mois:02d}_quittance_alan-rakotoarisoa.pdf"
        pdf_dst = os.path.join(SCRIPT_DIR, nom_fichier)
        shutil.copy2(os.path.join(tmpdir, "quittance.pdf"), pdf_dst)

    print(f"Quittance générée : {pdf_dst}")


if __name__ == "__main__":
    main()
