return {
  {
    "nvim-neo-tree/neo-tree.nvim",
    branch = "v3.x",
    dependencies = {
      "nvim-lua/plenary.nvim",
      "MunifTanjim/nui.nvim",
      "nvim-tree/nvim-web-devicons",
    },
    lazy = false,
    config = function ()
      vim.keymap.set("n", "<leader>e", "<Cmd>Neotree toggle<CR>", {desc="Toggle Neo-Tree"})
      require("neo-tree").setup({
        filesystem = {
          filtered_items = {
            hide_dotfiles = false
          }
        },
        -- Add this window section to change the default behavior
        window = {
          mappings = {
            ["<cr>"] = "open",        -- Enter opens in the current buffer
            ["t"]    = "open_tabnew", -- Press 't' to open in a new tab/bufferline entry
          }
        }
      })
    end
  }
}
