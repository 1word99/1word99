local M = {}

function M.diagnose()
    local diagnostics = vim.diagnostic.get(0)
    if #diagnostics > 0 then
        vim.api.nvim_buf_set_lines(0, -1, -1, false, {
            "🧠 [AI MIND ACTIVATED]",
            "Diagnosing " .. vim.fn.expand('%'),
            "Found " .. #diagnostics .. " issues"
        })
        vim.cmd('write')  -- Auto-save fixes
        return true
    end
    return false
end

return M
