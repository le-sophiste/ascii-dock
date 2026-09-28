#!/usr/bin/env bash
# install.sh — installe ASCII Dock et l'ajoute au menu d'applications
set -e

APP_DIR="$HOME/.local/share/ascii-dock"
DESKTOP_DIR="$HOME/.local/share/applications"

mkdir -p "$APP_DIR" "$DESKTOP_DIR"
cp ascii_dock.py icon.svg "$APP_DIR/"
chmod +x "$APP_DIR/ascii_dock.py"

sed "s|__HOME__|$HOME|g" ascii-dock.desktop > "$DESKTOP_DIR/ascii-dock.desktop"
chmod +x "$DESKTOP_DIR/ascii-dock.desktop"

command -v update-desktop-database >/dev/null 2>&1 && \
  update-desktop-database "$DESKTOP_DIR" || true

if ! python3 -c "import tkinter" 2>/dev/null; then
  echo "⚠ tkinter n'est pas installé. Sur Arch/CachyOS : sudo pacman -S tk"
fi

echo
echo "✔ ASCII Dock installé."
echo "  Cherche « ASCII Dock » dans ton menu d'applications, puis épingle-la"
echo "  au dock (clic droit -> Ajouter aux favoris / Épingler au dock,"
echo "  selon ton environnement : GNOME, KDE, XFCE, Hyprland+dock, etc.)"
echo
echo "  Tu peux aussi la lancer directement avec :"
echo "  python3 $APP_DIR/ascii_dock.py"
