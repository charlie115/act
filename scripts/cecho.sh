#!/bin/bash
# color-echo.sh: Display colored messages.

# TPUT
BOLD=`tput bold`
SLINE=`tput smul`
ELINE=`tput rmul`

BLACK=`tput setaf 0`
RED=`tput setaf 1`
GREEN=`tput setaf 2`
YELLOW=`tput setaf 3`
BLUE=`tput setaf 4`
MAGENTA=`tput setaf 5`
CYAN=`tput setaf 6`
WHITE=`tput setaf 7`

BBLACK=`tput bold; tput setaf 0`
BRED=`tput bold; tput setaf 1`
BGREEN=`tput bold; tput setaf 2`
BYELLOW=`tput bold; tput setaf 3`
BBLUE=`tput bold; tput setaf 4`
BMAGENTA=`tput bold; tput setaf 5`
BCYAN=`tput bold; tput setaf 6`
BWHITE=`tput bold; tput setaf 7`

SET=`tput sgr0`