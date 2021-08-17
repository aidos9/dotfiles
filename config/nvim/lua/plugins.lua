return require('packer').startup(function()
	-- Packer can manage itself
  	use 'wbthomason/packer.nvim'

	use 'neovim/nvim-lspconfig'
	use { 'nvim-treesitter/nvim-treesitter', run = ':TSUpdate' }
	use 'sheerun/vim-polyglot'
	use 'hrsh7th/nvim-compe'

	use 'nvim-lua/popup.nvim'
	use 'nvim-lua/plenary.nvim'
	use 'nvim-lua/telescope.nvim'
	use 'nvim-lua/lsp_extensions.nvim'
	use 'jremmen/vim-ripgrep'

	-- Debugging
	use 'mfussenegger/nvim-dap'

	use {
		'romgrk/barbar.nvim',
		requires = {'kyazdani42/nvim-web-devicons'}
	}

	use {
		"folke/trouble.nvim",
		requires = "kyazdani42/nvim-web-devicons",
		config = function()
			require("trouble").setup {
			}
		end
	}
end)
