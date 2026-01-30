-- lua/plugins/lsp/lspconfig.lua
return {
  "neovim/nvim-lspconfig",
  dependencies = { 
    "hrsh7th/cmp-nvim-lsp",
    "williamboman/mason-lspconfig.nvim", -- Ensure Mason bridge is loaded first
  },
  config = function()
    -- This loads your server configurations and global LSP settings
    require("configs.lsp") 
  end,
}