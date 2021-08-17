-- Load plugins
require('plugins')

local g = vim.g
local o = vim.o
local bo = vim.bo
local wo = vim.wo

o.termguicolors = true
o.syntax = 'on'
o.errorbells = false
o.smartcase = true
o.showmode = true
bo.autoindent = true
bo.smartindent = true

o.tabstop = 4
o.softtabstop = 4
o.shiftwidth = 4
o.expandtab = true
wo.number = true
wo.wrap = true
wo.signcolumn = 'yes'

g.updatetime = 300
-- Sets the key that is used for plugins, here it is a backslash
vim.g.mapleader = '\\'


-- Configure Tree-Sitter
local configs = require('nvim-treesitter.configs')

configs.setup {
    ensure_installed = { 'bash', 'c', 'c_sharp', 'cmake', 'html', 'cpp', 'css', 'dockerfile', 'fish', 'java', 'javascript', 'json', 'lua', 'php', 'python', 'rust', 'ruby', 'toml' },
    ignore_install = { 'zig' }, 
    highlight = {
        enable = true,
    }
}

-- Configure LSP and Autocomplete
-- Required for nvim-compe
vim.o.completeopt = "menuone,noselect"

local lspconfig = require('lspconfig')

require('compe').setup {
    enabled = true,
    autocomplete = true,
    debug = false,
    min_length = 1,
    preselect = 'enable',
    throttle_time = 80;
    source_timeout = 200;
    resolve_timeout = 800;
    incomplete_delay = 400;
    max_abbr_width = 100;
    max_kind_width = 100;
    max_menu_width = 100;
    documentation = {
      border = { '', '' ,'', ' ', '', '', '', ' ' }, -- the border option is the same as `|help nvim_open_win|`
      winhighlight = "NormalFloat:CompeDocumentation,FloatBorder:CompeDocumentationBorder",
      max_width = 120,
      min_width = 60,
      max_height = math.floor(vim.o.lines * 0.3),
      min_height = 1,
    };

    source = {
      path = true;
      buffer = true;
      calc = true;
      nvim_lsp = true;
      nvim_lua = true;
      vsnip = false;
      ultisnips = false;
      luasnip = false;
    };
}

require('lspconfig').rust_analyzer.setup({})

vim.lsp.handlers["textDocument/publishDiagnostics"] = vim.lsp.with(
  vim.lsp.diagnostic.on_publish_diagnostics, {
    virtual_text = true,
    signs = true,
    underline = true,
  }
)

-- Keymaps
vim.api.nvim_set_keymap('i', '<Tab>', 'pumvisible() ? "\\<C-n>" : "\\<Tab>"', {expr = true})
vim.api.nvim_set_keymap('i', '<C-Space>', 'compe#complete()', { expr = true, silent = true})
vim.api.nvim_set_keymap('i', '<CR>', 'compe#confirm("<CR>")', { expr = true, silent = true})

vim.api.nvim_set_keymap("n", "<leader>xx", "<cmd>Trouble<cr>",
  {silent = true, noremap = true}
)
vim.api.nvim_set_keymap("n", "<leader>xw", "<cmd>Trouble lsp_workspace_diagnostics<cr>",
  {silent = true, noremap = true}
)
vim.api.nvim_set_keymap("n", "<leader>xd", "<cmd>Trouble lsp_document_diagnostics<cr>",
  {silent = true, noremap = true}
)
vim.api.nvim_set_keymap("n", "<leader>xq", "<cmd>Trouble quickfix<cr>",
  {silent = true, noremap = true}
)
vim.api.nvim_set_keymap("n", "gR", "<cmd>Trouble lsp_references<cr>",
  {silent = true, noremap = true}
)

-- Code navigation shortcuts
vim.api.nvim_set_keymap("n", "<c-]>", "<cmd>lua vim.lsp.buf.definition()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "K", "<cmd>lua vim.lsp.buf.hover()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "gD", "<cmd>lua vim.lsp.buf.implementation()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "<c-k>", "<cmd>lua vim.lsp.buf.signature_help()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "1gD", "<cmd>lua vim.lsp.buf.type_definition()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "gr", "<cmd>lua vim.lsp.buf.references()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "g0", "<cmd>lua vim.lsp.buf.document_symbol()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "gW", "<cmd>lua vim.lsp.buf.workspace_symbol()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "gd", "<cmd>lua vim.lsp.buf.declaration()<CR>", { silent = true, noremap = true })
vim.api.nvim_set_keymap("n", "ga", "<cmd>lua vim.lsp.buf.code_action()<CR>", { silent = true, noremap = true })


vim.api.nvim_exec([[autocmd CursorMoved,InsertLeave,BufEnter,BufWinEnter,TabEnter,BufWritePost * lua require('lsp_extensions').inlay_hints{ prefix = '', highlight = "Comment", enabled = {"TypeHint", "ChainingHint", "ParameterHint"} }]], false)
-- Show diagnostic popup on cursor hold
vim.api.nvim_exec([[autocmd CursorHold * lua vim.lsp.diagnostic.show_line_diagnostics()]], false)

