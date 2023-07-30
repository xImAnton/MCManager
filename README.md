
# MCSRV

Manage your Minecraft Servers on Linux with a convenient CLI

*More Documentation coming...*

## .bashrc function

Pasting this function into your `.bashrc` allows for a quicker navigation
between server directories. By typing `mcd <server-id>`, your shell cd's into
the directory of the server. (mcd: short for mc-cd)
```bash
function mcd {
  if [ -z "$1" ]
  then
          echo -e "Available Servers:\n$(mcsrv list --props i --plain | sed 's/^/  /')"
          return
  fi
  eval "cd $(mcsrv dir $1)"
}
```
