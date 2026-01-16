return {
    {
        "williamboman/mason.nvim",
        opts = {
            ui = {
                icons = {
                    package_installed = "✓",
                    package_pending = "➜",
                    package_uninstalled = "✗",
                },
            },
        },
    },
    {
        "williamboman/mason-lspconfig.nvim",
        opts = {
            -- These are the specific servers for your languages
            ensure_installed = {
                "lua_ls", -- Lua Support
                "pyright", -- Python Support
                "bashls", -- Bash Support
            },
        },
    },
    -- This is a common helper to install non-LSP tools like formatters
    {
        "WhoIsSethDaniel/mason-tool-installer.nvim",
        opts = {
            ensure_installed = {
                "stylua", -- Lua Formatter
                "black", -- Python Formatter
                "debugpy", -- Python Debugger
                "shfmt", -- Bash Formatter
            },
        },
    },
}
