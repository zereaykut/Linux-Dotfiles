return {
    "numToStr/Comment.nvim",
    opts = {
        -- Add any custom configuration here
    },
    config = function(_, opts)
        require("Comment").setup(opts)
    end,
}
