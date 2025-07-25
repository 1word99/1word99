-- neovim_integration/code_actions.lua

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
  vim.api.nvim_create_user_command('OsmanliCodeAction', function(opts)
    local action = opts.fargs[1]
    local file_path = vim.api.nvim_buf_get_name(0)
    local content = table.concat(vim.api.nvim_buf_get_lines(0, 0, -1, false), '\n')

    local cmd
    if action == 'refactor' then
      cmd = string.format('python -c "from osmanli_ai.core.code_actions import CodeActions; ca = CodeActions(); print(ca.suggest_refactoring('''%s'''))" ', content)
    elseif action == 'optimize' then
      cmd = string.format('python -c "from osmanli_ai.core.code_actions import CodeActions; ca = CodeActions(); print(ca.suggest_optimizations('''%s'''))" ', content)
    else
      vim.api.nvim_echo({{'Invalid action. Use refactor or optimize.', 'ErrorMsg'}}, false, {})
      return
    end

    vim.fn.jobstart(cmd, {
      on_stdout = function(_, data)
        open_floating_win(data, "Code Action Suggestion")
      end,
      on_stderr = function(_, data)
        open_floating_win(data, "Error")
      end,
    })
  end, {nargs = 1})
end

return M

