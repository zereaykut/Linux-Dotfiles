# 💤 My Neovim Configuration

A personal, modular, and blazing fast Neovim configuration written in Lua. Managed by [lazy.nvim](https://github.com/folke/lazy.nvim).

![Neovim](https://img.shields.io/badge/Neovim-0.9+-57A143?style=for-the-badge&logo=neovim&logoColor=white)
![Lua](https://img.shields.io/badge/Lua-blue?style=for-the-badge&logo=lua&logoColor=white)

## ✨ Features

* **Package Manager**: Lazy.nvim for fast startup times.
* **LSP Support**: Native LSP configuration with Autocomplete (`nvim-cmp`).
* **Linting & Formatting**: `none-ls` and `conform` (via formatting.lua).
* **Syntax Highlighting**: Treesitter for better code coloration.
* **File Explorer**: Neo-tree for sidebar file management.
* **Fuzzy Finding**: Telescope to find files and text instantly.
* **Git Integration**: Git integration baked in.
* **AI Integration**: Setup for AI coding assistants.
* **Theme Switching**: Multiple color schemes configured.

## 📂 Structure

```text
.
├── init.lua              # Entry point
├── lazy-lock.json        # Plugin lockfile
└── lua
    ├── config            # Core configuration
    │   ├── keymaps.lua   # Custom keybindings
    │   ├── lazy.lua      # Lazy.nvim setup
    │   └── options.lua   # Vim options (numbers, tabs, etc.)
    ├── plugins           # Plugin specifications
    │   ├── ai.lua
    │   ├── autopairs.lua
    │   ├── comment.lua
    │   ├── flash.lua
    │   ├── formatting.lua
    │   ├── git-stuff.lua
    │   ├── lsp.lua
    │   ├── lualine.lua
    │   ├── neo-tree.lua
    │   ├── none-ls.lua
    │   ├── nvim-cmp.lua
    │   ├── spectre.lua
    │   ├── telescope.lua
    │   ├── treesitter.lua
    │   ├── trouble.lua
    │   ├── ui.lua
    │   └── which-key.lua
    └── themes            # Color schemes
        ├── catppuccin.lua
        ├── graphite.lua
        ├── gruvbox.lua
        ├── rosepine.lua
        ├── tokyonight.lua
        └── vague.lua