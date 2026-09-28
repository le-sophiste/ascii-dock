#!/usr/bin/env python3
"""ASCII Dock — détecte les jouets ASCII installés (catalogue connu +
scripts perso du $PATH), affiche pour chacun la liste de ses flags
(cliquables), construit la commande complète (copiable) et la lance dans
un terminal assez grand pour les animations plein écran.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

DATA_DIR = Path.home() / ".local" / "share" / "ascii-dock"
CUSTOM_FILE = DATA_DIR / "custom.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

BG, CARD, CARD2 = "#1e1e2e", "#313244", "#3b3d54"
FG, DIM, ACC, BLUE, YEL = "#cdd6f4", "#a6adc8", "#a6e3a1", "#89b4fa", "#f9e2af"

# (nom, [binaires possibles], description, commande par défaut — {bin} = binaire)
CATALOG = [
    ("sl", ["sl"], "Un train ASCII qui traverse l'écran.", "{bin}"),
    ("cbonsai", ["cbonsai"], "Fait pousser un bonsaï ASCII aléatoire.", "{bin} -l"),
    ("oneko", ["oneko"], "Un chat qui poursuit le curseur de la souris (X11).", "{bin}"),
    ("asciiquarium", ["asciiquarium"], "Un aquarium animé en ASCII.", "{bin}"),
    ("nyancat", ["nyancat"], "Le nyan cat classique, en boucle.", "{bin}"),
    ("gti", ["gti"], "Une voiture traverse le terminal, puis lance git.", "{bin} --version"),
    ("cmatrix", ["cmatrix"], "L'effet « pluie de caractères » façon Matrix.", "{bin}"),
    ("cava", ["cava"], "Visualiseur audio en barres ASCII.", "{bin}"),
    ("lavat", ["lavat"], "Une lampe à lave (metaballs) dans le terminal.", "{bin}"),
    ("pipes", ["pipes.sh", "pipes"], "Tuyaux animés façon économiseur Windows 95.", "{bin}"),
    ("cowsay", ["cowsay"], "Une vache (ou autre animal) qui dit un message.", "{bin} 'Miaou depuis le dock !'"),
    ("lolcat", ["lolcat"], "Colorise du texte en arc-en-ciel.", "echo 'Coucou en couleurs !' | {bin}"),
    ("figlet", ["figlet"], "Transforme du texte en gros caractères ASCII.", "{bin} Salut"),
    ("toilet", ["toilet"], "Comme figlet, avec des filtres de couleur.", "{bin} -F metal Salut"),
    ("hollywood", ["hollywood"], "Faux terminaux de hacker façon film.", "{bin}"),
    ("tty-clock", ["tty-clock"], "Une horloge géante en ASCII.", "{bin} -c"),
    ("genact", ["genact"], "De faux écrans de progression aléatoires.", "{bin}"),
]

# Texte ajouté quand on choisit des flags mais qu'on n'a rien tapé dans « flags »
TAIL_DEFAULT = {"cowsay": "Miaou depuis le dock !", "figlet": "Salut",
                "toilet": "Salut", "gti": "--version"}
PIPE_DEFAULT = {"lolcat": "Coucou en couleurs !"}

# Flags : (flag, description, exemple de valeur ou None, libellé affiché ou None)
FLAGS = {
    "sl": [
        ("-a", "Un accident se produit (des gens crient à l'aide)"),
        ("-c", "Locomotive C51 au lieu de D51"),
        ("-d", "Mode disco (couleurs alternées)"),
        ("-e", "Autorise l'interruption avec Ctrl+C"),
        ("-F", "Elle vole (Galaxy Express 999)"),
        ("-G", "Version « française » (façon Oscar)"),
        ("-l", "Petite version"),
        ("-w", "Jour de vent : locomotive plus rapide"),
        ("-", "Nombre de wagons (ex. 5 donne -5)", "5", "-N"),
        ("-v", "Affiche la version"),
    ],
    "cbonsai": [
        ("-l", "Pousse en direct, étape par étape (--live)"),
        ("-i", "Mode infini : enchaîne les arbres (--infinite)"),
        ("-S", "Économiseur d'écran (= -li, quitte sur une touche)"),
        ("-p", "Affiche l'arbre final sans animation (--print)"),
        ("-t", "Pause entre étapes en mode -l, en secondes", "0.03"),
        ("-w", "Attente entre 2 arbres en mode -i, en secondes", "4.0"),
        ("-m", "Message affiché à côté de l'arbre", "Bon dimanche"),
        ("-b", "Socle ASCII (0 = aucun)", "1"),
        ("-c", "Feuilles perso, séparées par des virgules", "&,*"),
        ("-k", "4 couleurs 0-255 : feuilles sombres, bois sombre, feuilles claires, bois clair", "2,3,10,11"),
        ("-M", "Multiplicateur de branches, 0-20 (défaut 5)", "5"),
        ("-L", "Vie de l'arbre, 0-200 (défaut 32)", "32"),
        ("-s", "Graine aléatoire (arbre reproductible)", "42"),
        ("-W", "Sauvegarde la progression dans un fichier", "~/.cache/cbonsai"),
        ("-C", "Charge la progression depuis un fichier", "~/.cache/cbonsai"),
        ("-v", "Mode verbeux"),
    ],
    "oneko": [
        ("-dog", "Un chien au lieu du chat"),
        ("-tora", "Chat tigré"),
        ("-sakura", "Sakura Kinomoto au lieu du chat"),
        ("-tomoyo", "Tomoyo Daidouji au lieu du chat"),
        ("-bsd", "Démon BSD au lieu du chat"),
        ("-time", "Intervalle d'animation en µs (défaut 125000, plus petit = plus rapide)", "125000"),
        ("-speed", "Distance par bond en pixels (défaut 16)", "16"),
        ("-idle", "Seuil de vitesse de la souris qui réveille le chat", "6"),
        ("-name", "Nom de la fenêtre du chat", "neko"),
        ("-towindow", "Poursuit une fenêtre que tu cliques ensuite"),
        ("-toname", "Poursuit la fenêtre portant ce nom", "xterm"),
        ("-tofocus", "Court vers la fenêtre active"),
        ("-position", "Décalage X/Y en pixels", "+0+0"),
        ("-rv", "Vidéo inversée"),
        ("-noshape", "Désactive l'extension Shape"),
        ("-fg", "Couleur du premier plan", "black"),
        ("-bg", "Couleur du fond", "white"),
        ("-help", "Affiche l'aide"),
    ],
    "asciiquarium": [
        ("-c", "Mode « classic » : espèces de la v1.0 uniquement"),
    ],
    "nyancat": [
        ("-i", "Affiche l'intro au démarrage"),
        ("-I", "Saute l'intro en mode telnet"),
        ("-t", "Mode telnet"),
        ("-n", "Cache le compteur de temps"),
        ("-s", "Ne change pas le titre de la fenêtre"),
        ("-e", "N'efface pas l'écran entre les images"),
        ("-d", "Délai entre images, 10 à 1000 ms (selon la version)", "90"),
        ("-f", "Affiche N images puis quitte", "200"),
        ("-r", "Rogne depuis le haut (lignes)", "0"),
        ("-R", "Rogne depuis le bas (lignes)", "20"),
        ("-c", "Rogne depuis la gauche (colonnes)", "0"),
        ("-C", "Rogne depuis la droite (colonnes)", "60"),
        ("-W", "Rogne à cette largeur", "40"),
        ("-H", "Rogne à cette hauteur", "20"),
        ("-h", "Affiche l'aide"),
    ],
    "gti": [
        ("GTI_SPEED=", "Vitesse de l'animation (défaut 1000, plus grand = plus lent)", "1000"),
        ("GIT=", "Binaire git lancé après l'animation", "/usr/bin/git"),
    ],
    "cmatrix": [
        ("-a", "Défilement asynchrone"),
        ("-b", "Caractères en gras aléatoires"),
        ("-B", "Tout en gras (prioritaire sur -b)"),
        ("-n", "Pas de gras du tout"),
        ("-f", "Force le type de terminal linux"),
        ("-l", "Mode console Linux (police matrix.fnt)"),
        ("-o", "Ancien style de défilement"),
        ("-s", "Économiseur d'écran : quitte à la 1re touche"),
        ("-m", "Mode « lambda » : tout devient λ"),
        ("-x", "Mode fenêtre X (xterm avec mtx.pcf)"),
        ("-u", "Délai de rafraîchissement 0-9 (défaut 4)", "4"),
        ("-C", "Couleur : green, red, blue, white, yellow, cyan, magenta, black", "red"),
        ("-V", "Affiche la version"),
        ("-h", "Affiche l'aide"),
    ],
    "cava": [
        ("-p", "Fichier de configuration alternatif", "~/.config/cava/config"),
        ("-v", "Affiche la version"),
        ("-h", "Affiche l'aide"),
    ],
    "lavat": [
        ("-c", "Couleur des metaballs (red, blue, yellow, green, cyan, magenta, white, black)", "red"),
        ("-k", "Couleur du contour (rim) — à utiliser avec -R", "cyan"),
        ("-R", "Épaisseur du contour, 1 à 5", "1"),
        ("-s", "Vitesse, 1 à 10 (défaut 5)", "5"),
        ("-r", "Rayon des metaballs, 1 à 10 (défaut 5)", "5"),
        ("-b", "Nombre de metaballs, 5 à 20 (défaut 10)", "10"),
        ("-F", "Caractères perso (ASCII seulement)", ".:-=+*#%@"),
        ("-C", "Garde toute la lave dans le terminal"),
        ("-p", "Mode fête : p1, p2 ou p3", "p3"),
        ("-g", "Dégradé en vraies couleurs (versions récentes)"),
        ("-G", "Gravité : les boules chauffent, montent, refroidissent (versions récentes)"),
        ("-h", "Affiche l'aide"),
    ],
    "pipes": [
        ("-p", "Nombre de tuyaux (défaut 1)", "3"),
        ("-t", "Type de tuyaux 0 à 9 (défaut 0), ou c + 16 caractères", "3"),
        ("-c", "Couleur 0-7 (pour plusieurs, ajoute d'autres -c dans « flags »)", "1"),
        ("-f", "Vitesse 20-100 (défaut 75)", "75"),
        ("-s", "Probabilité de ligne droite 5-15 (défaut 13)", "13"),
        ("-r", "Réinitialise après N caractères (défaut 2000)", "2000"),
        ("-R", "Position/direction de départ aléatoires"),
        ("-B", "Pas de gras"),
        ("-C", "Pas de couleur"),
        ("-K", "Ne change pas couleur/type sur les bords"),
        ("-h", "Affiche l'aide"),
        ("-v", "Affiche la version"),
    ],
    "cowsay": [
        ("-b", "Mode Borg"),
        ("-d", "Vache morte"),
        ("-g", "Mode cupide"),
        ("-p", "Paranoïaque"),
        ("-s", "Défoncée"),
        ("-t", "Fatiguée"),
        ("-w", "Survoltée"),
        ("-y", "Jeune"),
        ("-e", "Yeux perso (2 caractères)", "^^"),
        ("-T", "Langue perso (2 caractères)", "U "),
        ("-f", "Autre dessin que la vache (liste : -l)", "dragon"),
        ("-W", "Largeur de retour à la ligne (défaut 40)", "40"),
        ("-n", "Pas de retour à la ligne auto (texte via pipe)"),
        ("-l", "Liste les dessins disponibles"),
        ("-h", "Affiche l'aide"),
    ],
    "lolcat": [
        ("-p", "Inclinaison de l'arc-en-ciel (défaut 3.0)", "3.0"),
        ("-F", "Fréquence des couleurs (défaut 0.1)", "0.1"),
        ("-S", "Graine aléatoire (0 = auto)", "0"),
        ("-a", "Animation ligne par ligne"),
        ("-d", "Durée de l'animation en étapes (défaut 12)", "12"),
        ("-s", "Vitesse de l'animation (défaut 20)", "20"),
        ("-i", "Inverse fond et texte"),
        ("-t", "Vraies couleurs 24 bits"),
        ("-f", "Force la couleur même hors terminal"),
        ("-v", "Affiche la version"),
        ("-h", "Affiche l'aide"),
    ],
    "figlet": [
        ("-f", "Police", "slant"),
        ("-c", "Centré"),
        ("-l", "Aligné à gauche"),
        ("-r", "Aligné à droite"),
        ("-x", "Alignement par défaut"),
        ("-t", "Largeur = celle du terminal"),
        ("-w", "Largeur de sortie (défaut 80)", "120"),
        ("-p", "Mode paragraphe"),
        ("-n", "Retours à la ligne normaux (défaut)"),
        ("-k", "Kerning"),
        ("-s", "Smushing (défaut)"),
        ("-S", "Smushing forcé"),
        ("-o", "Chevauchement"),
        ("-W", "Pleine largeur"),
        ("-v", "Affiche la version"),
    ],
    "toilet": [
        ("-f", "Police", "mono12"),
        ("-F", "Filtres séparés par « : » (liste : -F list)", "crop:rotate"),
        ("--gay", "Filtre arc-en-ciel"),
        ("--metal", "Filtre métal"),
        ("-w", "Largeur de sortie (défaut 80)", "100"),
        ("-t", "Largeur = celle du terminal"),
        ("-s", "Composition par défaut"),
        ("-S", "Smushing"),
        ("-k", "Kerning"),
        ("-W", "Pleine largeur"),
        ("-o", "Chevauchement"),
        ("-E", "Format d'export (html, irc…)", "html"),
        ("-d", "Dossier des polices", "/usr/share/figlet"),
        ("-h", "Affiche l'aide"),
        ("-v", "Affiche la version"),
    ],
    "hollywood": [
        ("-s", "Nombre de zones (splits)", "6"),
        ("-q", "Sans le thème musical"),
        ("-h", "Affiche l'aide"),
    ],
    "tty-clock": [
        ("-s", "Affiche les secondes"),
        ("-S", "Économiseur d'écran (quitte sur une touche)"),
        ("-x", "Boîte autour de l'horloge"),
        ("-c", "Horloge centrée"),
        ("-C", "Couleur 0-7", "3"),
        ("-b", "Couleurs en gras"),
        ("-t", "Format 12 h"),
        ("-u", "Heure UTC"),
        ("-r", "Rebondit sur les bords"),
        ("-D", "Cache la date"),
        ("-B", "Deux-points clignotants"),
        ("-n", "Ne quitte pas sur une touche"),
        ("-f", "Format de date (strftime)", "%d/%m/%Y"),
        ("-d", "Délai entre rafraîchissements, en secondes (défaut 1)", "1"),
        ("-a", "Délai supplémentaire en nanosecondes", "0"),
        ("-T", "Affiche sur un tty donné", "/dev/pts/1"),
        ("-i", "Infos sur tty-clock"),
        ("-v", "Affiche la version"),
        ("-h", "Affiche l'aide"),
    ],
    "genact": [
        ("-l", "Liste les modules"),
        ("-m", "Modules à jouer, séparés par des virgules", "bootlog,cargo"),
        ("-s", "Facteur de vitesse (défaut 1)", "2"),
        ("-i", "Affiche instantanément les N premières lignes", "5"),
        ("--exit-after-time", "Quitte après une durée", "30s"),
        ("--exit-after-modules", "Quitte après N modules", "3"),
        ("-h", "Affiche l'aide"),
        ("-V", "Affiche la version"),
    ],
}

# Terminaux : préfixe d'exécution, flags de taille, flags plein écran, style d'argument
TERMINALS = [
    {"name": "kitty", "exec": [], "style": "args",
     "size": lambda c, r: ["-o", f"initial_window_width={c}c", "-o", f"initial_window_height={r}c"],
     "full": ["--start-as=fullscreen"]},
    {"name": "alacritty", "exec": ["-e"], "style": "args",
     "size": lambda c, r: ["-o", f"window.dimensions.columns={c}", "-o", f"window.dimensions.lines={r}"],
     "full": ["-o", 'window.startup_mode="Fullscreen"']},
    {"name": "wezterm", "exec": ["start", "--"], "style": "args",
     "size": lambda c, r: ["--config", f"initial_cols={c}", "--config", f"initial_rows={r}"],
     "full": []},
    {"name": "foot", "exec": [], "style": "args",
     "size": lambda c, r: ["-W", f"{c}x{r}"], "full": ["-F"]},
    {"name": "gnome-terminal", "exec": ["--"], "style": "args",
     "size": lambda c, r: [f"--geometry={c}x{r}"], "full": ["--full-screen"]},
    {"name": "konsole", "exec": ["-e"], "style": "args",
     "size": lambda c, r: ["-p", f"TerminalColumns={c}", "-p", f"TerminalRows={r}"],
     "full": ["--fullscreen"]},
    {"name": "xfce4-terminal", "exec": ["-x"], "style": "args",
     "size": lambda c, r: [f"--geometry={c}x{r}"], "full": ["--fullscreen"]},
    {"name": "terminator", "exec": ["-x"], "style": "args",
     "size": lambda c, r: [f"--geometry={c}x{r}"], "full": ["-f"]},
    {"name": "tilix", "exec": ["-e"], "style": "string",
     "size": lambda c, r: [f"--geometry={c}x{r}"], "full": ["--full-screen"]},
    {"name": "xterm", "exec": ["-e"], "style": "args",
     "size": lambda c, r: ["-geometry", f"{c}x{r}"], "full": ["-fullscreen"]},
]
SIZE_MODES = ["Normal", "Grand", "Plein écran"]


# ───────────────────────── utilitaires ─────────────────────────

def q(token):
    """Quote shell, en gardant le ~ développable."""
    if token == "~":
        return token
    if token.startswith("~/"):
        rest = token[2:]
        return "~/" + shlex.quote(rest) if rest else "~/"
    return shlex.quote(token)


def term_spec(name):
    base = os.path.basename(name)
    for spec in TERMINALS:
        if spec["name"] == base:
            return spec
    return {"name": base, "exec": ["-e"], "style": "args", "size": None, "full": []}


def find_terminal():
    env_term = os.environ.get("TERMINAL")
    if env_term and shutil.which(env_term):
        return env_term, term_spec(env_term)
    for spec in TERMINALS:
        if shutil.which(spec["name"]):
            return spec["name"], spec
    return None, None


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def personal_script_dirs():
    """Dossiers du $PATH situés sous $HOME (là où vivent tes propres scripts)."""
    home = os.path.realpath(str(Path.home()))
    dirs = []
    for p in os.environ.get("PATH", "").split(os.pathsep):
        if not p:
            continue
        real = os.path.realpath(p)
        if real.startswith(home) and os.path.isdir(real) and real not in dirs:
            dirs.append(real)
    return dirs


def find_personal_scripts(known_bins):
    found = {}
    for d in personal_script_dirs():
        try:
            for entry in os.scandir(d):
                if entry.name in known_bins or entry.name in found:
                    continue
                if entry.is_file(follow_symlinks=True) and os.access(entry.path, os.X_OK):
                    found[entry.name] = entry.path
        except (FileNotFoundError, PermissionError):
            continue
    return found


def copy_text(root, text):
    """Copie dans le presse-papiers (et le rend persistant si possible)."""
    try:
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update_idletasks()
    except tk.TclError:
        pass
    order = [("wl-copy", []), ("xclip", ["-selection", "clipboard"]),
             ("xsel", ["--clipboard", "--input"])]
    if not os.environ.get("WAYLAND_DISPLAY"):
        order = order[1:] + order[:1]
    for tool, args in order:
        if shutil.which(tool):
            try:
                p = subprocess.Popen([tool] + args, stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                p.stdin.write(text.encode("utf-8"))
                p.stdin.close()
            except OSError:
                continue
            break


# ───────────────────────── détection des flags via --help ─────────────────────────

OPT_RE = re.compile(
    r"^\s{0,12}(-{1,2}[A-Za-z0-9?][\w-]*(?:[ =,|/]+-{1,2}[A-Za-z0-9?][\w-]*)*)"
    r"(?:[ =]+(<[^>\s]+>|\[[^\]\s]+\]|[A-Z][A-Z0-9_]+)(?=\s|$))?\s*(.*)$"
)


BRACKET_RE = re.compile(
    r"\[\s*(-{1,2}[A-Za-z0-9?][\w-]*)(?:[ =]+(<[^>\]]+>|[A-Za-z_][\w.-]*))?\s*\]"
)


def parse_help(text):
    """Extrait [(flag, hint|None, description)] d'un texte d'aide.
    Comprend les listes « -x, --xxx  description » et les usages « [-x] [-y val] »."""
    found, seen = [], set()
    lines = text.splitlines()
    for line in lines:
        m = OPT_RE.match(line)
        if not m:
            continue
        flag = re.split(r"[ =,|/]+", m.group(1).strip())[0]
        if flag in seen or flag in ("-", "--"):
            continue
        seen.add(flag)
        hint = "" if m.group(2) else None
        desc = m.group(3).strip() or "(voir l'aide)"
        found.append((flag, hint, desc[:110]))
    for line in lines:
        for m in BRACKET_RE.finditer(line):
            flag = m.group(1)
            if flag in seen:
                continue
            seen.add(flag)
            found.append((flag, "" if m.group(2) else None, "(vu dans la ligne « usage »)"))
    return found[:80]


def _bytes(x):
    if x is None:
        return b""
    return x if isinstance(x, bytes) else x.encode("utf-8", "replace")


def run_capture(cmd):
    env = dict(os.environ, TERM="dumb")
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=3,
                           stdin=subprocess.DEVNULL, env=env)
        out = _bytes(p.stdout) + b"\n" + _bytes(p.stderr)
    except subprocess.TimeoutExpired as e:
        out = _bytes(e.stdout) + b"\n" + _bytes(e.stderr)
    except OSError:
        return ""
    return out.decode("utf-8", "replace")


HELP_OPTS = ("--help", "-help", "-h")


def discover_flags(argv):
    """Lance la commande avec --help, -help puis -h et fusionne tous les flags trouvés."""
    merged, seen = [], set()
    for opt in HELP_OPTS:
        for item in parse_help(run_capture(list(argv) + [opt])):
            if item[0] not in seen:
                seen.add(item[0])
                merged.append(item)
    return merged[:80]


# ───────────────────────── modèle d'un flag ─────────────────────────

class Flag:
    ENV_RE = re.compile(r"^[A-Z][A-Z0-9_]*=$")

    def __init__(self, flag, desc, hint=None, label=None, detected=False):
        self.flag, self.desc, self.hint = flag, desc, hint
        self.label = label or flag
        self.detected = detected
        self.is_env = bool(self.ENV_RE.match(flag))
        self.joined = self.is_env or flag == "-"


# ───────────────────────── une carte = une commande ─────────────────────────

class Card:
    def __init__(self, app, parent, name, desc, base_str, build_prefix, flags,
                 help_argv, bg, smart=False, on_delete=None):
        self.app, self.name, self.bg = app, name, bg
        self.base_str, self.build_prefix = base_str, build_prefix
        self.flags, self.help_argv, self.smart = list(flags), help_argv, smart
        self.vars, self.vals = {}, {}
        self.det_note = ""
        self.open = False

        self.frame = tk.Frame(parent, bg=bg, padx=10, pady=8)
        self.frame.pack(fill="x", pady=4, padx=4)

        top = tk.Frame(self.frame, bg=bg)
        top.pack(fill="x")
        text = tk.Frame(top, bg=bg)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=name, font=("monospace", 12, "bold"), bg=bg, fg=FG,
                 anchor="w").pack(fill="x")
        tk.Label(text, text=desc, font=("sans-serif", 9), bg=bg, fg=DIM, anchor="w",
                 wraplength=250, justify="left").pack(fill="x")

        right = tk.Frame(top, bg=bg)
        right.pack(side="right")
        if on_delete:
            ttk.Button(right, text="✕", width=3, command=on_delete).pack(side="right", padx=(4, 0))
        ttk.Button(right, text="Lancer", command=self.launch).pack(side="right")
        self.copy_btn = ttk.Button(right, text="Copier", command=lambda: self.copy(self.copy_btn))
        self.copy_btn.pack(side="right", padx=4)
        self.free = tk.Entry(right, width=14, bg=BG, fg=FG, insertbackground=FG)
        self.free.pack(side="right", padx=(4, 0))
        self.free.bind("<KeyRelease>", lambda e: self.update_preview())
        tk.Label(right, text="flags:", bg=bg, fg="#6c7086",
                 font=("sans-serif", 8)).pack(side="right")

        self.arrow = tk.Button(
            self.frame, anchor="w", bg=bg, fg=BLUE, activebackground=bg,
            activeforeground="#b4befe", bd=0, highlightthickness=0, cursor="hand2",
            font=("sans-serif", 9), command=self.toggle)
        self.arrow.pack(fill="x", pady=(4, 0))
        self.panel = tk.Frame(self.frame, bg=bg)
        self.build_panel()
        self.refresh_arrow()

    # -- construction de la commande --
    def assemble(self):
        env, args = [], []
        for f in self.flags:
            if not self.vars[f.flag].get():
                continue
            val = self.vals[f.flag].get() if f.hint is not None else ""
            if f.is_env:
                if val:
                    env.append(f.flag + q(val))
            elif f.joined:
                args.append(q(f.flag + val))
            else:
                args.append(q(f.flag))
                if f.hint is not None and val:
                    args.append(q(val))
        raw = self.free.get()
        try:
            free_tokens = shlex.split(raw)
        except ValueError:
            free_tokens = raw.split()
        return env, args, [q(t) for t in free_tokens]

    def command_line(self):
        env, args, free = self.assemble()
        if not (env or args or free):
            return self.base_str
        tail = args + free
        if self.smart and not free and self.name in TAIL_DEFAULT:
            tail.append(q(TAIL_DEFAULT[self.name]))
        core = " ".join([self.build_prefix] + tail)
        if self.smart and self.name in PIPE_DEFAULT:
            core = f"echo {q(PIPE_DEFAULT[self.name])} | " + core
        return (" ".join(env) + " " + core) if env else core

    def update_preview(self):
        if hasattr(self, "preview"):
            self.preview.set(self.command_line())

    # -- interface --
    def refresh_arrow(self):
        n = len(self.flags)
        label = f"flags ({n})" if n else "flags (aucun connu — clique pour détecter)"
        self.arrow.config(text=("▼ " if self.open else "▶ ") + label)

    def toggle(self):
        self.open = not self.open
        if self.open:
            self.panel.pack(fill="x")
        else:
            self.panel.pack_forget()
        self.refresh_arrow()

    def build_panel(self):
        bg = self.bg
        for w in self.panel.winfo_children():
            w.destroy()
        grid = tk.Frame(self.panel, bg=bg)
        grid.pack(fill="x", pady=(4, 4))
        for i, f in enumerate(self.flags):
            var = self.vars.setdefault(f.flag, tk.BooleanVar(value=False))
            tk.Checkbutton(
                grid, text=f.label, variable=var, command=self.update_preview,
                bg=bg, fg=FG, selectcolor="#11111b", activebackground=bg, activeforeground=FG,
                anchor="w", font=("monospace", 10, "bold"), highlightthickness=0,
            ).grid(row=i, column=0, sticky="w")
            if f.hint is not None:
                sv = self.vals.setdefault(f.flag, tk.StringVar(value=f.hint))
                e = tk.Entry(grid, textvariable=sv, width=12, bg=BG, fg=FG, insertbackground=FG)
                e.grid(row=i, column=1, padx=6, sticky="w")
                e.bind("<KeyRelease>", lambda ev: self.update_preview())
            tk.Label(grid, text=f.desc + ("  (détecté)" if f.detected else ""), bg=bg, fg=DIM,
                     font=("sans-serif", 9), wraplength=300, justify="left",
                     anchor="w").grid(row=i, column=2, sticky="w")
        grid.grid_columnconfigure(2, weight=1)

        tk.Label(self.panel, text="Commande à copier-coller :", bg=bg, fg=DIM,
                 font=("sans-serif", 9), anchor="w").pack(fill="x")
        pr = tk.Frame(self.panel, bg=bg)
        pr.pack(fill="x")
        self.preview = tk.StringVar()
        tk.Entry(pr, textvariable=self.preview, state="readonly", readonlybackground="#11111b",
                 fg=ACC, font=("monospace", 10)).pack(side="left", fill="x", expand=True)
        cb = ttk.Button(pr, text="Copier", command=lambda: self.copy(cb))
        cb.pack(side="left", padx=(6, 0))
        self.det_btn = ttk.Button(self.panel, text="Détecter les flags de ma version (lance --help, -help, -h)",
                                  command=self.discover)
        self.det_btn.pack(anchor="w", pady=(6, 0))
        tk.Label(self.panel, text=self.det_note, bg=bg, fg=DIM,
                 font=("sans-serif", 8), anchor="w").pack(fill="x")
        self.update_preview()

    # -- actions --
    def copy(self, btn):
        copy_text(self.app, self.command_line())
        old = btn.cget("text")
        btn.config(text="✔ Copié")
        self.frame.after(1400, lambda: self._restore(btn, old))

    def _restore(self, btn, text):
        try:
            btn.config(text=text)
        except tk.TclError:
            pass

    def launch(self):
        self.app.launch_shell(self.command_line())

    def discover(self):
        if not self.help_argv:
            self.det_note = "Impossible de lancer cette commande pour lire son aide."
            self.build_panel()
            return
        self.det_btn.state(["disabled"])
        result = {}

        def work():
            result["flags"] = discover_flags(self.help_argv)

        t = threading.Thread(target=work, daemon=True)
        t.start()

        def poll():
            try:
                if t.is_alive():
                    self.frame.after(150, poll)
                else:
                    self.finish_discover(result.get("flags", []))
            except tk.TclError:
                pass

        self.frame.after(150, poll)

    def finish_discover(self, found):
        known = {f.flag for f in self.flags}
        new = [Flag(fl, desc, hint, detected=True) for fl, hint, desc in found if fl not in known]
        self.flags += new
        self.det_note = (f"{len(new)} flag(s) ajouté(s) depuis l'aide de ta version."
                         if new else "Rien de nouveau trouvé dans l'aide.")
        self.build_panel()
        self.refresh_arrow()


# ───────────────────────── application ─────────────────────────

class AsciiDock(tk.Tk):
    def __init__(self):
        super().__init__(className="AsciiDock")  # sert au dock pour reconnaître l'appli
        self.title("ASCII Dock")
        self.geometry("720x760")
        self.configure(bg=BG)
        self.term_name, self.term_spec = find_terminal()
        self.custom = load_json(CUSTOM_FILE, [])
        settings = load_json(SETTINGS_FILE, {})
        self.size_var = tk.StringVar(value=settings.get("size", "Grand"))
        if self.size_var.get() not in SIZE_MODES:
            self.size_var.set("Grand")
        self.form_open = False

        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=16, pady=(16, 8))
        tk.Label(header, text="ASCII Dock", font=("monospace", 18, "bold"),
                 bg=BG, fg=ACC).pack(side="left")
        ttk.Button(header, text="⟳ Actualiser", command=self.refresh).pack(side="right")
        combo = ttk.Combobox(header, textvariable=self.size_var, values=SIZE_MODES,
                             state="readonly", width=11)
        combo.pack(side="right", padx=(0, 8))
        combo.bind("<<ComboboxSelected>>", lambda e: save_json(SETTINGS_FILE, {"size": self.size_var.get()}))
        tk.Label(header, text="Terminal :", bg=BG, fg=DIM,
                 font=("sans-serif", 9)).pack(side="right", padx=(0, 4))

        self.status = tk.Label(self, text="", bg=BG, fg="#9399b2", font=("sans-serif", 9))
        self.status.pack(fill="x", padx=16)

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.list_frame = tk.Frame(self.canvas, bg=BG)
        self.win_id = self.canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.win_id, width=e.width))
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-2, "units"))
        self.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(2, "units"))
        self.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))

        self.toggle_btn = tk.Button(
            self, text="▶  Ajouter une commande perso", anchor="w", bg=BG, fg=BLUE,
            activebackground=BG, activeforeground="#b4befe", bd=0, cursor="hand2",
            font=("sans-serif", 10, "bold"), command=self.toggle_form)
        self.toggle_btn.pack(fill="x", padx=16, pady=(0, 4))
        self.form_frame = tk.Frame(self, bg=CARD, padx=12, pady=10)

        def labeled_entry(label):
            tk.Label(self.form_frame, text=label, bg=CARD, fg=FG,
                     font=("sans-serif", 9), anchor="w").pack(fill="x")
            e = tk.Entry(self.form_frame, bg=BG, fg=FG, insertbackground=FG)
            e.pack(fill="x", pady=(0, 6))
            return e

        self.entry_name = labeled_entry("Nom (affiché dans la liste)")
        self.entry_cmd = labeled_entry("Commande à exécuter (ex: cmatrix -b, ou fortune | lolcat)")
        self.entry_desc = labeled_entry("Description courte")
        ttk.Button(self.form_frame, text="＋ Ajouter", command=self.add_custom_command).pack(anchor="e")

        self.refresh()

    # -- formulaire commande perso --
    def toggle_form(self):
        self.form_open = not self.form_open
        if self.form_open:
            self.toggle_btn.config(text="▼  Ajouter une commande perso")
            self.form_frame.pack(fill="x", padx=16, pady=(0, 12))
        else:
            self.toggle_btn.config(text="▶  Ajouter une commande perso")
            self.form_frame.pack_forget()

    def add_custom_command(self):
        name, cmd = self.entry_name.get().strip(), self.entry_cmd.get().strip()
        desc = self.entry_desc.get().strip() or "Commande personnalisée."
        if not name or not cmd:
            messagebox.showwarning("ASCII Dock", "Nom et commande sont obligatoires.")
            return
        self.custom.append({"name": name, "cmd": cmd, "desc": desc})
        save_json(CUSTOM_FILE, self.custom)
        for e in (self.entry_name, self.entry_cmd, self.entry_desc):
            e.delete(0, "end")
        self.refresh()

    def remove_custom(self, idx):
        del self.custom[idx]
        save_json(CUSTOM_FILE, self.custom)
        self.refresh()

    # -- liste --
    def section(self, text):
        tk.Label(self.list_frame, text=text, bg=BG, fg=YEL, font=("sans-serif", 9, "bold"),
                 anchor="w").pack(fill="x", padx=8, pady=(10, 2))

    def refresh(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        found, known_bins = 0, set()
        for name, bins, desc, tmpl in CATALOG:
            known_bins.update(bins)
            bin_ = next((b for b in bins if shutil.which(b)), None)
            if not bin_:
                continue
            found += 1
            flags = [Flag(*t) for t in FLAGS.get(name, [])]
            Card(self, self.list_frame, name, desc, tmpl.format(bin=q(bin_)), q(bin_),
                 flags, [bin_], CARD, smart=True)

        if self.custom:
            self.section("Mes commandes perso")
            for idx, entry in enumerate(self.custom):
                try:
                    help_argv = [shlex.split(entry["cmd"])[0]]
                except (ValueError, IndexError):
                    help_argv = None
                Card(self, self.list_frame, entry["name"], entry["desc"], entry["cmd"],
                     entry["cmd"], [], help_argv, CARD2,
                     on_delete=lambda i=idx: self.remove_custom(i))

        personal = find_personal_scripts(known_bins)
        if personal:
            self.section("Scripts perso détectés automatiquement")
            for name, path in sorted(personal.items()):
                Card(self, self.list_frame, name, f"Trouvé dans {path}", q(path), q(path),
                     [], [path], CARD2)

        term = (f"Terminal : {self.term_name}" if self.term_name
                else "⚠ Aucun terminal graphique détecté")
        self.status.config(text=f"{found}/{len(CATALOG)} détectés · {len(self.custom)} perso · "
                                f"{len(personal)} scripts auto · {term}")
        if found == 0 and not self.custom and not personal:
            tk.Label(self.list_frame, bg=BG, fg="#f38ba8", justify="left", wraplength=560,
                     text="Rien n'est installé pour l'instant.\nInstalle par exemple :\n"
                          "  sudo pacman -S sl asciiquarium nyancat cowsay\n"
                          "  yay -S gti cbonsai oneko\npuis clique sur Actualiser.",
                     ).pack(padx=8, pady=24)
        self.canvas.yview_moveto(0)

    # -- lancement --
    def term_size(self):
        cols = max(100, min(240, self.winfo_screenwidth() // 11))
        rows = max(30, min(70, self.winfo_screenheight() // 24))
        return cols, rows

    def size_args(self):
        spec, mode = self.term_spec, self.size_var.get()
        if not spec or mode == "Normal":
            return []
        if mode == "Plein écran":
            return list(spec["full"])
        if spec["size"]:
            return spec["size"](*self.term_size())
        return []

    def term_command(self, size_args, argv):
        spec = self.term_spec
        tail = [shlex.join(argv)] if spec["style"] == "string" else argv
        return [self.term_name] + size_args + spec["exec"] + tail

    def launch_shell(self, cmd):
        if not self.term_name:
            messagebox.showerror("ASCII Dock", "Aucun terminal graphique trouvé.\n"
                                 "Installe xterm ou définis la variable $TERMINAL.")
            return
        script = (f"( {cmd} ); printf '\\n[terminé — appuie sur Entrée pour fermer] '; read _")
        argv = ["sh", "-c", script]
        size_args = self.size_args()
        try:
            proc = subprocess.Popen(self.term_command(size_args, argv))
        except Exception as exc:
            messagebox.showerror("ASCII Dock", f"Impossible de lancer :\n{exc}")
            return
        if size_args:
            fallback = self.term_command([], argv)

            def verify():
                if proc.poll() not in (None, 0):
                    try:
                        subprocess.Popen(fallback)
                    except Exception:
                        pass

            self.after(900, verify)


if __name__ == "__main__":
    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("tkinter n'est pas installé. Sur Arch/CachyOS : sudo pacman -S tk")
        sys.exit(1)
    AsciiDock().mainloop()
