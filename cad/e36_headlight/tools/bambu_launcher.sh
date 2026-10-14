#!/bin/sh
# Run the Flathub Bambu Studio outside the flatpak sandbox (containers without a session bus) using its runtime libs.
A=$HOME/.local/share/flatpak/app/com.bambulab.BambuStudio/current/active/files
R=$HOME/.local/share/flatpak/runtime/org.gnome.Platform/x86_64/50/active/files
export LD_LIBRARY_PATH=$A/lib:$A/lib/x86_64-linux-gnu:$R/lib/x86_64-linux-gnu:$R/lib
export GIO_MODULE_DIR=$R/lib/x86_64-linux-gnu/gio/modules
exec $R/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 $A/bin/bambu-studio "$@"
