"""Autocompletion support for Bash, Zsh and Fish."""

# Copyright 2016-2019 Faculty Science Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

bash_script = r"""_complete() {

    local cur="${COMP_WORDS[COMP_CWORD]}"

    COMPREPLY=()

    if [[ ${cur} == * ]]; then
        COMPREPLY=($(compgen -W "${1}" -- ${cur}))
        return 0
    fi
}

_complete_path() {
    
    local cur="${COMP_WORDS[COMP_CWORD]}"

    COMPREPLY=()
    if [[ ${cur} == * ]]; then
        _filedir
        return 0
    fi
    
}
_complete_newlinesep() {

    local cur="${COMP_WORDS[COMP_CWORD]}"
    local IFS=$'\n'
    COMPREPLY=()

    if [[ ${cur} == * ]]; then
        COMPREPLY=($(compgen -W "${1}" -- ${cur}))
        return 0
    fi
}

_get_projects() {
    faculty project list 2>/dev/null
}

_get_servers() {
    faculty server list "$1" 2>/dev/null
}

_get_environments() {
    faculty environment list "$1" 2>/dev/null
}

_get_jobs() {
    faculty job list "$1" 2>/dev/null
}

_get_job_runs() {
    faculty job list-runs "$1" "$2" 2>/dev/null
}

_add_double_quotes() {
    case $1 in
    *\ *)
        echo "\"$1\""
        ;;
    *)
        echo $1
        ;;
    esac
}

_add_double_quotes_to_compreply() {

    local clength i
    clength=${#COMPREPLY[@]}
    for ((i = 0; i < clength; i++)); do
        COMPREPLY[$i]=$(_add_double_quotes ${COMPREPLY[i]})
    done
    return 0
}

_complete_project() {

    local opts=$(_get_projects)
    local IFS=$'\n'
    _complete_newlinesep "$opts"
    _add_double_quotes_to_compreply

    return 0
}

_remove_double_quotes() {

    s=$1
    s="${s%\"}"
    s="${s#\"}"
    echo $s
}

_complete_server() {

    local project=$(_remove_double_quotes "$1")
    local opts=$(_get_servers "$project")
    _complete_newlinesep "$opts"
    _add_double_quotes_to_compreply

    return 0
}

_complete_environment() {

    local project=$(_remove_double_quotes "$1")
    local opts=$(_get_environments "$project")
    _complete_newlinesep "$opts"
    _add_double_quotes_to_compreply

    return 0
}

_complete_job() {

    local project=$(_remove_double_quotes "$1")
    local opts=$(_get_jobs "$project")
    local IFS=$'\n'
    _complete_newlinesep "$opts"
    _add_double_quotes_to_compreply

    return 0
}

_complete_job_run() {

    local project=$(_remove_double_quotes "$1")
    local job=$(_remove_double_quotes "$2")
    local opts=$(_get_job_runs "$project" "$job")
    echo $project

    return 0
}

_faculty() {
    if [[ $COMP_CWORD -eq 1 ]]; then
        _complete "environment file home login project server shell version completion job"
    fi

    if [[ $COMP_CWORD -gt 1 ]]; then
        local base="${COMP_WORDS[1]}"

        case $base in
        "shell")

            if [[ $COMP_CWORD -eq 2 ]]; then _complete_project; fi
            if [[ $COMP_CWORD -eq 3 ]]; then
                local project=${COMP_WORDS[2]}
                _complete_server "$project"
            fi
            ;;

        "server")
            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "list new open terminate"
            fi
            if [[ $COMP_CWORD -eq 3 ]]; then
                _complete_project
            fi
            if [[ $COMP_CWORD -eq 4 ]]; then
                local selection=${COMP_WORDS[2]}

                case $selection in
                terminate)
                    local project=${COMP_WORDS[3]}
                    _complete_server "$project"
                    ;;
                open)
                    _complete "--server"
                    ;;
                esac
            fi
            if [[ $COMP_CWORD -eq 5 ]]; then
                local selection=${COMP_WORDS[2]}
                if [[ $selection == open ]]; then
                    local project=${COMP_WORDS[3]}
                    _complete_server "$project"
                fi
            fi
            ;;

        "environment")

            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "apply list logs status"
            fi
            if [[ $COMP_CWORD -eq 3 ]]; then
                _complete_project
            fi
            if [[ $COMP_CWORD -eq 4 ]]; then
                local project=${COMP_WORDS[3]}
                _complete_server "$project"
            fi
            if [[ $COMP_CWORD -eq 5 ]]; then
                local selection=${COMP_WORDS[2]}
                if [[ $selection == apply ]]; then
                    local project=${COMP_WORDS[3]}
                    _complete_environment "$project"
                fi
            fi
            ;;
        
        "file")

            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "get put sync-down sync-up"
            fi
            if [[ $COMP_CWORD -eq 3 ]]; then
                _complete_project 
            fi
            if [[ $COMP_CWORD -eq 4 ]]; then
                local selection=${COMP_WORDS[2]}
                case $selection in
                "put"|"sync-up")
                    _complete_path
                    ;;
                esac
            fi
            if [[ $COMP_CWORD -eq 5 ]]; then
                local selection=${COMP_WORDS[2]}
                case $selection in
                "get"|"sync-down")
                    _complete_path
                    ;;
                esac
            fi
            ;;
        
        "completion")

            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "bash zsh fish"
            fi
            ;;        
            
        "project")

            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "list"
            fi
            ;;     
            
        "job")

            if [[ $COMP_CWORD -eq 2 ]]; then
                _complete "list list-runs logs run"
            fi
            if [[ $COMP_CWORD -eq 3 ]]; then
                _complete_project 
            fi
            if [[ $COMP_CWORD -eq 4 ]]; then
                local project=${COMP_WORDS[3]}
                _complete_job "$project"
            fi
            if [[ $COMP_CWORD -eq 5 ]]; then
                local selection=${COMP_WORDS[2]}
                if [[ $selection == logs ]]; then
                    local project=${COMP_WORDS[3]}
                    local job=${COMP_WORDS[4]}
                    _complete_job_run "$project" "$job"
                fi
            fi
            ;;     
            
        esac
        return 0
    fi
}

complete -F _faculty faculty
"""


fish_script = r"""function __fish_faculty_list_projects
    command faculty project list 2>/dev/null
end

function __fish_faculty_list_all_servers_verbose
    set cmd (commandline -opc)
    command faculty server list $cmd[-1] --all --verbose 2>/dev/null | tail -n +2 
end

function __fish_faculty_list_environments
    set cmd (commandline -opc)
    command faculty environment list $cmd[-2] 2>/dev/null
end

function __fish_faculty_list_jobs
    set cmd (commandline -opc)
    command faculty job list $cmd[-1] 2>/dev/null 
end

function __fish_faculty_list_runs
    set cmd (commandline -opc)
    command faculty job list-runs $cmd[-2] $cmd[-1] 2>/dev/null
end

function __fish_faculty_list_instance_types
    command faculty server instance-types 2>/dev/null
end

function __fish_faculty_list_instance_types_verbose
    command faculty server instance-types --verbose 2>/dev/null | tail -n +2
end

function __fish_faculty_dirname
    if test -z "$argv[1]" -o $argv[1] = '/project'
        set p '/project/'
    else
        if test (string sub $argv[1] --start -1 = '/')
            set p $argv[1]
        else
            set p (dirname $argv[1])/
        end
    end
    echo $p
end

function __fish_faculty_remote_path_completions
    set cmd (commandline -opc)
    set p (__fish_faculty_dirname (echo (commandline -ct) | sed -e 's/\\\ / /g'))
    faculty file ls $cmd[4] $p
end

function __fish_faculty_local_path_completions
    set p (echo (commandline -ct) | sed -e 's/\\\ / /g')
    __fish_complete_path $p
end

# common options

complete -c faculty -x
complete -c faculty -l help -d 'Display help and exit.'

# list available servers, when server is an option (i.e. --server)
# this assumes the Project is in the fourth position

function __fish_faculty_server_is_option
    set cmd (commandline -opc)
    if [ (count $cmd) -ge 1 ]
        and [ $cmd[-1] = '--server' ]
        return 0
    end
    return 1
end

function __fish_faculty_list_servers_if_option
    set cmd (commandline -opc)
    command faculty server list $cmd[4] --verbose --all 2>/dev/null | tail -n +2
end

complete -c faculty -n "__fish_faculty_server_is_option" -x -a '(string split "\n" (__fish_faculty_list_servers_if_option) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'

# list available environments, when environment is an option (i.e. --environment)
# this assumes the Project is in the fourth position

function __fish_faculty_environment_is_option
    set cmd (commandline -opc)
    if [ (count $cmd) -ge 1 ]
        and [ $cmd[-1] = '--environment' ]
        return 0
    end
    return 1
end

function __fish_faculty_list_environments_if_option
    set cmd (commandline -opc)
    command faculty environment list $cmd[4]
end

complete -c faculty -n "__fish_faculty_environment_is_option" -x -a "(__fish_faculty_list_environments_if_option)"

# list available server types, when type is an option (i.e. --type)

function __fish_faculty_type_is_option
    set cmd (commandline -opc)
    if [ (count $cmd) -ge 1 ]
        and [ $cmd[-1] = '--type' ]
        return 0
    end
    return 1
end

complete -c faculty -n "__fish_faculty_type_is_option" -x -a "jupyter jupyterlab rstudio"

# list available machine types, when machine-type is an option (i.e. --machine-type)

function __fish_faculty_machine_type_is_option
    set cmd (commandline -opc)
    if [ (count $cmd) -ge 1 ]
        and [ $cmd[-1] = '--machine-type' ]
        return 0
    end
    return 1
end

complete -c faculty -n "__fish_faculty_machine_type_is_option" -x -a '(string split "\n" (__fish_faculty_list_instance_types_verbose) | awk -F\' \' \'{ print $1 "\t" "CPUs: " $2 ", Ram: " $3 " GB, GPUs: " $5 ", Cost: $" $(NF-2) " / hr" }\')'

# environment

complete -c faculty -n "__fish_is_first_token" -a environment -d "Manipulate Faculty server environments."

complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_is_token_n 3" -x -a apply -d "Apply an environment to the server."
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from apply; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from apply; and __fish_is_token_n 5" -x -a '(string split "\n" (__fish_faculty_list_servers_if_option) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from apply; and __fish_is_token_n 6" -x -a "(__fish_faculty_list_environments)"

complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_is_token_n 3" -x -a list -d "List your environments."
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from list; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from list" -s v -l verbose -d "Print extra information about environments."

complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_is_token_n 3" -x -a logs -d "Stream the logs for a server environment application."
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from logs; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from logs; and __fish_is_token_n 5" -x -a '(string split "\n" (__fish_faculty_list_servers_if_option) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from logs" -s s -l step -d "Display only the logs for this step."

complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_is_token_n 3" -x -a status -d "Get the execution status for an environment."
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from status; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from environment; and __fish_seen_subcommand_from status; and __fish_is_token_n 5" -x -a '(string split "\n" (__fish_faculty_list_servers_if_option) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'

# file

complete -c faculty -n "__fish_is_first_token" -a file -d "Manipulate files in a Faculty project."

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 3" -x -a get -d "Copy a file from the Faculty workspace to the local machine."
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from get; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from get; and __fish_is_token_n 5" -a '(__fish_faculty_remote_path_completions)'
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from get; and __fish_is_token_n 6" -a '(__fish_faculty_local_path_completions)'

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 3" -x -a put -d "Copy a local file to the Faculty workspace."
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from put; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from put; and __fish_is_token_n 5" -a '(__fish_faculty_local_path_completions)'
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from put; and __fish_is_token_n 6" -a '(__fish_faculty_remote_path_completions)'

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 3" -x -a sync-down -d "Sync remote files down from project with rsync."
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-down; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-down; and __fish_is_token_n 5" -a '(__fish_faculty_remote_path_completions)'
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-down; and __fish_is_token_n 6" -a '(__fish_faculty_local_path_completions)'

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 3" -x -a sync-up -d "Sync local files up to a project with rsync."
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-up; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-up; and __fish_is_token_n 5" -a '(__fish_faculty_local_path_completions)'
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from sync-up; and __fish_is_token_n 6" -a '(__fish_faculty_remote_path_completions)'

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 3" -x -a ls -d "List files and directories on the Faculty workspace."
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from ls; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_seen_subcommand_from ls; and __fish_is_token_n 5" -a '(__fish_faculty_remote_path_completions)'

complete -c faculty -n "__fish_seen_subcommand_from file; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from file" -l server -d "Name or ID of server to use."

# login

complete -c faculty -n "__fish_is_first_token" -a login -d "Write Faculty credentials to file."

# projects

complete -c faculty -n "__fish_is_first_token" -a projects -d "List accessible Faculty projects."
complete -c faculty -n "__fish_seen_subcommand_from projects" -s v -l verbose -d "Print extra information about projects."

# server

complete -c faculty -n "__fish_is_first_token" -a server -d "Manipulate Faculty servers."

complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_is_token_n 3" -x -a list -d "List your Faculty servers."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from list; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from list" -s v -l verbose -d "Print extra information about servers."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from list" -s a -l all -d "Show all servers, not just running ones."

complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_is_token_n 3" -x -a new -d "Create a new Faculty server."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --cores; and not __fish_seen_subcommand_from --machine-type" -l cores -d "Number of CPU cores  [default: 1]."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --memory; and not __fish_seen_subcommand_from --machine-type" -l memory -d "Server memory in GB  [default: 4]."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --type" -l type -d "Server type  [default: jupyter]."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --machine-type; and not __fish_seen_subcommand_from --cores; and not __fish_seen_subcommand_from --memory" -l machine-type -d "Machine type for a dedicated instance."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --version" -l version -d "Server image version [advanced]."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --name" -l name -d "Name to assign to the server."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --environment" -l environment -d "Environments to apply to the server."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from new; and not __fish_seen_subcommand_from --wait" -l wait -d "Wait until the server is running before exiting."

complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_is_token_n 3" -x -a open -d "Open a Faculty server in your browser."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from open; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from open" -l server -d "Name or ID of server to use."

complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_is_token_n 3" -x -a terminate -d "Terminate a Faculty server."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from terminate; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from terminate; and __fish_is_token_n 5" -x -a '(string split "\n" (__fish_faculty_list_all_servers_verbose) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'

complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_is_token_n 3" -x -a instance-types -d "List the types of servers available on dedicated infrastructure."
complete -c faculty -n "__fish_seen_subcommand_from server; and __fish_seen_subcommand_from instance-types" -s v -l verbose -d "Print extra information about instance types."

# shell

complete -c faculty -n "__fish_is_first_token" -a shell -d "Open a shell on an Faculty server."
complete -c faculty -n "__fish_seen_subcommand_from shell; and __fish_is_token_n 3" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from shell; and __fish_is_token_n 4" -x -a '(string split "\n" (__fish_faculty_list_all_servers_verbose) | awk -F\'[[:space:]][[:space:]]+\' \'{ print $1 "\t" "Type: " $2 ", Machine Type: " $3 ", CPUs: " $4 ", RAM: " $5 ", Status: " $6 ", Started: " $8}\')'

# version

complete -c faculty -n "__fish_is_first_token" -a version -d "Print the faculty version number."

# job

complete -c faculty -n "__fish_is_first_token" -a job -d "Manipulate Faculty jobs."

complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_is_token_n 3" -x -a list -d "List the jobs in a project."
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from list; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from list" -s v -l verbose -d "Print extra information about jobs."

complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_is_token_n 3" -x -a list-runs -d "List the runs of a job."
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from list-runs; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from list-runs; and __fish_is_token_n 5" -x -a "(__fish_faculty_list_jobs)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from list-runs" -s v -l verbose -d "Print extra information about runs."

complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_is_token_n 3" -x -a logs -d "Print the logs for a run."
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from logs; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from logs; and __fish_is_token_n 5" -x -a "(__fish_faculty_list_jobs)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from logs; and __fish_is_token_n 6" -x -a "(__fish_faculty_list_runs)"

complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_is_token_n 3" -x -a run -d "Run a job."
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from run; and __fish_is_token_n 4" -x -a "(__fish_faculty_list_projects)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from run; and __fish_is_token_n 5" -x -a "(__fish_faculty_list_jobs)"
complete -c faculty -n "__fish_seen_subcommand_from job; and __fish_seen_subcommand_from run" -l num-subruns -d "Number of sub runs."
"""


zsh_script = r"""_faculty() {
  local state line
  typeset -A opt_args

  local ret=1

  _arguments -C \
    '1: :_faculty_cmds' \
    '*:: :->args' \
    && ret=0

  case $state in
    (args)
      case $line[1] in
        (environment)
          _arguments -C \
            '1:: :_faculty_environment_cmds' \
            '*:: :->environment-args' && ret=0
        case $state in
          (environment-args)
            case $line[1] in
              (apply)
                _arguments -C \
                  '--help[Display help message.]' \
                  '1:: :_faculty_projects' \
                  '2:: :{_faculty_servers "$line[1]"}' \
                  '3:: :{_faculty_environments "$line[1]"}' \
                && ret=0
              ;;
              (list)
              _arguments -C \
                '(-v --verbose)'{-v,--verbose}'[Print extra information about environments.]' \
                '--help[Display help message.]' \
                '1:: :_faculty_projects' \
              && ret=0
              ;;
              (logs)
              _arguments -C \
                '--help[Display help message.]' \
                '(-s --step)'{-s,--step}'[Display only the logs for this step.]' \
                '1:: :_faculty_projects' \
                '2:: :{_faculty_servers "$line[1]"}' \
              && ret=0
              ;;
              (status)
              _arguments -C \
                '--help[Display help message.]' \
                '1:: :_faculty_projects' \
                '2:: :{_faculty_servers "$line[1]"}' \
              ;;
            esac
          ;;
        esac
      ;;
      (file)
        _arguments -C \
          '1:: :_faculty_file_cmds' \
          '*:: :->file-args' && ret=0
          case $state in
            (file-args)
              case $line[1] in
                (get)
                  _arguments -C \
                    '--help[Display help message.]' \
                    '--server[Name or ID of server to use.]: :{_faculty_servers "$line[1]"}' \
                    '1: :_faculty_projects' \
                    '2: :{_remote "$line[1]" "$line[2]"}' \
                    '3: :_files' \
                  && ret=0
                ;;
                (put)
                _arguments -C \
                  '1: :_faculty_projects' \
                  '2: :_files' \
                  '3:: :{_remote "$line[1]" "$line[3]"}' \
                  '--help[Display help message.]' \
                  '--server[Name or ID of server to use.]: :{_faculty_servers "$line[1]"}' \
                && ret=0
                ;;
                (sync-down)
                _arguments -C \
                  '--help[Display help message.]' \
                  '--server[Name or ID of server to use.]: :{_faculty_servers "$line[1]"}' \
                  '1: :_faculty_projects' \
                  '2: :{_remote "$line[1]" "$line[2]"}' \
                  '3: :_files' \
                && ret=0
                ;;
                (sync-up)
                _arguments -C \
                  '1: :_faculty_projects' \
                  '2: :_files' \
                  '3: :{_remote "$line[1]" "$line[3]"}' \
                  '--help[Display help message.]' \
                  '--server[Name or ID of server to use.]: :{_faculty_servers "$line[1]"}' \
                && ret=0
		;; 
                (ls)
                _arguments -C \
                  '1: :_faculty_projects' \
                  '2: :{_remote "$line[1]" "$line[2]"}' \
                  '--help[Display help message.]' \
                && ret=0
		;; 
              esac
            ;;
          esac
        ;;
        (job)
        _arguments -C \
          '1:: :_faculty_job_cmds' \
          '*:: :->job-args' && ret=0
          case $state in
            (job-args)
              case $line[1] in
                (list)
                  _arguments -C \
                    '--help[Display help message.]' \
                    '(-v --verbose)'{-v,--verbose}'[Print extra information about jobs.]' \
                    '1: :_faculty_projects' \
                  && ret=0
                ;;
                (list-runs)
                _arguments -C \
                  '--help[Display help message.]' \
                  '(-v --verbose)'{-v,--verbose}'[Print extra information about runs.]' \
                  '1: :_faculty_projects' \
                  '2:: :{_faculty_jobs "$line[1]"}' \
                && ret=0
                ;;
                (logs)
                _arguments -C \
                  '--help[Display help message.]' \
                  '1: :_faculty_projects' \
                  '2:: :{_faculty_jobs "$line[1]"}' \
                  '3: :{_faculty_runs "$line[1]" "$line[2]"}' \
                && ret=0
                ;;
                (run)
                _arguments -C \
                  '--help[Display help message.]' \
                  '--num-subruns[Number of sub runs.]' \
                  '1: :_faculty_projects' \
                  '2:: :{_faculty_jobs "$line[1]"}' \
                ;;
              esac
            ;;
          esac
        ;;
        (login|version)
          _message 'No more arguments' && ret=0
        ;;
        (projects)
        _arguments \
          '(-v --verbose)'{-v,--verbose}'[Print extra information about projects.]' \
          "--help[Display help message.]" && ret=0
        ;;
        (server)
          _arguments -C \
            '1:: :_faculty_server_cmds' \
            '*:: :->server-args' && ret=0
          case $state in
              (server-args)
                 case $line[1] in
                   (list)
                     _arguments -C \
                       '--help[Display help message.]' \
                       '(-a --all)'{-a,--all}'[Show all servers]' \
                       '(-v --verbose)'{-v,--verbose}'[Print extra information about servers.]' \
                       '1:: :_faculty_projects' \
                       && ret=0
                   ;;
                   (new)
                      _arguments -C \
                        '--cores[Number of CPU cores]: :_cores' \
                        '--memory[Server memory in GB]: :_memory' \
                        '--type[Server type (default: jupyter)]: :_server_type' \
                        '--version[Server image version]: :_server_image_version' \
                        '--name[Name to assign to the server]: :_server_name' \
                        '--environment[Environments to apply to the server]: :{_faculty_environments "$line[1]"}' \
                        '--wait[Wait until the server is running before exiting]' \
                        '--help[Display help message]' \
			'--machine-type[Machine type for a dedicated instance]: :_node_type' \
                        '1:: :_faculty_projects' \
                        && ret=0
                  ;;
                  (open)
                     _arguments -C \
                       '--server[Name or ID of server to use.]: :{_faculty_servers "$line[1]"}' \
                       '--help[Display help message.]' \
                       '1:: :_faculty_projects' \
                       && ret=0
                 ;;
                 (terminate)
                   _arguments -C \
                     '--help[Display help message.]' \
                     '1:: :_faculty_projects' \
                     '2:: :{_faculty_servers "$line[1]"}' \
                     && ret=0
                 ;;
	        (instance-types)
                _arguments -C \
                  '--help[Display help message.]' \
                  '(-v --verbose)'{-v,--verbose}'[Print extra information about instance types.]' \
		&& ret=0
		;;  
              esac
            ;;
        esac
        ;;
        (shell)
          _arguments \
            '--help[Display help message.]' \
            '1:: :_faculty_projects' \
            '2:: :{_faculty_servers "$line[1]"}' \
          && ret=0
        ;;
      esac
      case $line[2] in
        (list|new|open|terminate)
           _message 'No more arguments' && ret=0
      ;;
      esac
  ;;
  esac
}


_faculty_cmds() {
  local commands; commands=(
    'environment:Manipulate Faculty server environments.'
    'file:Manipulate files in a Faculty project.'
    'job:Manipulate Faculty jobs.'
    'login:Write Faculty credentials to file.'
    'projects:List accessible Faculty projects.'
    'server:Manipulate Faculty servers.'
    'shell:Open a shell on an Faculty server.'
    'version:Print the faculty version number.'
    '--help:Display help message.'
  )
  _describe 'command' commands
}

_faculty_environment_cmds() {
  local commands; commands=(
    'apply:Apply an environment to the server.'
    'list:List your environments.'
    'logs:Stream the logs for a server environment.'
    'status:Get the execution status for an environment.'
    '--help:Display help message.'
  )
  _describe 'command' commands
}

_faculty_file_cmds() {
  local commands; commands=(
    'get:Copy a file from the Faculty workspace to the local machine.'
    'put:Copy a local file to the Faculty workspace.'
    'sync-down:Sync remote files down from project with rsync.'
    'sync-up:Sync local files up to a project with rsync.'
    'ls:List files and directories on the Faculty workspace.'
    '--help:Display help message.'
  )
  _describe 'command' commands
}

_faculty_job_cmds() {
  local commands; commands=(
    'list:List the jobs in a project.'
    'list-runs:List the runs of a job.'
    'logs:Print the logs for a run.'
    'run:Run a job.'
    '--help:Display help message.'
  )
  _describe 'command' commands
}

_faculty_server_cmds() {
  local commands; commands=(
    'list:List your Faculty servers.'
    'new:Create a new Faculty server.'
    'open:Open a Faculty server in your browser.'
    'terminate:Terminate a Faculty server.'
    'instance-types:List the types of servers available on dedicated infrastructure.'
    '--help:Display help message.'
  )
  _describe 'command' commands
}

_remote() {
  
  _remote_path_suggestions ${1//\\ /\ } ${2//\\ /\ }
  IFS=$'\n' SML_REMOTE_PATH_SUGGESTIONS=($(echo $SML_REMOTE_PATH_SUGGESTIONS))

  local files=()
  local directories=()
  local files_display=()
  local directories_display=()

  for item in ${SML_REMOTE_PATH_SUGGESTIONS[@]}; do
    if [ ${${:-$item}[-1]} = "/" ]; then
      files+=($item)
      files_display+=($item:t/)
    else
      directories+=($item)
      directories_display+=($item:t)
    fi
  done

  compadd  -d files_display $( IFS=' ' echo "${files[*]}" )
  compadd  -q -S/ -d directories_display $( IFS=' ' echo "${directories[*]}" )

}

_cores() {
  _message 'Number of CPU cores (default 1; max 32).'
}

_memory() {
  _message 'Server memory in GB (default 4; max 64).'
}

_server_name() {
  _message 'Name to assign to the server.'
}

_server_image_version() {
  _message 'Server image version.'
}

_server_type(){
  local commands; commands=(
    'jupyter'
    'jupyterlab'
    'rstudio'
  )
  _describe 'command' commands
}

_node_type(){

    setopt localoptions sh_word_split

    node_types=$(faculty server instance-types --verbose 2>/dev/null)
    IFS=$'\n' node_types=($node_types)

    header="$node_types[1]"
    node_types=("${node_types[@]:1}")

    max_name_length=-1
    max_cpu_length=-1
    for node_type in ${node_types[@]}
    do
        node_type_name=`echo $node_type | awk '{print $1;}'`
        if [ ${#node_type_name} -gt $max_name_length ]
        then
	    max_name_length=${#node_type_name}
	fi
	cpu=`echo $node_type | awk '{print $2;}'`
        if [ ${#cpu} -gt $max_cpu_length ]
        then
	    max_cpu_length=${#node_type_name}
	fi
    done

    pad_length=`expr $max_name_length`
    pad=`printf '%.0s ' {1..$pad_length}`
    header=`echo $header | sed -e "s/Machine Type[[:space:]]*CPUs/Machine Type${pad}CPUs/g"`

    local commands; commands=()
    for node_type in ${node_types[@]}
    do
        node_type_name=`echo $node_type | awk '{print $1;}'`
	node_type_info=`echo $node_type | sed -e "s/$node_type_name//g" -e "s/^[ \t]*//"`
        cpu=`echo $node_type_info | awk '{print $1;}'`
	pad_length=`expr $max_cpu_length - ${#cpu} + 2`
	pad=`printf '%.0s ' {1..$pad_length}`
	commands+=$node_type_name:$pad$node_type_info
    done

    _message "${header}"
    _describe -V 'command' commands

}

_faculty_projects() {

  projects=$(faculty project list 2>/dev/null)

  local IFS=$'\n'
  setopt localoptions sh_word_split
  projects=($projects)
  _describe 'Available Faculty projects' projects

}

_faculty_servers() {

  local IFS=$'\n'
  setopt localoptions sh_word_split

  servers=$(faculty server list ${1//\\ /\ } --verbose --all 2>/dev/null)
  servers=($servers)

  if [ "$servers" = "No servers." ]
  then
        _message "No servers."
  else
      header="$servers[1]"

      servers=("${servers[@]:1}")

      server_names=$(faculty server list ${1//\\ /\ } --all 2>/dev/null)
      server_names=($server_names)

      max_length=-1
      for server_name in ${server_names[@]}
      do
         if [ ${#server_name} -gt $max_length ]
         then
            max_length=${#server_name}
         fi
      done

      pad_length=`expr $max_length - 6`
      pad=`printf '%.0s ' {1..$pad_length}`
      header=`echo $header | sed -e "s/Server Name[[:space:]]*Type/Server Name${pad}Type/g"`

      num_servers=${#server_names[@]}

      local commands; commands=()
      for i in $(seq 1 $num_servers); do

         server=$servers[i]
         server_name=$server_names[i]
         server=`echo $server | sed -e "s/$server_name//g" -e "s/^[ \t]*//"`
         commands+=$server_name:$server
      done

      _message "${header}"
      _describe 'command' commands
  fi
}

_faculty_environments() {

  environments=$(faculty environment list ${1//\\ /\ } 2>/dev/null)

  local IFS=$'\n'
  setopt localoptions sh_word_split
  environments=($environments)
  _describe 'Available Faculty environments' environments

}

_faculty_jobs() {

  jobs=$(faculty job list ${1//\\ /\ } 2>/dev/null)

  local IFS=$'\n'
  setopt localoptions sh_word_split
  jobs=($jobs)
  _describe 'Available Faculty jobs' jobs

}

_faculty_runs() {

  runs=$(faculty job list-runs ${1//\\ /\ } ${2//\\ /\ } 2>/dev/null)

  local IFS=$'\n'
  setopt localoptions sh_word_split
  runs=($runs)
  _describe 'Available Faculty runs' runs

}

_remote_path_suggestions() {

  if test -z "$2" -o "$2" = '/project'; then
    p=/project/
  else
    if test ${${:-$2}[-1]} = '/'; then
      p=$2
    else
      p=$2:h/
    fi
  fi

  SML_REMOTE_PATH_SUGGESTIONS=$(faculty file ls $1 $p)
}

compdef _faculty faculty
"""
