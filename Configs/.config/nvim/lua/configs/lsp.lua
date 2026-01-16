-- Setup capabilities for nvim-cmp
local capabilities = require("cmp_nvim_lsp").default_capabilities()

-- 2. Configure Lua Support
vim.lsp.config("lua_ls", {
	capabilities = capabilities,
	settings = {
		Lua = {
			diagnostics = {
				globals = { "vim" },
			},
		},
	},
})
vim.lsp.enable("lua_ls")

-- Configure Python Support (Pyright)
vim.lsp.config("pyright", {
	capabilities = capabilities,
	settings = {
		python = {
			analysis = {
				autoSearchPaths = true,
				useLibraryCodeForTypes = true,
				diagnosticMode = "openFilesOnly",
				typeCheckingMode = "basic",
			},
		},
	},
})
vim.lsp.enable("pyright")

-- Configure Bash Support (bashls)
vim.lsp.config("bashls", {
	capabilities = capabilities,
})
vim.lsp.enable("bashls")

-- General Diagnostics Config
vim.diagnostic.config({
	virtual_text = true,
})

-- LspAttach: Completion & Format on Save
vim.api.nvim_create_autocmd("LspAttach", {
	callback = function(ev)
		local client = vim.lsp.get_client_by_id(ev.data.client_id)

		-- Native completion support (Neovim 0.11+)
		if client and client:supports_method("textDocument/completion") then
			vim.lsp.completion.enable(true, client.id, ev.buf, { autotrigger = false })
		end

		-- Format on Save logic
		-- Only creates the autocmd if the server supports formatting
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
