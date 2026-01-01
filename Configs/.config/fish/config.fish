set fish_greeting ""

# Variables
set -gx SOURCE_PATH "$HOME/.local/share/bin"

# Add to PATH
fish_add_path $SOURCE_PATH

# 
alias cc='clear'
# alias hl='helix'
alias nv='nvim'

# Eza
alias  l='eza -lh  --icons=auto' # long list
alias ls='eza -1   --icons=auto' # short list
alias ll='eza -lha --icons=auto --sort=name --group-directories-first' # long list all
alias ld='eza -lhD --icons=auto' # long list dirs

# Directory 
alias ..='cd ..'
alias ...='cd ../..'
alias .3='cd ../../..'
alias .4='cd ../../../..'
alias .5='cd ../../../../..'

abbr mkdir 'mkdir -p'
abbr rm 'rm -rf'

# Pacman
alias pacs='sudo pacman -S'    # Install a package
alias pacy='sudo pacman -Syu'  # Update packages & system
alias pacr='sudo pacman -Rscn' # Remove a package with its dependencies
alias upd='sudo reflector --latest 5 --age 2 --fastest 5 --protocol https --sort rate --save /etc/pacman.d/mirrorlist && cat /etc/pacman.d/mirrorlist && sudo pacman -Syu && fish_update_completions' # update pacman mirrorlist

# Yay
alias un='yay -Rns'               # uninstall package
alias up='yay -Syu'               # update system/package/aur
alias pl='yay -Qs'                # list installed package
alias pa='yay -Ss'                # list availabe package
alias pc='yay -Sc'                # remove unused cache
alias po='yay -Qtdq | yay -Rns -' # remove unused packages, also try > yay -Qqd | yay -Rsu --print -
alias vc='codium --disable-gpu'     # gui code editor

# Pikaur
alias pik='pikaur'

# Git
abbr gitc 'git clone'

# Python
alias pyev='python -m venv venv'      # create python environment named env
alias pyac='. venv/bin/activate.fish'  # activate python environment in fish shell
alias jp='jupyter lab'                # run jupyter lab

if status is-interactive
    # Commands to run in interactive sessions can go here
    
    # pyenv 
    pyenv init - | source

    # Search terminal history (Ctrl + R)
    atuin init fish | source
    
    # zoxide is a smarter cd command, inspired by z and autojump.
    zoxide init fish | source

    # Startup termşnal with a gif
    random_kitty_gif.sh
    
    # Starship
    starship init fish | source

end


