import? 'adamghill.justfile'
import? '../dotfiles/just/justfile'

# List commands
_default:
    just --list --unsorted --justfile {{ justfile() }} --list-heading $'Available commands:\n'

# Grab default `adamghill.justfile` from GitHub
fetch:
  curl https://raw.githubusercontent.com/adamghill/dotfiles/master/just/justfile > adamghill.justfile

# Run the development server
serve port='8026':
  uv run --all-extras python3 manage.py runserver 0:{{ port }}
