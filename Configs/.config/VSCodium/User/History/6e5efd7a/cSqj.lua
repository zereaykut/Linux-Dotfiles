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
    require "plugins.alpha", -- dashboard
    require 'plugins.telescope',
    require 'plugins.treesitter',
    require 'plugins.lsp',
    require 'plugins.nvim-cmp', -- autocompletion
    require 'plugins.nvim-tree',
    require "plugins.lazygit",

    require 'plugins.auto-session',
    require "plugins.autopairs",
    require "plugins.bufferline",
    require "plugins.comment",
    require "plugins.dressing",
    require "plugins.formatting",
    require "plugins.gitsigns",
    require "plugins.indent-blankline",
    require "plugins.misc",
    require "plugins.linting",


    -- require "plugins.alpha"
)