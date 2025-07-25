# Osmanli AI Neovim Integration

This directory contains the Lua scripts required to connect Neovim to the Osmanli AI backend.

## Features

- **Code Actions**: Send selected code to the AI for explanation, completion, fixing, or analysis.
- **Chat**: Open an interactive chat window with the AI.
- **Refactoring**: Send refactoring requests.
- **Live Diagnostics**: Receive real-time diagnostics from the AI as you type.

## Setup

1.  **Ensure you have a modern Neovim version (0.8+) installed.**

2.  **Place this `nvim_integration` directory somewhere accessible to Neovim.** A good location is inside your Neovim configuration directory (e.g., `~/.config/nvim/`).

3.  **Source the `init.lua` from your main Neovim configuration.**

    Add the following line to your `init.lua` (or `init.vim`):

    **For `init.lua`:**
    ```lua
    -- Make sure to adjust the path to where you placed the nvim_integration directory
    require("nvim_integration") 
    ```

    **For `init.vim`:**
    ```vim
    " Make sure to adjust the path to where you placed the nvim_integration directory
    lua require("nvim_integration")
    ```

4.  **Start the Osmanli AI Backend.**

    Run the main application from the project root:
    ```bash
    python main.py --interface=none
    ```
    The `--interface=none` flag keeps the backend running in headless mode. The Neovim bridge will be active.

## Default Keymaps

-   `<leader>ae`: **E**xplain selected code.
-   `<leader>ac`: **C**omplete selected code.
-   `<leader>af`: **F**ix selected code.
-   `<leader>aa`: **A**nalyze selected code.

## Commands

-   `:OsmanliChat`: Open the AI chat window.
-   `:OsmanliRefactor <your query>`: Send a refactoring request.
-   `:OsmanliGenerateTests`: Generate tests for the selected code.
