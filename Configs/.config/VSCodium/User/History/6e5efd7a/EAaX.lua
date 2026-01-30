require("core.keymaps")
require("core.options")


local lazypath = vim.fn.stdpath 'data' .. '/lazy/lazy.nvim'
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system {
    'git',
    'clone',
    '--filter=blob:none',
    'https://github.com/folke/lazy.nvim.git',
    '--branch=stable', -- latest stable release
    lazypath,
  }
end
vim.opt.rtp:prepend(lazypath)


require("lazy").setup(
    require "themes.catppuccin",
    require 'plugins.telescope',
    require 'plugins.treesitter',
    require 'plugins.lsp',
    require 'plugins.nvim-cmp', -- autocompletion
    require "plugins.lazygit"
    -- require "plugins.alpha"
)