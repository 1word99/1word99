
-- osmanli_ai_completion.lua

local M = {}
local ollama_bridge = nil

local function notify(msg, level)
    vim.notify("Osmanli AI Completion: " .. msg, level or vim.log.levels.INFO)
end

function M.setup(bridge_instance)
    ollama_bridge = bridge_instance

    -- Setup a basic completion source
    vim.api.nvim_create_autocmd("InsertCharPre", {
        group = vim.api.nvim_create_augroup("OsmanliAICompletion", { clear = true }),
        callback = function()
            local line = vim.api.nvim_get_current_line()
            local cursor_col = vim.api.nvim_win_get_cursor(0)[2]
            local partial_line = string.sub(line, 1, cursor_col)

            -- Only trigger if the partial line is not empty and has some length
            if #partial_line > 0 and ollama_bridge then
                -- Send a request to the Python backend for completion
                -- This should be an async call, but for simplicity, we'll make it blocking for now
                -- In a real scenario, you'd want to debounce this and handle async responses
                local response = ollama_bridge.send_request({
                    action = "complete_as_you_type",
                    code = partial_line,
                    context = {
                        filepath = vim.api.nvim_buf_get_name(0),
                        cursor = vim.api.nvim_win_get_cursor(0),
                    }
                })

                if response and response.completion then
                    -- This is a very basic way to insert completion.
                    -- A proper LSP or completion plugin integration would be more robust.
                    local completion_text = response.completion
                    -- Only insert if the completion actually adds something new
                    if string.find(completion_text, partial_line, 1, true) == 1 then
                        local remaining = string.sub(completion_text, #partial_line + 1)
                        if #remaining > 0 then
                            vim.api.nvim_feedkeys(remaining, "n", false)
                        end
                    end
                elseif response and response.error then
                    notify("Completion error: " .. response.error, vim.log.levels.ERROR)
                end
            end
        end,
    })
end

return M
