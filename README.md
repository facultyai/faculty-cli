# faculty-cli

`faculty` is the command line interface to the [Faculty platform](https://faculty.ai/products-services/platform/).

## Enabling shell autocompletion

`faculty` provides autocompletion support for Bash, Zsh and Fish. 

Below are the procedures to set up autocompletion for each shell. 

## Bash

The `faculty` completion script for Bash can be generated with the command 
`faculty completion bash`. Sourcing the completion script in your shell 
enables autocompletion. However, the completion script depends on 
`bash-completion`. To test if you have `bash-completion` already installed 
, run `type _init_completion`. 


### Install `bash-completion`

#### Linux

`bash-completion` is provided by many package managers. You can install it 
with `apt-get install bash-completion` or `yum install bash-completion`, etc.

The above commands create `/usr/share/bash-completion/bash_completion`, which 
is the main script of `bash-completion`. Depending on your package manager, you 
have to manually source this file in your `~/.bashrc` file.

To find out, reload your shell and run `type _init_completion`. If the command 
succeeds, you’re already set, otherwise add the following to your `~/.bashrc`
file:

```
source /usr/share/bash-completion/bash_completion
```

Reload your shell and verify that bash-completion is correctly installed by 
typing `type _init_completion`.

### Enable autocompletion

You now need to ensure that the kubectl completion script gets sourced in all 
your shell sessions. To do this add the following to your `~/.bashrc` file: 


```
source <(faculty completion bash)
```

After reloading your shell, `faculty` autocompletion should be working.

## Zsh

The faculty completion script for Zsh can be generated with the command 
`faculty completion zsh`. Sourcing the completion script in your shell enables 
autocompletion. To do so in all your shell sessions, add the following to your 
`~/.zshrc` file:

```
source <(faculty completion zsh)
```

After reloading your shell, `faculty` autocompletion should be working.

If you get an error like `command not found: compdef`, then add the following 
to the beginning of your `~/.zshrc` file:

```
autoload -Uz compinit && compinit
```

## Fish

The faculty completion script for Fish can be generated with the command 
`faculty completion fish`.

```
faculty completion fish | source
```


>>>>>>> Update README with autocomplete instructions
