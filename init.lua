
-- init.lua

-- Load the ollama bridge
local ollama_bridge = require("neovim_ollama_bridge")
local osmanli_ai_chat = require("osmanli_ai_chat")
local osmanli_ai_completion = require("osmanli_ai_completion")
local gemma_chat_nvim = require("gemma_chat_nvim")

-- Setup the bridge
ollama_bridge.setup({
    host = "127.0.0.1",
    port = 8000,
})

-- Setup the chat window
osmanli_ai_chat.setup(ollama_bridge) -- Pass the bridge to the chat module

-- Setup Gemma Chat
gemma_chat_nvim.setup() -- Setup the Gemma Chat module

-- Setup the completion
osmanli_ai_completion.setup(ollama_bridge) -- Pass the bridge to the completion module

-- Keymaps
vim.api.nvim_set_keymap('v', '<leader>ae', ":lua require('neovim_ollama_bridge').send_code('explain')<CR>", { noremap = true, silent = true })
nvim.api.nvim_set_keymap('v', '<leader>ac', ":lua require('neovim_ollama_bridge').send_code('complete')<CR>", { noremap = true, silent = true })
nvim.api.nvim_create_user_command("OsmanliChat", osmanli_ai_chat.open_chat_window, { desc = "Open Osmanli AI Chat Window" })
nvim.api.nvim_set_keymap('v', '<leader>af', ":lua require('neovim_ollama_bridge').send_code('fix')<CR>", { noremap = true, silent = true })
nvim.api.nvim_set_keymap('v', '<leader>aa', ":lua require('neovim_ollama_bridge').send_code('analyze')<CR>", { noremap = true, silent = true })
nvim.api.nvim_create_user_command("OsmanliRefactor", function(args) require('neovim_ollama_bridge').send_refactor_request(args.args) end, { nargs = 1, desc = "Send a refactoring request to Osmanli AI" })
nvim.api.nvim_create_user_command("OsmanliDebugAnalyze", function(args) require('neovim_ollama_bridge').send_debug_analysis_request(args.args) end, { nargs = 1, desc = "Send debug context for AI analysis" })
nvim.api.nvim_create_user_command("OsmanliGenerateTests", function() require('neovim_ollama_bridge').send_test_generation_request() end, { desc = "Generate tests for selected code" })

-- Autocommand to send diagnostics to Python after saving a buffer
vim.api.nvim_create_autocmd({"BufWritePost"}, {
    pattern = "*",
    callback = function()
        ollama_bridge.send_diagnostics_to_python()
    end,
})

