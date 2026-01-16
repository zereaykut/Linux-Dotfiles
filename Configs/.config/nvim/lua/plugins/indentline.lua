return {
	"lukas-reineke/indent-blankline.nvim",
	main = "ibl",
	event = { "BufReadPost", "BufNewFile" },
	opts = {
		indent = {
			char = "│", -- This is the vertical line character
			tab_char = "│",
		},
		scope = {
			enabled = true,
			show_start = true,
			show_end = false,
			injected_languages = false,
			highlight = { "Function", "Label" },
			priority = 1024,
		},
		exclude = {
			filetypes = {
				"help",
				"neo-tree",
				"lazy",
				"mason",
			},
		},
	},
}
