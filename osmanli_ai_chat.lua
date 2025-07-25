-- osmanli_ai_chat.lua

local M = {}
local uv = vim.loop
local job_handles = {}
local ollama_bridge = nil -- To hold the bridge instance

local chat_bufnr = nil
local chat_winid = nil

local function notify(msg, level)
    vim.notify("Osmanli AI Chat: " .. msg, level or vim.log.levels.INFO)
end

local function append_to_chat_buffer(text)
    if chat_bufnr and vim.api.nvim_buf_is_valid(chat_bufnr) then
        vim.api.nvim_buf_set_option(chat_bufnr, "modifiable", true)
        vim.api.nvim_buf_set_lines(chat_bufnr, -1, -1, false, vim.split(text, "\n", { plain = true }))
        vim.api.nvim_buf_set_option(chat_bufnr, "modifiable", false)
        vim.api.nvim_win_set_cursor(chat_winid, {vim.api.nvim_buf_line_count(chat_bufnr), 0})
    end
end

local function handle_shell_output(err, data)
    if err then
        append_to_chat_buffer("[ERROR]: " .. err .. "\n")
        return
    end
    if data then
        append_to_chat_buffer(data)
    end
end

local function on_exit(code, signal)
    append_to_chat_buffer(string.format("\n[Process exited with code: %d, signal: %s]\n", code, signal or "none"))
end

local function execute_shell_command(command)
    append_to_chat_buffer("\n> " .. command .. "\n")
    local job_id = uv.spawn(command, {
        args = vim.split(command, " "),
        stdio = {nil, "pipe", "pipe"},
    }, on_exit)

    if job_id then
        job_handles[job_id] = true
        uv.read_start(job_id, handle_shell_output)
    else
        append_to_chat_buffer("[ERROR]: Failed to start process.\n")
    end
end

local function send_to_ai(prompt)
    append_to_chat_buffer("\n[You]: " .. prompt .. "\n")
    -- This will be handled by the Python side via the bridge
    -- For now, we'll just simulate a response
    append_to_chat_buffer("[AI]: Thinking... (Integration with Python AI coming soon)\n")
    if ollama_bridge then
        -- Send the prompt to the Python AI via the bridge
        local response = ollama_bridge.send_request({
            action = "chat",
            prompt = prompt,
        })
        if response and response.chat_response then
            append_to_chat_buffer("[AI]: " .. response.chat_response .. "\n")
        elseif response and response.error then
            append_to_chat_buffer("[AI Error]: " .. response.error .. "\n")
        else
            append_to_chat_buffer("[AI]: No response or unexpected response from AI.\n")
        end
    else
        append_to_chat_buffer("[AI]: Bridge not initialized. Cannot send prompt.\n")
    end
end

function M.setup(bridge_instance)
    ollama_bridge = bridge_instance
end

function M.open_chat_window()
    if chat_bufnr and vim.api.nvim_buf_is_valid(chat_bufnr) and chat_winid and vim.api.nvim_win_is_valid(chat_winid) then
        vim.api.nvim_set_current_win(chat_winid)
        return
    end

    chat_bufnr = vim.api.nvim_create_buf(false, { scratch = true, buftype = "nofile", bufhidden = "hide" })
    vim.api.nvim_buf_set_name(chat_bufnr, "OsmanliAIChat")

    chat_winid = vim.api.nvim_open_win(chat_bufnr, true, {
        relative = "editor",
        width = math.floor(vim.o.columns * 0.4),
        height = math.floor(vim.o.lines * 0.8),
        row = math.floor(vim.o.lines * 0.1),
        col = math.floor(vim.o.columns * 0.55),
        border = "single",
        focusable = true,
        zindex = 100,
    })

    vim.api.nvim_buf_set_lines(chat_bufnr, 0, -1, false, {"Welcome to Osmanli AI Chat!", "", "Type your message or a shell command (prefix with !) below.", ""})
    vim.api.nvim_buf_set_option(chat_bufnr, "modifiable", false)

    -- Create an input buffer below the chat window
    local input_bufnr = vim.api.nvim_create_buf(false, { scratch = true, buftype = "nofile", bufhidden = "hide" })
    vim.api.nvim_buf_set_name(input_bufnr, "OsmanliAIChatInput")

    local input_winid = vim.api.nvim_open_win(input_bufnr, true, {
        relative = "win",
        win = chat_winid,
        anchor = "SW",
        width = math.floor(vim.o.columns * 0.4),
        height = 1,
        row = math.floor(vim.o.lines * 0.8) - 1,
        col = 0,
        border = "single",
        focusable = true,
        zindex = 100,
    })

    vim.api.nvim_set_current_win(input_winid)
    vim.api.nvim_buf_set_option(input_bufnr, "buflisted", false)
    vim.api.nvim_buf_set_option(input_bufnr, "wrap", false)
    vim.api.nvim_buf_set_option(input_bufnr, "filetype", "osmanli_ai_chat_input")

    vim.api.nvim_buf_set_keymap(input_bufnr, "n", "<CR>", ":lua require('osmanli_ai_chat').handle_input()<CR>", { noremap = true, silent = true })
    vim.api.nvim_buf_set_keymap(input_bufnr, "i", "<CR>", ":lua require('osmanli_ai_chat').handle_input()<CR>", { noremap = true, silent = true })

    vim.cmd("startinsert")
end

function M.handle_input()
    local input_bufnr = vim.api.nvim_get_current_buf()
    local input_line = vim.api.nvim_buf_get_lines(input_bufnr, 0, 1, false)[1]
    vim.api.nvim_buf_set_lines(input_bufnr, 0, -1, false, { "" })

    if input_line:sub(1, 1) == "!" then
        execute_shell_command(input_line:sub(2))
    else
        send_to_ai(input_line)
    end

    vim.api.nvim_set_current_win(vim.api.nvim_get_current_win())
    vim.cmd("startinsert")
end

return M
