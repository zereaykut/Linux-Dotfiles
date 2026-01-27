return {
	"nvim-pack/nvim-spectre",
	dependencies = { "nvim-lua/plenary.nvim" },
	-- Load the plugin when the "Spectre" command is triggered
	cmd = "Spectre",
	opts = {
		open_cmd = "vnew", -- Open in a vertical split
		-- You can add more custom configuration here (see spectre documentation)
	},
	-- Keymaps to trigger the plugin
	keys = {
		{
			"<leader>S",
			function()
				require("spectre").open()
			end,
			desc = "Open Spectre (Search & Replace)",
		},
		{
			"<leader>sw",
			function()
				require("spectre").open_visual({ select_word = true })
			end,
			desc = "Spectre: Search current word",
		},
		{
			"<leader>sw",
			function()
				require("spectre").open_visual()
			end,
			mode = "v", -- Enable in visual mode
			desc = "Spectre: Search selection",
		},
		{
			"<leader>sp",
			function()
				require("spectre").open_file_search({ select_word = true })
			end,
			desc = "Spectre: Search in current file",
		},
	},
}
