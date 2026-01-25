return {
	{
		"nvim-treesitter/nvim-treesitter",
		branch = "master",
		lazy = false,
		build = ":TSUpdate",
		config = function()
			require("nvim-treesitter.configs").setup({
				ensure_installed = {
					"lua",
					"python",
					"bash",
					"vim",
					"vimdoc",
					"javascript",
					"typescript",
					"tsx",
					"yaml",
					"markdown",
					"markdown_inline",
					"gitignore",
					"dockerfile",
					"json",
					"c",
				},
				highlight = { enable = true },
				indent = { enable = true },
			})
			vim.treesitter.language.register("bash", "zsh")
		end,
	},
}
