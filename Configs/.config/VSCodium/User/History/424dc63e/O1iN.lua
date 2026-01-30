local capabilities = require('cmp_nvim_lsp').default_capabilities()

-- 1. Load Lua settings from your new location
local lua_settings = require("plugins.lsp.lua_ls")

-- 2. Configure Lua
vim.lsp.config('lua_ls', {
  capabilities = capabilities,
  settings = lua_settings.settings, -- Use the settings from the other file
})
vim.lsp.enable('lua_ls')

-- 3. Configure Python (Pyright)
vim.lsp.config('pyright', {
  capabilities = capabilities,
})
vim.lsp.enable('pyright')

-- 4. Configure Bash
vim.lsp.config('bashls', {
  capabilities = capabilities,
})
vim.lsp.enable('bashls')

-- Global LspAttach for Autocomplete and Format on Save
vim.api.nvim_create_autocmd("LspAttach", {
  callback = function(ev)
    local client = vim.lsp.get_client_by_id(ev.data.client_id)
    
    -- Autocomplete
    if client and client:supports_method("textDocument/completion") then
      vim.lsp.completion.enable(true, client.id, ev.buf, { autotrigger = false })
    end

    -- Format on Save
    if client and client:supports_method("textDocument/formatting") then
      vim.api.nvim_create_autocmd("BufWritePre", {
        buffer = ev.buf,
        callback = function()
          vim.lsp.buf.format({ bufnr = ev.buf, id = client.id })
        end,
      })
    end
  end,
})