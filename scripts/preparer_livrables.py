"""Publier les petites listes, trois figures et une synthèse PDF depuis les exports."""
from pathlib import Path
import json
import shutil
import textwrap

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

racine = Path(__file__).resolve().parents[1]
source = racine / 'data/processed'
livrables = racine / 'docs/livrables'
images = racine / 'docs/images'
livrables.mkdir(exist_ok=True)
images.mkdir(exist_ok=True)
comparaison = pd.read_csv(source / 'comparaison_selections.csv', sep=';')
listes = pd.read_csv(source / 'listes_scenarios.csv', sep=';', dtype={'ISBN': 'string'})
selection = pd.read_csv(source / 'selection_francais.csv', sep=';', dtype={'ISBN': 'string'})
initiale = pd.read_csv(source / 'selection_initiale.csv', sep=';', dtype={'ISBN': 'string'})
kpi = pd.read_csv(source / 'controle_kpi.csv', sep=';').iloc[0]
base = comparaison.loc[comparaison['Scenario'].eq('Initiale · 100')].iloc[0]
variante = comparaison.loc[comparaison['Scenario'].eq('Deux par auteur · 100')].iloc[0]
for nom in ['selection_francais', 'selection_initiale', 'comparaison_selections', 'listes_scenarios', 'mouvements_selections']:
    shutil.copyfile(source / f'{nom}.csv', livrables / f'{nom}.csv')

# Petits résultats réels réutilisables par le portfolio ; pas de données fictives.
resultats = {
    'date': '2026-10-09', 'datasetVersion': 18, 'datasetYear': 2020,
    'source': 'https://github.com/juleescourne/goodreads-analytics-etl',
    'kpi': json.loads(pd.DataFrame([kpi]).to_json(orient='records'))[0],
    'scenarios': json.loads(comparaison.round(6).to_json(orient='records', force_ascii=False)),
    'listes': json.loads(listes.round(6).to_json(orient='records', force_ascii=False)),
}
(livrables / 'parcours.json').write_text(json.dumps(resultats, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.labelcolor': '#3b4644', 'text.color': '#141a19',
                     'figure.facecolor': '#ffffff', 'axes.facecolor': '#ffffff'})
accent, secondaire = '#0d5e63', '#a8c4c1'
figures = []
fig, ax = plt.subplots(figsize=(10, 4.7), layout='constrained')
labels = ['Français renseigné', 'Critères de candidature', 'Groupes titre / auteur', 'Proposition à relire']
valeurs = [int(kpi['NbFichesFrancais']), int(base.NbCandidats), int(base.NbRepresentants), len(selection)]
barres = ax.barh(labels, valeurs, color=[secondaire, accent, accent, '#9c3327'])
ax.bar_label(barres, labels=[f'{n:,}'.replace(',', ' ') for n in valeurs], padding=6)
ax.invert_yaxis(); ax.set_xlim(0, valeurs[0]*1.15); ax.set_xlabel('Nombre de fiches, puis groupes rapprochés')
ax.set_title('Du catalogue français à une proposition de 20 fiches', loc='left', pad=16, fontweight='bold')
fig.savefig(images / 'parcours-selection.png', dpi=160); figures.append(fig)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.7), layout='constrained')
for ax, titre, champ in [(axes[0], 'Libellés auteur distincts', 'NbAuteurs'), (axes[1], 'Maximum de fiches par auteur', 'MaxParAuteur')]:
    bars=ax.bar(['Initiale', 'Deux par auteur'], [base[champ], variante[champ]], color=[secondaire, accent], width=.55)
    ax.bar_label(bars, fmt='%.0f', padding=5); ax.set_ylim(0, max(base[champ], variante[champ])*1.3); ax.set_title(titre, fontsize=12); ax.set_ylabel('Nombre')
fig.suptitle('Même seuil de 100 notations : une liste moins concentrée', fontsize=14, fontweight='bold')
fig.savefig(images / 'diversite-selection.png', dpi=160); figures.append(fig)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.7), layout='constrained')
for regle, couleur, style in [('Initiale', secondaire, 'o-'), ('Deux par auteur', accent, 's--')]:
    d=comparaison.loc[comparaison.Regle.eq(regle)]
    axes[0].plot(['100', '500', '1 000'], d.NbCommunsReference, style, color=couleur, linewidth=2.5, label=regle)
    axes[1].plot(['100', '500', '1 000'], d.MaxParAuteur, style, color=couleur, linewidth=2.5, label=regle)
axes[0].set_title('Fiches communes avec la référence à 100', fontsize=11); axes[0].set_ylim(0,22); axes[0].set_yticks([0,5,10,15,20]); axes[0].set_ylabel('Fiches sur 20')
axes[1].set_title('Maximum de fiches d’un même auteur', fontsize=11); axes[1].set_ylim(0,11); axes[1].set_yticks([0,2,4,6,8,10]); axes[1].legend(loc='upper left', frameon=False)
for ax in axes: ax.set_xlabel('Minimum de notations'); ax.grid(axis='y', alpha=.15)
fig.suptitle('Un seuil plus strict ne garantit pas plus de diversité', fontsize=14, fontweight='bold')
fig.savefig(images / 'stabilite-selection.png', dpi=160); figures.append(fig)
for fig in figures:plt.close(fig)

# Synthèse analytique, générée en Python ; distincte du rapport natif Power BI.
def page(titre, sous_titre, numero):
    fig=plt.figure(figsize=(11.7,8.3), facecolor='#f6f8f6')
    fig.text(.06,.94,'GOODREADS  /  ÉTUDE DE CAS',fontsize=10,color=accent,weight='bold')
    fig.text(.06,.89,titre,fontsize=22,weight='bold')
    fig.text(.06,.84,sous_titre,fontsize=10,color='#626d6a')
    fig.text(.06,.035,'Jules Courné · Calculs du 09/10/2026 · Données Kaggle v18 / 2020 · Figures issues des exports Python',fontsize=8,color='#626d6a')
    fig.text(.94,.035,str(numero),fontsize=8,ha='right',color='#626d6a')
    return fig

def texte(fig,x,y,s,largeur=108,taille=11):
    fig.text(x,y,textwrap.fill(s,largeur),va='top',fontsize=taille,linespacing=1.55)

with PdfPages(livrables/'Goodreads_synthese.pdf') as pdf:
    fig=page('Quels livres proposer à une équipe éditoriale ?', 'Mission fictive pour Lire & Choisir · une proposition de travail à valider',1)
    texte(fig,.06,.78,'1 850 032 fiches conservées ; 86,40 % de langues absentes ; cinq notations en médiane. Je limite la sélection aux fiches explicitement en français et lis la note avec son volume.')
    ax=fig.add_axes([.05,.24,.90,.45]);ax.imshow(plt.imread(images/'parcours-selection.png'));ax.axis('off')
    texte(fig,.06,.21,'Critères : note ≥ 4/5, au moins 100 notations, auteur et éditeur renseignés, pagination positive et ≤ 5 000. Une fiche représente chaque groupe titre/auteur normalisé. Aucun compteur d’édition n’est additionné.')
    texte(fig,.06,.10,'Décision proposée : plafonner à deux fiches par libellé auteur, puis vérifier les séries, éditions, ISBN et disponibilités avant toute publication.',taille=10)
    pdf.savefig(fig);plt.close(fig)
    fig=page('Comparer les règles avant de choisir', 'Le plafond par auteur complète le classement ; il ne constitue pas un optimum démontré.',2)
    ax=fig.add_axes([.05,.39,.90,.40]);ax.imshow(plt.imread(images/'diversite-selection.png'));ax.axis('off')
    texte(fig,.06,.37,f"Au seuil de 100 notations, {int(variante.CommunsInitiale100)} fiches restent communes avec la liste initiale. Les quatre remplaçantes portent la diversité de {int(base.NbAuteurs)} à {int(variante.NbAuteurs)} libellés auteur. La note moyenne passe de {base.NoteMoyenne:.3f} à {variante.NoteMoyenne:.3f} / 5.")
    rows=[[f'{r.Regle} / {r.NotesMinimum}',int(r.NbCommunsReference),int(r.NbAuteurs),int(r.MaxParAuteur)] for r in comparaison.itertuples()]
    ax=fig.add_axes([.06,.075,.88,.19]);ax.axis('off');t=ax.table(cellText=rows,colLabels=['Règle / seuil','Communs sur 20*','Auteurs','Max / auteur'],cellLoc='center',colWidths=[.43,.21,.18,.18],bbox=[0,0,1,1]);t.auto_set_font_size(False);t.set_fontsize(9)
    for (row,col),c in t.get_celld().items():
        c.set_edgecolor('#dde3dd')
        if row==0:c.set_facecolor(accent);c.set_text_props(color='white',weight='bold')
    fig.text(.06,.055,'* Référence : la liste à 100 notations de la même règle. Les seuils 500 et 1 000 donnent ici les mêmes 20 fiches.',fontsize=8,color='#626d6a')
    pdf.savefig(fig);plt.close(fig)
    fig=page('Tester la stabilité de la proposition', 'Six listes recalculées ; les titres entrants et sortants sont disponibles en CSV et dans le portfolio.',3)
    ax=fig.add_axes([.05,.35,.90,.43]);ax.imshow(plt.imread(images/'stabilite-selection.png'));ax.axis('off')
    texte(fig,.06,.31,'Passer de 100 à 500 notations remplace cinq fiches dans chaque règle. Le classement initial passe de six à neuf fiches pour un même auteur. Un volume minimum plus élevé réduit les candidats, mais peut renforcer la concentration de la liste.')
    texte(fig,.06,.18,'Je propose de garder 100 notations et le plafond de deux par auteur comme point de départ. Le choix reste éditorial : relire les tomes et coffrets, vérifier le catalogue commercial, puis tester une petite page de découverte. Les taux de clic et d’ajout au panier seraient mesurés lors de ce test, sans gain présumé.')
    texte(fig,.06,.085,'Limites : photographie de 2020, pas de stock ni de prix, auteurs/contributeurs non séparés, pas d’identifiant d’œuvre fiable.',largeur=145,taille=8)
    pdf.savefig(fig);plt.close(fig)
    fig=page('Les 20 propositions à examiner', 'Règle retenue : ≥ 100 notations et maximum deux fiches par libellé auteur · éditions et disponibilité non validées',4)
    rows=[]
    for r in selection.itertuples():
        titre=textwrap.shorten(r.Titre,width=76,placeholder='…')
        rows.append([r.RangSelection,titre,r.Auteurs,f'{r.Note:.2f}',f'{int(r.NbNotes):,}'.replace(',',' ')])
    ax=fig.add_axes([.045,.16,.91,.63]);ax.axis('off')
    t=ax.table(cellText=rows,colLabels=['Rang','Titre (abrégé si nécessaire)','Auteur(s)','Note','Notations'],colWidths=[.045,.575,.20,.06,.12],cellLoc='left',bbox=[0,0,1,1]);t.auto_set_font_size(False);t.set_fontsize(7)
    for (row,col),c in t.get_celld().items():
        c.set_edgecolor('#dde3dd')
        if row==0:c.set_facecolor(accent);c.set_text_props(color='white',weight='bold')
        elif row%2==0:c.set_facecolor('#e9f0ed')
    texte(fig,.06,.125,'Les titres complets, identifiants Goodreads et ISBN sont conservés dans selection_francais.csv. Les mentions de tomes, épisodes ou intégrales imposent une relecture éditoriale. Le plafond par auteur ne garantit pas la diversité des séries ou des genres.',taille=9)
    pdf.savefig(fig);plt.close(fig)
print('Synthèse PDF de quatre pages, trois figures et listes réelles publiables générées.')
