-- /home/desktop/Desktop/box/curtain/nvim_integration/gemma_chat_nvim.lua

local M = {} -- Module table to export functions

local default_config = {
    -- Add Gemma-specific settings here if needed
}

local chat_bufnr = nil -- To store the buffer number of the chat window

-- Function to append messages to the chat buffer
function M.append_to_chat_buffer(message)
    if not chat_bufnr or not vim.api.nvim_buf_is_valid(chat_bufnr) then
        return
    end
    
    -- Ensure buffer is modifiable before writing
    vim.api.nvim_buf_set_option(chat_bufnr, 'modifiable', true)
    
    -- Append the message
    vim.api.nvim_buf_set_lines(chat_bufnr, -1, -1, false, {message})
    
    -- Scroll to bottom
    vim.cmd('normal! G')
    
    -- Set back to non-modifiable after writing
    vim.api.nvim_buf_set_option(chat_bufnr, 'modifiable', false)
end

-- Function to send chat message
function M.send_chat_message()
    if not chat_bufnr or not vim.api.nvim_buf_is_valid(chat_bufnr) then
        return
    end

    local current_line = vim.api.nvim_get_current_line()
    if current_line == "" then return end -- Don't send empty messages

    -- Ensure buffer is modifiable for the entire operation
    vim.api.nvim_buf_set_option(chat_bufnr, 'modifiable', true)

    -- Append user message to chat history
    vim.api.nvim_buf_set_lines(chat_bufnr, -1, -1, false, {"You: " .. current_line})

    -- Clear the input line (by replacing it with an empty string)
    local line_num = vim.api.nvim_win_get_cursor(0)[1]
    vim.api.nvim_buf_set_lines(chat_bufnr, line_num - 1, line_num, false, {""})

    -- Send message to Python bridge
    local message_payload = {
        type = "chat_message",
        payload = {
            message = current_line
        }
    }
    require('neovim_ollama_bridge').send_message(message_payload)

    -- Append "AI: Thinking..." message
    vim.api.nvim_buf_set_lines(chat_bufnr, -1, -1, false, {"AI: Thinking..."})

    -- Set back to non-modifiable after all writes
    vim.api.nvim_buf_set_option(chat_bufnr, 'modifiable', false)
    
    -- Go back to insert mode for next input
    vim.cmd('startinsert')
end

function M.setup(opts)
    opts = opts or {}
    local config = vim.tbl_deep_extend("force", default_config, opts)

    vim.notify("Gemma Chat Neovim: Initializing chat interface.", vim.log.levels.INFO)

    vim.api.nvim_create_user_command("GemmaChat", function()
        -- Create a new buffer if one doesn't exist or is invalid
        if not chat_bufnr or not vim.api.nvim_buf_is_valid(chat_bufnr) then
            vim.cmd("vsplit") -- Open a new vertical split for chat
            vim.cmd("enew") -- Create a new empty buffer
            chat_bufnr = vim.api.nvim_get_current_buf()

            vim.bo.buftype = "nofile"   -- Make it a scratch buffer
            vim.bo.bufhidden = "wipe"   -- Close it when hidden
            vim.bo.swapfile = false     -- Don't create a swap file
            vim.bo.modifiable = true    -- Start as modifiable for initial content
            
            vim.api.nvim_buf_set_name(chat_bufnr, "GemmaChatBuffer")
            vim.api.nvim_buf_set_lines(chat_bufnr, 0, -1, false, {
                "Hello! I am Gemma. How can I help you today?",
                "--------------------------------------------------",
                "Type your message below and press Enter to send.",
                "--------------------------------------------------",
                ""
            })
            
            -- Set to non-modifiable after initial setup
            vim.api.nvim_buf_set_option(chat_bufnr, 'modifiable', false)
        else
            -- Switch to existing chat buffer
            vim.api.nvim_set_current_buf(chat_bufnr)
        end

        -- Map <CR> in insert mode to send message
        vim.api.nvim_buf_set_keymap(chat_bufnr, 'i', '<CR>', 
            [[<Esc>:lua require('gemma_chat_nvim').send_chat_message()<CR>]], 
            {noremap = true, silent = true})

        vim.notify("Gemma Chat buffer opened. Type and press Enter to send.", vim.log.levels.INFO)
        vim.cmd('startinsert')
    end, { desc = "Open Gemma AI chat interface" })

    vim.notify("Gemma Chat Neovim setup complete. Use :GemmaChat", vim.log.levels.INFO)
end

return M