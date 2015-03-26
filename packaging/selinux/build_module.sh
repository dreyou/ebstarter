#!/bin/sh
checkmodule -M -m -o ebstarter.mod ebstarter.te
semodule_package -o ebstarter.pp -m ebstarter.mod
echo "Change type of sender.py to shell_exec_t with command: chcon -t shell_exec_t sender.py"
echo "Install module with command: semodule -i ebstarter.pp"