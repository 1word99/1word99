-- neovim_integration/terminal_bridge.lua

local M = {}

local function open_floating_win(content, title)
  local width = vim.api.nvim_get_option("columns")
  local height = vim.api.nvim_get_option("lines")

  local win_width = math.floor(width * 0.8)
  local win_height = math.floor(height * 0.8)

  local row = math.floor((height - win_height) / 2)
  local col = math.floor((width - win_width) / 2)

  local buf = vim.api.nvim_create_buf(false, true)
  vim.api.nvim_buf_set_lines(buf, 0, -1, false, content)

  local win = vim.api.nvim_open_win(buf, true, {
    relative = "editor",
    width = win_width,
    height = win_height,
    row = row,
    col = col,
    style = "minimal",
    border = "rounded",
    title = title,
  })
end

function M.setup()
  vim.api.nvim_create_user_command('OsmanliTerminal', function(opts)
    local cmd = table.concat(opts.fargs, " ")
    vim.fn.jobstart('python -c "from osmanli_ai.core.terminal_integration import TerminalIntegration; term = TerminalIntegration(); print(term.execute(\\'" .. cmd .. "\\'))" ', {
      on_stdout = function(_, data)
        open_floating_win(data, "Output of: " .. cmd)
      end,
      on_stderr = function(_, data)
        open_floating_win(data, "Error of: " .. cmd)
      end,
    })
  end, {nargs = '+'})
end

return M
