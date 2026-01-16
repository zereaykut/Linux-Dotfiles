return {
	"nvimtools/none-ls.nvim",
	dependencies = { "nvim-lua/plenary.nvim" },
	config = function()
		local null_ls = require("null-ls")
		null_ls.setup({
			sources = {
				null_ls.builtins.formatting.stylua, -- Lua Formatter
				null_ls.builtins.formatting.black, -- Python Formatter
				null_ls.builtins.formatting.shfmt, -- Bash Formatter
			},
		})
	end,
}
