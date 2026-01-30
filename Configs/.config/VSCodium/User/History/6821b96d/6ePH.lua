return {
    "neovim/nvim-lspconfig",
    dependencies = {
        "williamboman/mason.nvim",
        "williamboman/mason-lspconfig.nvim",
        "WhoIsSethDaniel/mason-tool-installer.nvim",
        "hrsh7th/cmp-nvim-lsp", -- Integration with nvim-cmp
    },
    config = function()
        local lspconfig = require("lspconfig")
        local capabilities = require("cmp_nvim_lsp").default_capabilities()

        -- 1. Setup Mason
        require("mason").setup({
            ui = {
                icons = {
                    package_installed = "✓",
                    package_pending = "➜",
                    package_uninstalled = "✗",
                },
            },
        })

        -- 2. Setup Mason Tool Installer (For non-LSP tools)
        require("mason-tool-installer").setup({
            ensure_installed = {
                "stylua", -- Lua formatter
                "black",  -- Python formatter
                "debugpy", -- Python debugger
                "shfmt",  -- Shell formatter
            },
        })

        -- 3. Setup Mason LSP Config (Auto-setup servers)
        require("mason-lspconfig").setup({
            ensure_installed = { "lua_ls", "pyright", "bashls" },
            handlers = {
                -- Default handler: Setup server with default config
                function(server_name)
                    lspconfig[server_name].setup({
                        capabilities = capabilities,
                    })
                end,

                -- Custom Override: Lua LS
                ["lua_ls"] = function()
                    lspconfig.lua_ls.setup({
                        capabilities = capabilities,
                        settings = {
                            Lua = {
                                diagnostics = { globals = { "vim" } },
                            },
                        },
                    })
                end,

                -- Custom Override: Pyright
                ["pyright"] = function()
                    lspconfig.pyright.setup({
                        capabilities = capabilities,
                        settings = {
                            python = {
                                analysis = {
                                    autoSearchPaths = true,
                                    useLibraryCodeForTypes = true,
                                    diagnosticMode = "openFilesOnly",
                                    typeCheckingMode = "basic",
                                },
                            },
                        },
                    })
                end,
            },
        })

        -- 4. LspAttach Autocommand (Keymaps & Formatting)
        vim.api.nvim_create_autocmd("LspAttach", {
            group = vim.api.nvim_create_augroup("UserLspConfig", {}),
            callback = function(ev)
                local client = vim.lsp.get_client_by_id(ev.data.client_id)
                local opts = { buffer = ev.buf }

                -- Example Keymaps
                vim.keymap.set("n", "gD", vim.lsp.buf.declaration, opts)
                vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
                vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
                vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)
                vim.keymap.set({ "n", "v" }, "<leader>ca", vim.lsp.buf.code_action, opts)

                -- Format on Save (using None-ls or LSP)
                if client and client.supports_method("textDocument/formatting") then
                    vim.api.nvim_create_autocmd("BufWritePre", {
                        buffer = ev.buf,
                        callback = function()
                             -- Use whatever formatter is available (LSP or None-ls)
                            vim.lsp.buf.format({ async = false, bufnr = ev.buf })
                        end,
                    })
                end
            end,
        })
    end,
}