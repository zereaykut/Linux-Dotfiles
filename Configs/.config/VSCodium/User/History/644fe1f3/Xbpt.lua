-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not (vim.uv or vim.loop).fs_stat(lazypath) then
  local lazyrepo = "https://github.com/folke/lazy.nvim.git"
  local out = vim.fn.system({ "git", "clone", "--filter=blob:none", "--branch=stable", lazyrepo, lazypath })
  if vim.v.shell_error ~= 0 then
    vim.api.nvim_echo({
      { "Failed to clone lazy.nvim:\n", "ErrorMsg" },
      { out, "WarningMsg" },
      { "\nPress any key to exit..." },
    }, true, {})
    vim.fn.getchar()
    os.exit(1)
  end
end
vim.opt.rtp:prepend(lazypath)

-- Setup lazy.nvim
require("lazy").setup({
  spec = {
    -- 1. Import your active theme directly
    { import = "themes.tokyonight" },

    -- 2. Import grouped plugin subdirectories
    { import = "plugins.lsp" },   -- mason, nvim-cmp, lspconfig, none-ls
    { import = "plugins.ui" },    -- lualine, bufferline, indentline, rainbow
    { import = "plugins.git" },   -- gitsigns, vim-fugitive
    { import = "plugins.utils" }, -- telescope, treesitter, neo-tree, which-key, flash, comment
  },
  
  -- Optimization: Use a theme that exists for the installer UI
  install = { colorscheme = { "tokyonight" } },
  
  -- Optimization: UI appearance
  ui = {
    border = "rounded",
  },

  -- Performance: Only check for updates once a day instead of every startup
  checker = { 
    enabled = true,
    notify = false, 
  },
  
  -- Performance: Automatically reload the config when you save a file in lua/
  change_detection = {
    notify = false,
  },
})