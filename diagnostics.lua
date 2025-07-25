-- neovim_integration/diagnostics.lua

local M = {}

local function refresh_diagnostics()
  local file_path = vim.api.nvim_buf_get_name(0)
  local cmd = string.format('python -c "from osmanli_ai.core.language_server import LanguageServer; ls = LanguageServer(); print(ls.get_diagnostics(\"%s\"))" ', file_path)

  vim.fn.jobstart(cmd, {
    on_stdout = function(_, data)
      local diagnostics = vim.fn.json_decode(table.concat(data, ""))
      vim.diagnostic.set(0, "osmanli_ai", diagnostics, {})
    end,
    on_stderr = function(_, data)
      vim.api.nvim_echo({{'Error getting diagnostics:\n' .. table.concat(data, '\n'), 'ErrorMsg'}}, false, {})
    end,
  })
end

function M.setup()
  vim.api.nvim_create_augroup("OsmanliDiagnostics", { clear = true })
  vim.api.nvim_create_autocmd({"BufWritePost"}, {
    group = "OsmanliDiagnostics",
    pattern = "*.py", -- Or other file types
    callback = refresh_diagnostics,
  })
end

return M
