return {
  "binarylinuxx/graphite-nvim",
  priority = 1000,  -- Load first
  config = function()
    vim.cmd.colorscheme("graphite")  -- Default grey variant
    -- Or choose from available variants:
    -- vim.cmd.colorscheme("graphite-grey")
    -- vim.cmd.colorscheme("graphite-purple") 
    -- vim.cmd.colorscheme("graphite-pink")
    -- vim.cmd.colorscheme("graphite-red")
    -- vim.cmd.colorscheme("graphite-orange")
    -- vim.cmd.colorscheme("graphite-yellow")
    -- vim.cmd.colorscheme("graphite-green")
    -- vim.cmd.colorscheme("graphite-teal")
    -- vim.cmd.colorscheme("graphite-blue")
  end,
}