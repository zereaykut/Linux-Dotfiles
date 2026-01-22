-- A Git wrapper so awesome, it should be illegal
return {
    "tpope/vim-fugitive",
    config = function()
        -- Git Status Dashboard
        vim.keymap.set("n", "<leader>gs", vim.cmd.Git, { desc = "Git [S]tatus" })

        -- Commit mappings
        vim.keymap.set("n", "<leader>gc", ":Git commit<CR>", { desc = "Git [C]ommit" })

        -- Push and Pull
        vim.keymap.set("n", "<leader>gp", ":Git push<CR>", { desc = "Git [P]ush" })
        vim.keymap.set("n", "<leader>gl", ":Git pull<CR>", { desc = "Git Pu[l]l" })

        -- Diff/Conflict Resolution
        -- Using 'h' and 'l' to represent left/right target selection
        vim.keymap.set("n", "<leader>gh", ":diffget //2<CR>", { desc = "Git Diff Get [H] (Left)" })
        vim.keymap.set("n", "<leader>gj", ":diffget //3<CR>", { desc = "Git Diff Get [L] (Right)" })

        -- Blame
        vim.keymap.set("n", "<leader>gb", ":Git blame<CR>", { desc = "Git [B]lame" })
    end,
}
