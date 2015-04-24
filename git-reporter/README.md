# Git-Reporter

Git repository changes reporter

Script chekout to specified branch, fetch (not pull) from remote 
and show differences between HEAD and remote using time period.

Default output is mail using mutt command. If script run on corporate
network propably you have to use SASL/TLS auth to be able to send
mail from your workstation.
Use ~/.muttrc file to configure mutt for smtp authentification

Example ~/.muttrc using SSL SMTPS port ans plain auth
```
set from=your.name@host.tld
set use_from=yes
set smtp_url = "smtps://your_login_to_mailserver@mx.mailserver.tld:465/"
set smtp_pass = "yourpassword"
```

If you need more advanced configuration for your smtp check for mutt
manual pages.

Screenshot of email

![Alt text](https://raw.githubusercontent.com/rvojcik/toolbox-scripts/master/git-reporter/images/git-reporter.png "Screenshot")
