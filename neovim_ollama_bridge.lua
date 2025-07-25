-- /home/desktop/Desktop/box/curtain/nvim_integration/neovim_ollama_bridge.lua

local M = {} -- Module table to export functions
local uv = vim.loop -- Alias for Neovim's libuv functions
local json = vim.json -- Neovim's built-in JSON parser

-- Default configuration for the bridge
local default_config = {
    host = "127.0.0.1",
    port = 8001,
    reconnect_interval = 5000 -- 5 seconds
}

local client = nil -- Variable to hold the client object
local config = {}
local reconnect_timer = nil

-- Helper to display messages
local function notify(msg, level)
    vim.schedule(function()
        vim.notify("Neovim Ollama Bridge: " .. msg, level or vim.log.levels.INFO)
    end)
end

-- --- Message Handlers ---
-- (Message handlers remain the same as before)
local function handle_fix_proposals(payload)
    local proposals = payload.proposals
    if not proposals or #proposals == 0 then
        notify("No fix proposals received.", vim.log.levels.INFO)
        return
    end

    local bufnr = vim.api.nvim_get_current_buf()
    local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
    local proposal_lines = {}
    table.insert(proposal_lines, "--- Proposed Fixes ---")
    table.insert(proposal_lines, "")

    for i, proposal in ipairs(proposals) do
        table.insert(proposal_lines, string.format("Proposal %d: %s", i, proposal.description or "No description"))
        table.insert(proposal_lines, string.format("  File: %s", proposal.filepath))
        table.insert(proposal_lines, string.format("  Line: %d", proposal.line))
        table.insert(proposal_lines, "  --- Old ---")
        table.insert(proposal_lines, "  " .. (proposal.old_text or ""))
        table.insert(proposal_lines, "  --- New ---")
        table.insert(proposal_lines, "  " .. (proposal.new_text or ""))
        table.insert(proposal_lines, "")
    end

    -- Display in a floating window for now. For actual interaction, a more complex UI is needed.
    vim.api.nvim_open_win(0, true, {
        relative = "editor",
        row = math.floor(vim.o.lines * 0.1),
        col = math.floor(vim.o.columns * 0.1),
        width = math.floor(vim.o.columns * 0.8),
        height = math.floor(vim.o.lines * 0.8),
        border = "single",
        style = "minimal",
        bufhidden = "wipe",
        focusable = true,
    })
    local win_bufnr = vim.api.nvim_get_current_buf()
    vim.api.nvim_buf_set_lines(win_bufnr, 0, -1, false, proposal_lines)
    vim.api.nvim_buf_set_option(win_bufnr, "modifiable", false)
    notify("Fix proposals displayed in floating window.", vim.log.levels.INFO)
end

local function handle_diagnostics(payload)
    local diagnostics = payload.diagnostics
    local filepath = payload.filepath
    if not diagnostics or #diagnostics == 0 then
        notify("No diagnostics received.", vim.log.levels.INFO)
        vim.diagnostic.set("ollama-bridge", 0, {}) -- Clear diagnostics for current buffer
        return
    end

    local nvim_diagnostics = {}
    for _, diag in ipairs(diagnostics) do
        table.insert(nvim_diagnostics, {
            lnum = diag.line - 1, -- 0-indexed
            col = diag.column - 1, -- 0-indexed
            message = diag.message,
            severity = vim.diagnostic.severity[diag.severity:upper()] or vim.diagnostic.severity.INFO,
            source = "OllamaBridge",
        })
    end
    
    vim.diagnostic.set("ollama-bridge", 0, nvim_diagnostics, {
        filetype = vim.bo.filetype,
        bufnr = vim.api.nvim_get_current_buf(),
    })
    notify(string.format("Received %d diagnostics for %s.", #diagnostics, filepath), vim.log.levels.INFO)
end

local function handle_code_generation(payload)
    local generated_code = payload.code
    local description = payload.description or "Generated Code"
    if not generated_code then
        notify("No code received for generation.", vim.log.levels.WARN)
        return
    end

    vim.cmd("vnew") -- Open a new vertical split
    local bufnr = vim.api.nvim_get_current_buf()
    vim.api.nvim_buf_set_option(bufnr, "bufhidden", "wipe")
    vim.api.nvim_buf_set_option(bufnr, "buftype", "nofile")
    vim.api.nvim_buf_set_option(bufnr, "swapfile", false)
    vim.api.nvim_buf_set_name(bufnr, description .. " (Generated)")
    vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, vim.split(generated_code, "\n", { plain = true }))
    notify(string.format("Generated code for '%s' displayed in new buffer.", description), vim.log.levels.INFO)
end

local function handle_code_insertion(payload)
    local code = payload.code
    if not code then
        notify("No code received for insertion.", vim.log.levels.WARN)
        return
    end

    vim.api.nvim_buf_set_lines(0, vim.api.nvim_get_current_line(), vim.api.nvim_get_current_line(), false, vim.split(code, "\n", { plain = true }))
    notify("Code inserted into current buffer.", vim.log.levels.INFO)
end

local function handle_fix_results(payload)
    local status = payload.status
    local message = payload.message
    local fixed_code = payload.fixed_code

    if status == "success" then
        notify("Fix results: " .. message, vim.log.levels.INFO)
        if fixed_code then
            handle_code_generation({code = fixed_code, description = "Fixed Code"})
        end
    else
        notify("Fix failed: " .. message, vim.log.levels.ERROR)
    end
end

local function handle_analysis_results(payload)
    local status = payload.status
    local message = payload.message
    local analysis_results = payload.analysis_results

    if status == "success" then
        notify("Analysis results: " .. message, vim.log.levels.INFO)
        if analysis_results and analysis_results.issues then
            local nvim_diagnostics = {}
            for _, issue in ipairs(analysis_results.issues) do
                table.insert(nvim_diagnostics, {
                    lnum = issue.line - 1,
                    col = issue.column - 1,
                    message = issue.message,
                    severity = vim.diagnostic.severity[issue.severity:upper()] or vim.diagnostic.severity.INFO,
                    source = "OsmanliAI",
                })
            end
            vim.diagnostic.set("osmanli-ai", 0, nvim_diagnostics, { bufnr = vim.api.nvim_get_current_buf() })
        end
    else
        notify("Analysis failed: " .. message, vim.log.levels.ERROR)
    end
end

local function handle_refactor_results(payload)
    local status = payload.status
    local message = payload.message
    local changes_applied = payload.changes_applied

    if status == "success" then
        notify("Refactor results: " .. message, vim.log.levels.INFO)
        if changes_applied and changes_applied.applied_changes then
            for _, change in ipairs(changes_applied.applied_changes) do
                notify(string.format("Applied %s to %s: %s", change.action, change.filepath, change.status), vim.log.levels.INFO)
            end
        end
    else
        notify("Refactor failed: " .. message, vim.log.levels.ERROR)
    end
end

local function handle_debug_analysis_results(payload)
    local status = payload.status
    local analysis = payload.analysis

    if status == "success" then
        notify("Debug Analysis Results: " .. analysis, vim.log.levels.INFO)
    else
        notify("Debug Analysis Failed: " .. analysis, vim.log.levels.ERROR)
    end
end

local function handle_verification_results(payload)
    local results = payload.results
    if results then
        local chat_module = require("gemma_chat_nvim")
        chat_module.append_to_chat_buffer("\n--- Verification Results ---")
        chat_module.append_to_chat_buffer("Tests: " .. (results.tests or "N/A"))
        chat_module.append_to_chat_buffer("Linting: " .. (results.linting or "N/A"))
        chat_module.append_to_chat_buffer("--------------------------\n")
    end
end

local function handle_chat_response(payload)
    local response = payload.response
    if response then
        local chat_module = require("gemma_chat_nvim")
        chat_module.append_to_chat_buffer("AI: " .. response)
    end
end

local function handle_apply_fix(payload)
    local filepath = payload.filepath
    local old_content = payload.old_content
    local new_content = payload.new_content

    if not filepath or not old_content or not new_content then
        notify("Invalid apply_fix payload.", vim.log.levels.ERROR)
        return
    end

    local current_filepath = vim.api.nvim_buf_get_name(0)
    local bufnr = vim.api.nvim_get_current_buf()

    if current_filepath ~= filepath then
        local found_buf = false
        for _, b in ipairs(vim.api.nvim_list_bufs()) do
            if vim.api.nvim_buf_is_valid(b) and vim.api.nvim_buf_get_name(b) == filepath then
                bufnr = b
                found_buf = true
                break
            end
        end

        if not found_buf then
            vim.cmd("edit " .. filepath)
            bufnr = vim.api.nvim_get_current_buf()
        end
    end

    local current_lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
    local current_content = table.concat(current_lines, "\n")

    if current_content == old_content then
        vim.api.nvim_buf_set_lines(bufnr, 0, -1, false, vim.split(new_content, "\n", { plain = true }))
        vim.api.nvim_buf_call(bufnr, function()
            vim.cmd("write")
        end)
        notify(string.format("Applied fix to %s", filepath), vim.log.levels.INFO)
    else
        notify(string.format("Content mismatch for %s. Fix not applied.", filepath), vim.log.levels.WARN)
    end
end

local function handle_ping(payload)
    notify("Received ping from Python server. Sending pong.", vim.log.levels.DEBUG)
    M.send_message({type = "pong", payload = {timestamp = uv.now()}})
end

-- Dispatch incoming messages based on their 'type'
local message_dispatch = {
    fix_proposals = handle_fix_proposals,
    diagnostics = handle_diagnostics,
    code_generation = handle_code_generation,
    code_insertion = handle_code_insertion,
    fix_results = handle_fix_results,
    analysis_results = handle_analysis_results,
    refactor_results = handle_refactor_results,
    debug_analysis_results = handle_debug_analysis_results,
    apply_fix = handle_apply_fix,
    verification_results = handle_verification_results,
    chat_response = handle_chat_response,
    ping = handle_ping, -- Add ping handler
}

-- Function to handle data from the server
local function on_read(err, chunk)
    if err then
        notify("Error reading from server: " .. err, vim.log.levels.ERROR)
        M.teardown()
        return
    end

    if chunk then
        local ok, message = pcall(json.decode, chunk)
        if ok and message and message.type and message_dispatch[message.type] then
            notify("Received structured message of type: " .. message.type, vim.log.levels.DEBUG)
            vim.schedule(function()
                message_dispatch[message.type](message.payload)
            end)
        else
            notify("Received raw data from server: " .. chunk, vim.log.levels.INFO)
        end
    else
        notify("Server disconnected.", vim.log.levels.INFO)
        M.teardown()
    end
end

function M.connect()
    if client and not client:is_closing() then
        notify("Already connected or connecting.", vim.log.levels.WARN)
        return
    end

    client = uv.new_tcp()
    notify("Connecting to Python server at " .. config.host .. ":" .. config.port, vim.log.levels.INFO)

    client:connect(config.host, config.port, function(err)
        if err then
            notify("Failed to connect: " .. err, vim.log.levels.ERROR)
            client:close()
            client = nil
            -- Schedule a reconnect attempt
            if reconnect_timer == nil then
                reconnect_timer = uv.new_timer()
            end
            reconnect_timer:start(config.reconnect_interval, 0, function()
                reconnect_timer:stop()
                reconnect_timer:close()
                reconnect_timer = nil
                M.connect()
            end)
            return
        end

        notify("Successfully connected to Python server.", vim.log.levels.INFO)
        client:read_start(on_read)
    end)
end

function M.setup(opts)
    opts = opts or {}
    config = vim.tbl_deep_extend("force", default_config, opts)

    M.connect()

    vim.api.nvim_create_user_command("OllamaSend", function(args)
        local message = args.args
        if client and not client:is_closing() then
            client:write(message .. "\n")
            notify("OllamaSend: Sent message '" .. message .. "' to Python client.", vim.log.levels.INFO)
        else
            notify("OllamaSend: No Python client connected to send message.", vim.log.levels.WARN)
        end
    end, { nargs = 1, desc = "Send a message to the Ollama Python bridge" })
end

function M.send_message(message)
    if client and not client:is_closing() then
        client:write(json.encode(message) .. "\n")
        return true
    else
        notify("Not connected to Python server.", vim.log.levels.WARN)
        return false
    end
end

function M.send_code(action)
    local selection = M.get_visual_selection()
    if selection == nil then
        notify("No text selected.", vim.log.levels.WARN)
        return
    end

    local message = {
        action = action,
        code = selection,
        context = {
            filepath = vim.api.nvim_buf_get_name(0),
            cursor = vim.api.nvim_win_get_cursor(0),
        }
    }
    if M.send_message(message) then
        notify("Sent " .. action .. " request to Python client.", vim.log.levels.INFO)
    end
end

function M.send_refactor_request(query)
    local message = {
        action = "refactor",
        query = query,
    }
    if M.send_message(message) then
        notify("Sent refactor request to Python client.", vim.log.levels.INFO)
    end
end

function M.send_debug_analysis_request(debug_context_query)
    local message = {
        action = "debug_analysis",
        query = debug_context_query,
        code = M.get_visual_selection(),
        context = {
            filepath = vim.api.nvim_buf_get_name(0),
            cursor = vim.api.nvim_win_get_cursor(0),
        }
    }
    if M.send_message(message) then
        notify("Sent debug analysis request to Python client.", vim.log.levels.INFO)
    end
end

function M.get_visual_selection()
    local _, start_row, start_col, _ = unpack(vim.fn.getpos("'<"))
    local _, end_row, end_col, _ = unpack(vim.fn.getpos("'>"))
    if start_row == 0 then
        return nil
    end
    local lines = vim.api.nvim_buf_get_lines(0, start_row - 1, end_row, false)
    if #lines == 0 then
        return nil
    end
    if #lines == 1 then
        lines[1] = string.sub(lines[1], start_col, end_col)
    else
        lines[#lines] = string.sub(lines[#lines], 1, end_col)
        lines[1] = string.sub(lines[1], start_col)
    end
    return table.concat(lines, "\n")
end

function M.teardown()
    if reconnect_timer then
        reconnect_timer:stop()
        reconnect_timer:close()
        reconnect_timer = nil
    end
    if client then
        client:close()
        client = nil
        notify("Disconnected from Python server.", vim.log.levels.INFO)
    end
end

function M.send_buffer_and_cursor_updates()
    if client and not client:is_closing() then
        local bufnr = vim.api.nvim_get_current_buf()
        local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)
        local content = table.concat(lines, "\n")
        local cursor = vim.api.nvim_win_get_cursor(0)

        local buffer_message = {
            type = "buffer_update",
            payload = {
                content = content,
                filepath = vim.api.nvim_buf_get_name(bufnr)
            }
        }
        local cursor_message = {
            type = "cursor_update",
            payload = {
                row = cursor[1],
                col = cursor[2]
            }
        }
        M.send_message(buffer_message)
        M.send_message(cursor_message)
    end
end

function M.send_diagnostics_to_python()
    if client and not client:is_closing() then
        local bufnr = vim.api.nvim_get_current_buf()
        local diagnostics = vim.diagnostic.get(bufnr)
        local filepath = vim.api.nvim_buf_get_name(bufnr)

        local formatted_diagnostics = {}
        for _, diag in ipairs(diagnostics) do
            table.insert(formatted_diagnostics, {
                line = diag.lnum + 1,
                column = diag.col + 1,
                message = diag.message,
                severity = vim.diagnostic.severity[diag.severity] or "info",
                source = diag.source or "nvim",
            })
        end

        local message = {
            type = "neovim_diagnostics",
            payload = {
                filepath = filepath,
                diagnostics = formatted_diagnostics
            }
        }
        if M.send_message(message) then
            notify(string.format("Sent %d diagnostics to Python for %s.", #diagnostics, filepath), vim.log.levels.INFO)
        end
    end
end

return M
