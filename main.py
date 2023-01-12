# -*- coding: utf-8 -*-
"""Modèle_de_ségrégation.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1UWnyR_LAGNzgheMsmKq8-E-nRcZOt-sd

#**Descriptif du projet** 

En 1971, Thomas Schelling proposa un modèle de ségrégation sociale très simple, basé sur le fait qu'un individu (un "agent") 
préfère être entouré d'un certain nombre d'agents identiques. Le modèle considère une grille 2D contenant NxN cases. 
Une case peut être vide, contenir un agent d'un type (par exemple de couleur bleue) ou d'un autre (de couleur rouge). 
Le nombre total d'agents est fixé, de façon à laisser un certain nombre de cases vides. 
La dynamique imposée est simple : pour un agent donné, on compte le nombre total T d'agents dans les 8 cases qui l'entourent, 
le nombre S d'agents identiques, et si S/T est plus petit que C (un seuil critique entre 0 et 1), on déplace l'agent à la case donnée la plus proche. 
Selon les paramètres (nombre d'agents de chaque couleur, taille de la grille, valeur de C), on observera différents comportements dynamiques. 
On pourra notamment trouver des paramètres critiques de transition de phase caractérisant la ségrégation.
"""
import threading
from os.path import isfile, join

# Library
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import colors
import random
import imageio
from datetime import datetime
import os
import glob

from concurrent.futures import ThreadPoolExecutor

# Paramètres de la simulation

SHAPE_GRILLE = (200, 200)
N_BLEU, N_ROUGE = int(200*200*0.4), int(200*200*0.4)
T = 1.25 / 8
ITER_MAX = 1000

# ---------------------------------

count_images_saved = 0
lock = threading.Lock()


def create_folder(where, name_new_folder=None):
    new_folder_path = f"{where}/{name_new_folder}/" if name_new_folder else f"{where}/"
    if not os.path.exists(new_folder_path):
        os.mkdir(new_folder_path)
    return new_folder_path


"""# **I-Initialisation de la grille 2D**"""


def init_grille_2D(n, m):
    grille_2D = np.ones((n, m)) * (-1)  # Grille 2D de cases vides
    return grille_2D


"""# **II- Affichage de la grille 2D**"""


def affiche_grille_2D(grille):
    n, m = grille.shape  # Taille de la grille
    for i in range(n):
        for j in range(m):
            agent = grille[i][j]  # On parcourt la grille
            if (agent == 1):  # Si agent est bleu (soit 1) alors on affiche une croix
                print("X", end=" ")
            elif (agent == 2):  # Sinon si l'agent est rouge (soit 2) alors on affiche un cercle
                print("O", end=" ")
            else:  # Sinon on laisse la case vide.
                print(" ", end=" ")
        print(" ")


"""# **III - Placer agents sur la grille de façon aléatoire.**"""


# Fonction permettant de placer un agent
def placer_agent(grille, i, j, couleur):
    if couleur == "b":
        grille[i][j] = 1
    elif couleur == "r":
        grille[i][j] = 2


# Fonction permettant de placer N agents
def placer_N_agents(grille, n, couleur):
    for k in range(n):
        i_agent = np.random.randint(0, grille.shape[0])  # Valeurs random des coords (i,j)
        j_agent = np.random.randint(0, grille.shape[1])

        while grille[i_agent][
            j_agent] != -1:  # Tant que case différente de vide (soit case occupée) on réitère les coords...
            i_agent = np.random.randint(0, grille.shape[0])
            j_agent = np.random.randint(0, grille.shape[1])

        placer_agent(grille, i_agent, j_agent,
                     couleur)  # Sinon si la case est vide alors appelle de la f* placer 1 agent pour placer l'agent.


"""# **IV-Tracer la grille**"""


def create_frame(grille, figsize=(8, 8), plot_it=False, title=None, display_ticks=True, save_it=False, namefile=None,
                 dirpath=None):
    global count_images_saved
    # creation d'une map colorée avec des valeurs discrètes
    cmap = colors.ListedColormap(['white', 'blue', "red"])
    # print(cmap.N)
    bounds = [-1.5, 0, 1.5, 3]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    fig, ax = plt.subplots(figsize=figsize)

    if title:
        plt.title(title, fontsize=20)
    ax.imshow(grille, cmap=cmap, norm=norm)

    # définitions des axes (x,y)
    if display_ticks:
        ax.set_xticks(np.arange(0, grille.shape[0], 1))
        ax.set_yticks(np.arange(0, grille.shape[1], 1))
    else:
        ax.set_xticks([])
        ax.set_yticks([])

    # Pour ajouter une grille
    # ax.grid(axis='both', linestyle='-', color='k', linewidth=2)
    if plot_it:
        plt.show()

    file_path = None
    if save_it:
        if not namefile.endswith(".png"):
            raise ValueError(f" {namefile} : Nom de fichier incorrecte")

        file_path = os.path.join(dirpath, namefile)
        fig.savefig(file_path)
        fig.clf()
        with lock:
            count_images_saved += 1

    plt.close(fig)
    count_images_saved += 1

    return file_path if save_it and file_path else None


"""# **V-Conditions relative au plaçement des agents**"""


# Fonction qui permet de trouver une case vide aléatoirement
def case_vacante(grille):
    indices = np.argwhere(grille == -1)
    random_index = random.choice(indices)
    k, l = tuple(random_index)
    """
    k = np.random.randint(0, grille.shape[0])  # (k,l) : Valeurs random des coords d'une case vide
    l = np.random.randint(0, grille.shape[1])
    while grille[k][l] != -1:
        k = np.random.randint(0, grille.shape[0])
        l = np.random.randint(0, grille.shape[1])
    """
    return k, l


# Fonction qui permet de trouver une case avec un agent bleu ou rouge aléatoirement
def trouver_agent_alea(grille):
    i_agent = np.random.randint(0, grille.shape[0])  # (i_agent,j_agent) : Valeurs random des coords d'une case vide
    j_agent = np.random.randint(0, grille.shape[1])
    while grille[i_agent][j_agent] == -1:
        i_agent = np.random.randint(0, grille.shape[0])
        j_agent = np.random.randint(0, grille.shape[1])
    return i_agent, j_agent


# Fonction qui compte le nombre de voisins identiques et total
def compter_nb_voisins(grille, i_agent, j_agent):
    couleur_agent_X = grille[i_agent][j_agent]  # Couleur agent correspondant aux coords (i_agent, j_agent)
    Nt = 0  # nb voisin total
    Ns = 0  # nb voisin identique

    # haut
    if i_agent - 1 > 0:  # condition limite du haut de la grille
        voisin = grille[i_agent - 1][j_agent]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # bas
    if i_agent + 1 < grille.shape[0]:  # condition limite du bas de la grille
        voisin = grille[i_agent + 1][j_agent]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1

    # Les diagonales
    # droite 
    if j_agent + 1 < grille.shape[1]:  # condition limite du bord droit de la grille
        voisin = grille[i_agent][j_agent + 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # gauche
    if j_agent - 1 > 0:  # condition limite du bord gauche de la grille
        voisin = grille[i_agent][j_agent - 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # no
    if i_agent - 1 > 0 and j_agent - 1 > 0:  # À partir de là, "les conditions limite des diagonales de la grille"
        voisin = grille[i_agent - 1][j_agent - 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # ne 
    if i_agent - 1 > 0 and j_agent + 1 < grille.shape[1]:
        voisin = grille[i_agent - 1][j_agent + 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # so 
    if i_agent + 1 < grille.shape[0] and j_agent - 1 > 0:
        voisin = grille[i_agent + 1][j_agent - 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1
    # se
    if i_agent + 1 < grille.shape[0] and j_agent + 1 < grille.shape[1]:
        voisin = grille[i_agent + 1][j_agent + 1]
        if voisin != -1:
            Nt += 1

        if couleur_agent_X == 1:
            if voisin == 1:
                Ns += 1
        elif couleur_agent_X == 2:
            if voisin == 2:
                Ns += 1

    return Ns, Nt


"""# **VI-Définition de l'utilité et condition de satisafaction des agents**"""


def utility(grille, i_agent, j_agent, T):
    Ns, Nt = compter_nb_voisins(grille, i_agent, j_agent)  # On compte son nombre de voisins (semblable, total)
    Nd = Nt - Ns  # Nombre agent différent

    if (Nd <= T * Nt):  # Si la condition de satisfaction est respectée, utilité C=1.
        return 1
    else:  # Sinon utilité C=0.
        return 0


def scan_agents(grille, T):
    for i in range(grille.shape[0]):  # On parcourt la grille et on scan (pointe) un agent
        for j in range(grille.shape[1]):
            # print(i,j)
            if (grille[i][j] != -1):
                utility(grille, i, j, T)  # On vérifie la condition de satisfaction
                if utility(grille, i, j, T) == 0:  # Si la condition n'est pas satisfaite alors
                    k, l = case_vacante(grille)  # On choisit une case vacante aléatoirement
                    grille[k][l] = grille[i][j]  # On pose l'agent sur la case vacante
                    grille[i][j] = -1  # Puis on libère la place à l'endroit où était initialement l'agent.


def verif_satisfaction_all(grille, nb_agents_total, T):
    cpt = 0
    for i in range(grille.shape[0]):
        for j in range(grille.shape[1]):
            if (grille[i][j] != -1):
                if (utility(grille, i, j, T) == 1):
                    cpt += 1
    # print("verif: ",cpt,nb_agents_total)
    if (cpt == nb_agents_total):
        return True, cpt
    else:
        return False, cpt


def plot_history_satisfaction(history, bleus, rouges, cv, T,plot_it=True, save_it=True, namefile=None, dirpath=None):
    nb_agents_total = bleus + rouges
    pourcentages = np.array(
        history) / nb_agents_total * 100  # calcule du pourcentage d'agents satisfaits à chaque pas de temps en divisant le nombre d'agents satisfaits
    # par le nombre total d'agents et en multipliant par 100
    ici = np.where(pourcentages >= 100, pourcentages, 0)

    fig = plt.figure(figsize=(14, 6))  # Creation d'une figure de taille 14x6
    ax = fig.add_subplot(1, 1, 1)  # Ajout des axes
    plt.title(
        f"Pourcentage d'agents satisfaits (avec T={T}), {bleus + rouges} agents (b={bleus}, r={rouges}) et {cv} cases vides")  # Titre

    ax.set_yticks(np.arange(0, 101, 10 if pourcentages.max() > 20 else 1),
                  minor=True)  # Definit les graduations des ordonnées dans un intervalle entre 0 et 100 avec un pas de 10.
    ax.grid(which='minor', alpha=0.4)
    ax.grid(which='major', alpha=0.6)

    # Tracer des points représentant le pourcentage d'agents satisfaits qui sont supérieurs ou égaux à 99 % (point rouge) et égaux à 100 % (point noir).

    ax.plot(pourcentages, linewidth=5.0, c="purple", label='% satisfaction')
    p = 99
    ax.scatter([i for i in range(len(pourcentages)) if 100 > pourcentages[i] >= p],
               [pourcentages[i] for i in range(len(pourcentages)) if 100 > pourcentages[i] >= p], s=45, marker="H",
               c="red", label='% > 99.0')
    ax.scatter([i for i in range(len(pourcentages)) if pourcentages[i] == 100],
               [pourcentages[i] for i in range(len(pourcentages)) if pourcentages[i] == 100], s=60, marker="H",
               c="black", label='% == 100.0')

    # Affichage du tracer et enregistrement sous la forme d'un fichier
    ax.legend()

    if plot_it:
        plt.show()
    if save_it and namefile:
        if not namefile.endswith(".png"):
            raise ValueError(f" {namefile} : Nom de fichier incorrecte")
        output_path = os.path.join(dirpath, namefile)
        fig.savefig(output_path)
        #print(f"> {output_path} saved")


def launch_segregation_game(shape_grille=(10, 10), nb_agents_bleu=40, nb_agents_rouge=40, T=3 / 8, ITER_MAX=10000,
                            verbose=True):
    # Vérification des paramètres
    nb_agents_total = nb_agents_bleu + nb_agents_rouge
    grille_capacity = shape_grille[0] * shape_grille[1]
    if nb_agents_total >= grille_capacity:
        raise ValueError("Le nombre d'agents est supérieur à la capacité de la grille")

    cases_vides = grille_capacity - nb_agents_total

    # Initialisation de la grille initial
    grille = init_grille_2D(*shape_grille)
    placer_N_agents(grille, nb_agents_bleu, "b")  # placer agent bleu
    placer_N_agents(grille, nb_agents_rouge, "r")  # placer agent rouge
    history_grille = [grille.copy()]
    iter = 0

    # Tracer de la grille finale (avec condition de satisfaction appliquée)
    ok, cpt_satisfaction = verif_satisfaction_all(grille, nb_agents_total, T)
    history_cpt_satisfaction = [cpt_satisfaction]

    while not ok and iter < ITER_MAX:
        scan_agents(grille, T)  # mouvements
        ok, cpt_satisfaction = verif_satisfaction_all(grille, nb_agents_total, T)
        # save historique
        history_grille.append(grille.copy())
        history_cpt_satisfaction.append(cpt_satisfaction)
        iter += 1
        if verbose and iter in [1, 10, 100, 500, 1000, 5000]:
            print(f"i={iter} : {cpt_satisfaction / nb_agents_total :.1%} agents satisfaits")
    # Fin de la boucle

    return history_grille, history_cpt_satisfaction, iter, nb_agents_bleu, nb_agents_rouge, cases_vides


def get_all_frames_from(folder):  # using glob
    return sorted(glob.glob(folder + "/i_*.png"))


def generate_gif(frames_img_paths: list, gifname, dirpath, fps=5,reduce_frames_by=1):
    if not gifname.endswith(".gif"):
        raise ValueError(f" {gifname} : Nom de fichier incorrecte")

    #todo : reduce frames by
    # select frames only each reduce_frames_by
    frames_img_paths = frames_img_paths[::reduce_frames_by]

    images = []
    for filename in frames_img_paths:
        images.append(imageio.v2.imread(filename))

    gif_output_path = f"{dirpath}/{gifname}"
    imageio.mimsave(gif_output_path, images, fps=fps)
    return gif_output_path


def generate_png_file(grille, cpt_satisfaction, i, iters_done, nb_agents_total, dirpath):
    pourcentage_satisfaction = (cpt_satisfaction / (nb_agents_total)) * 100

    # add zeros to the left of the number
    namefile = f"i_{str(i).zfill(len(str(iters_done)))}.png"
    create_frame(grille, title=f"iteration {i} : {pourcentage_satisfaction : .2f} % satisfaction",
                 namefile=namefile, dirpath=dirpath, save_it=True, plot_it=False, display_ticks=False)
    # if i % 100 == 0 or i in [0, 10, 50]:
    #    print(f"> {namefile} saved.")

# display loading bar
def display_loading_bar(iter, iter_max, bar_length=20,the_end=False):
    percent = float(iter) / iter_max
    arrow = '=' * int(round(percent * bar_length) - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))

    print('> [{}] {}%'.format(arrow + spaces, int(round(percent * 100))), end='\r' if not the_end else '\n')

def main():
    global count_images_saved
    print(">>> Start...")

    history_grille, history_cpt_satisfaction, final_iter, nb_agents_bleu, nb_agents_rouge, cases_vides = launch_segregation_game(
        shape_grille=SHAPE_GRILLE,
        nb_agents_bleu=N_BLEU,
        nb_agents_rouge=N_ROUGE, T=T,
        ITER_MAX=ITER_MAX)

    print(f"> Iterations : {final_iter}")
    # Affiches des grilles aux itérations spécifiés
    primary_params_str = f"({SHAPE_GRILLE[0]}x{SHAPE_GRILLE[1]}), CV={cases_vides} (b={N_BLEU}, r={N_ROUGE}), T={T:.2f}"
    start_dirname = f"{primary_params_str} {datetime.now().strftime('%d-%m-%Y %H%M')}"

    # Création du dossier de sauvegarde

    frames_dirpath = create_folder(create_folder("backups", create_folder("frames")), start_dirname)
    print(f"> dir: {frames_dirpath}")

    # Sauvegarde des grilles sous forme d'images

    """n_workers = 8

    args = ((history_grille[i], history_cpt_satisfaction[i], i, final_iter,
             nb_agents_bleu + nb_agents_rouge, frames_dirpath) for i in range(len(history_grille)))
    with ThreadPoolExecutor(max_workers=min(n_workers, final_iter)) as executor:
        results = executor.map(lambda p: generate_png_file(*p), args)"""

    len_history_grille = len(history_grille)
    for i in range(len_history_grille):
        generate_png_file(history_grille[i], history_cpt_satisfaction[i], i, final_iter,
                          nb_agents_bleu + nb_agents_rouge, frames_dirpath)
        # display loading
        if i % 100 == 0 or i in [0, 10, 50]:
            display_loading_bar(i, len_history_grille)




    # plot satisfaction
    plot_history_satisfaction(history_cpt_satisfaction, nb_agents_bleu, nb_agents_rouge, cases_vides, T=T,
                              save_it=True, namefile=f"satisfaction_curve.png", dirpath=frames_dirpath)
    display_loading_bar(i + 1, len_history_grille, the_end=True)

    frames_path = get_all_frames_from(frames_dirpath)
    if not len(frames_path) > 0:
        raise ValueError(f"Pas de frames trouvées dans le dossier {frames_dirpath}")

    # Création du gif !
    fps = len(history_grille) // 10
    many = fps * 3

    first_image = frames_path[0]
    last_image = frames_path[-1]

    frames_path = [first_image] * many + frames_path  # add at the beginning the first
    frames_path = frames_path + [last_image] * many  # add at the end the last
    gifs_dirpath = create_folder("backups", create_folder("gifs"))

    gif_output_path = generate_gif(frames_path, f"{start_dirname} i={final_iter}_{ITER_MAX}.gif", gifs_dirpath, fps=fps)
    print(f"~~> {gif_output_path} saved")
    print(">>> End.")


if __name__ == '__main__':
    main()
