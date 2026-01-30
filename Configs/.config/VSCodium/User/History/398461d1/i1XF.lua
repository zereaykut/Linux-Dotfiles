return {
  "nvim-treesitter/nvim-treesitter",
  build = ":TSUpdate",
  dependencies = {
    -- Change this line from a simple string to a table with lazy = true
    { 
      "nvim-treesitter/nvim-treesitter-textobjects", 
      lazy = true 
    },
  },
  config = function()
    require("nvim-treesitter.configs").setup({
      ensure_installed = { 
        "c", "lua", "vim", "vimdoc", "query", "python", "javascript", "bash", "json" 
      },

      auto_install = true,
      
      highlight = { 
        enable = true,
        additional_vim_regex_highlighting = false,
        disable = function(lang, buf)
            local max_filesize = 100 * 1024 -- 100 KB
            local ok, stats = pcall(vim.loop.fs_stat, vim.api.nvim_buf_get_name(buf))
            if ok and stats and stats.size > max_filesize then
                return true
            end
        end,
      },

      indent = { enable = true },

      textobjects = {
        select = {
          enable = true,
          lookahead = true, 
          keymaps = {
            ["af"] = "@function.outer",
            ["if"] = "@function.inner",
            ["ac"] = "@class.outer",
            ["ic"] = "@class.inner",
          },
        },
      },
    })
  end,
}