#!/bin/bash
#       
# Git repository changes reporter v0.1
#
# Script chekout to specified branch, fetch (not pull) from remote 
# and show differences between HEAD and remote using time period
#
# Default output is mail using mutt command. If script run on corporate
# network propably you have to use SASL/TLS auth to be able to send
# mail from your workstation.
# Use ~/.muttrc file to configure mutt for smtp authentification
#
# Example ~/.muttrc using SSL SMTPS port ans plain auth
#
# set from=your.name@host.tld
# set use_from=yes
# set smtp_url = "smtps://your_login_to_mailserver@mx.mailserver.tld:465/"
# set smtp_pass = "yourpassword"
#
# If you need more advanced configuration for your smtp check for mutt
# manual pages.
#
# Robert Vojcik <robert.vojcik@livesport.eu>

# Defined variables
git="git"
git_options="--color=always"
output_file=$(mktemp /tmp/git-report-XXXXXXX)
script_path=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )


##############################
# Place for deefined functions
##############################

# Help function with exit
show_help() {
        echo -e "\nUsage: $0 [options]"
        echo -e "\t-r\t\t- repository path"
        echo -e "\t-t\t\t- time period (default: 12 hours ago)"
        echo -e "\t  \t\t  same usage as in git since option,"
        echo -e "\t  \t\t  you can use seconds ago, days ago, month ago or specific time and date"
        echo -e "\t-m\t\t- mail address"
        echo -e "\t-o\t\t- output, mail or stdout (default: mail)"
        echo -e "\t-b\t\t- branch to be checked (default: master)"
        echo -e "\t-h\t\t- this message"
        exit 1
}

new_line() {
    echo -e "\n<br />" >> $output_file;
}

print_error() {
    echo "$1"
    exit 1
}


##############################
# Dependency check
##############################
# Check for git binary
if ! which git &> /dev/null ; then print_error "Missing git binary" ; fi
# Check for mutt binary
if ! which mutt &> /dev/null ; then print_error "Missing mutt binary" ; fi


##############################
# End of defined functions 
##############################

 #Check for options and parameters
if [ $# -eq 0 ] ; then
        show_help
fi


# Parsing arguments
while getopts “t:r:m:o:b:h” OPTION
do
     case $OPTION in
         r)
            repository_path=$OPTARG
            ;;
         t)
            time=$OPTARG
            ;;
         m)
            mail=$OPTARG
            ;;
         o)
            output_type=$OPTARG
         b)
            # If not specified, use remote origin by default
            if [[ "$OPTARG" == *"/"*  ]] ; then 
                short_branch=$(echo $OPTARG | cut -d"/" -f2)
                branch=$OPTARG
            else
                short_branch=$OPTARG
                branch=origin/$OPTARG
            fi
            
            ;;
         h)
             show_help
             ;;
     esac
done


if [[ "$output_type" == "" ]] ; then 
    output_type=mail
fi

if [[ "$branch" == "" ]] ; then 
    branch=origin/master
fi

if [ -z "$repository_path" ] ; then
    echo "No repository path entered"
    show_help
fi

if [[ "$mail" == "" ]] && [[ "$output_type" == "mail" ]] ; then
    echo "No email address entered"
    show_help
fi

# Set default values
if [ -z "$time" ] ; then
    time="12 hours ago"
fi

# Mail heading
echo -e "</pre><h3>Report for $repository_path branch $branch ($time)</h3><br /><pre>" >> $output_file
new_line

# Change directory to repository 
cd $repository_path
git checkout $short_branch -q
git fetch &> /dev/null

# Print git stat for changes
$git diff $git_options --stat --since "$time" HEAD..$branch >> $output_file
new_line

# Print git log
$git log $git_options --since "$time" --pretty=format:"%Cblue%cr%Creset | %Cred%h %Cgreen%s%Creset | %cn ( %ce )" HEAD..$branch >> $output_file
new_line

echo -e "</pre><h4>Showing individual commits</h4><pre>" >> $output_file
new_line
for commit in `$git log $git_options --since "$time" --pretty="%h" HEAD..$branch` ; do 
    $git show $git_options $commit >> $output_file
done

if [[ "$output_type" == "mail" ]] ; then 
    cat $output_file| $script_path/ansi2html.sh | mutt -s "GIT Report of $repository_path since $time" -e "set content_type=text/html" $mail
else
    # Cat and remove html tags
    cat $output_file | sed -r 's/<[\/a-zA-Z0-9]+[ ]*[\/a-zA-Z0-9]*>//g'
fi

rm $output_file
