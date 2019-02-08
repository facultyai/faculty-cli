# faculty-cli

`faculty` is the command line interface to the [Faculty platform](https://sherlockml.com). <!-- TODO Change link destination -->

## Enable tab completion for bash, fish, or zsh

`faculty` supports generating completion scripts for `bash`, `fish`, and `zsh`. 

```bash
# Bash
faculty completions bash > /etc/bash_completion.d/faculty.bash-completion

# Bash (macOS/Homebrew)
faculty completions bash > $(brew --prefix)/etc/bash_completion.d/faculty.bash-completion

# Fish
faculty completions fish > ~/.config/fish/completions/faculty.fish

# Zsh
faculty completions zsh > ~/.zfunc/_faculty
```

You may need to restart your shell in order for the changes to take effect.

For `zsh`, you must then add the following line in your `~/.zshrc` before
`compinit`:

```zsh
fpath+=~/.zfunc
```
