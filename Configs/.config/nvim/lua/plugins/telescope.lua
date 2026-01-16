return {
  'nvim-telescope/telescope.nvim', tag = '0.1.8',
  config = function ()
    local builtin = require("telescope.builtin")
    vim.keymap.set("n", "<leader>fd", builtin.find_files, {desc = "Find files"})
    vim.keymap.set("n", "<leader>ff", builtin.live_grep, {desc = "Live grep"})
  end
}

