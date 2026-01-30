return {
  "catppuccin/nvim",
  lazy = false,
  name = "rose-pine",
  priority = 1000,
  config = function()
    vim.cmd.colorscheme("catppuccin-mocha")
  end,
}