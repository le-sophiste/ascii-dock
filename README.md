# ASCII Dock

Une petite appli graphique (Python + tkinter) pour Linux qui détecte tout
seule quels jouets ASCII sont installés sur ta machine (`sl`, `cbonsai`,
`oneko`, `asciiquarium`, `nyancat`, `gti`, `cmatrix`, `cava`, `lavat`,
`cowsay`, `lolcat`, `figlet`, `toilet`, `pipes.sh`, `hollywood`, `tty-clock`,
`genact`…) ainsi que tes propres scripts, affiche à quoi sert chacun, liste
leurs flags, construit la commande à copier-coller et la lance dans un
terminal en un clic. Prévue pour être épinglée dans le dock.

Testée sous Arch / CachyOS avec fish.

## Installer

```bash
git clone https://github.com/TON-PSEUDO/ascii-dock.git
cd ascii-dock
bash install.sh
```

(remplace `TON-PSEUDO` par ton nom d'utilisateur GitHub)

Nécessite Python 3 avec tkinter (`sudo pacman -S tk` sous Arch).

Ça copie l'appli dans `~/.local/share/ascii-dock/` et l'enregistre comme
application de bureau (`~/.local/share/applications/ascii-dock.desktop`).

## Ajouter au dock

1. Ouvre ton menu d'applications et cherche **ASCII Dock**.
2. Clic droit dessus → *Ajouter aux favoris* / *Épingler au dock* / *Épingler
   à la barre des tâches* (le libellé exact dépend de ton environnement :
   GNOME, KDE Plasma, XFCE, Hyprland avec un dock comme nwg-dock ou Waybar…).
3. Lance-la une première fois pour qu'elle apparaisse dans le dock si ton
   environnement épingle automatiquement les apps en cours d'exécution.

## Fonctionnement

- Au démarrage (et à chaque clic sur **Actualiser**), l'appli parcourt le
  `PATH` avec `shutil.which()` pour voir quels programmes de sa liste sont
  installés. Rien à configurer : si tu installes un nouveau jouet ASCII
  (`sudo pacman -S ...` ou `yay -S ...`) puis cliques sur Actualiser, il
  apparaît automatiquement dans la liste.
- Chaque ligne affiche le nom, une courte description, et un bouton
  **Lancer** qui ouvre le programme dans un terminal (l'appli détecte
  automatiquement kitty, alacritty, wezterm, foot, gnome-terminal, konsole,
  xfce4-terminal, terminator, tilix ou xterm — ou utilise `$TERMINAL` si tu
  l'as défini).

## Flags cliquables + commande à copier

Sous chaque commande, une petite flèche **▶ flags (N)** déplie la liste de
tous ses flags avec leur description :

- **Coche** un flag pour l'ajouter. Si le flag prend une valeur (ex. `-C red`,
  `-m "Bon dimanche"`), une case de saisie apparaît, déjà remplie avec un
  exemple que tu peux modifier.
- Le champ **flags:** en haut de la ligne sert pour tout le reste (texte à
  afficher, flags que la liste ne connaît pas, `-c 1 -c 2`…).
- La ligne verte **« Commande à copier-coller »** montre la commande complète
  qui sera lancée. Le bouton **Copier** la met dans le presse-papiers : tu la
  colles ensuite dans ton terminal.
- **Lancer** exécute exactement cette commande dans un terminal.

Pour les commandes qui ne sont pas dans le catalogue (comme tes scripts
`lavat`, `tacos`…), clique sur **Détecter les flags de ma version** : l'appli
lance `commande --help`, `commande -help` puis `commande -h` (3 secondes max
chacune), fusionne tout ce qui ressemble à des flags (listes d'options et
lignes « usage » entre crochets) et les ajoute à la liste. N'utilise ce bouton que pour des commandes dont tu
sais que `--help` est inoffensif.

Pour `gti`, la vitesse se règle avec la variable `GTI_SPEED` (case
« GTI_SPEED= »), et les arguments git se tapent dans le champ **flags:**
(ex. `status`).

## Taille du terminal

Le menu **Terminal :** en haut à droite choisit la taille de la fenêtre
lancée : **Normal**, **Grand** (calculé d'après ton écran, défaut) ou
**Plein écran**. Le terminal reste ouvert après la fin de la commande
(appuie sur Entrée pour le fermer). Si ton terminal refuse l'option de
taille, l'appli relance automatiquement en taille normale.

## Comment les commandes sont détectées

L'appli combine trois sources :

1. **Le catalogue intégré** (~17 programmes connus : `sl`, `cbonsai`,
   `oneko`, `cava`, `lavat`, etc.) — détecté si le binaire existe dans le `PATH`.
2. **Tes commandes perso ajoutées via le formulaire** (flèche ▶ en bas),
   sauvegardées dans `custom.json`.
3. **Tes scripts perso détectés automatiquement** : l'appli regarde tous
   les dossiers de ton `$PATH` qui se trouvent **sous ton dossier
   personnel** (typiquement `~/.local/bin` ou `~/bin` — c'est là que
   vivent presque toujours les scripts qu'on écrit soi-même, contrairement
   aux paquets système installés dans `/usr/bin`), et liste tout ce qui
   est exécutable dedans, sans rien à faire de ton côté.

Si un de tes scripts (comme `tacos`) n'apparaît toujours pas :
- Vérifie où il se trouve avec `which tacos`.
- S'il n'est pas dans un dossier sous ton `$HOME` qui fait partie du
  `$PATH` (regarde avec `echo $PATH`), déplace-le dans `~/.local/bin`
  (crée-le si besoin et ajoute-le à ton `$PATH` dans ta config fish), ou
  ajoute-le simplement à la main via le formulaire ci-dessous.

## Ajouter tes propres commandes

En bas de la fenêtre, clique sur la flèche **▶ Ajouter une commande perso**
pour déplier un petit formulaire : nom affiché, commande à exécuter (ex.
`cmatrix -b`, ou même un pipe comme `fortune | lolcat`), et une description.
Clique sur **＋ Ajouter** : la commande apparaît dans une section « Mes
commandes perso » avec un bouton **Lancer** et un **✕** pour la retirer.

Ces commandes sont sauvegardées dans
`~/.local/share/ascii-dock/custom.json` et restent disponibles au prochain
lancement de l'appli.

## Ajouter des détections automatiques au catalogue intégré

Pour qu'un programme apparaisse automatiquement (sans avoir à le retaper
dans le formulaire à chaque appli), ouvre
`~/.local/share/ascii-dock/ascii_dock.py` et ajoute une ligne dans la liste
`CATALOG`, sous la forme :

```python
("nom-affiché", ["nom-du-binaire"], "Description courte.", ["nom-du-binaire", "--option"]),
```

Mets `None` à la place de la commande si le programme se lance sans argument
particulier.

## Licence

MIT — voir le fichier `LICENSE`.
