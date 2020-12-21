# This script must be executed as source ./reset_env.sh or it will be inoperative.
# This is a copy of the script in TransitUtils - don't modify this version.
# These commands are placed in a script because differing versions of Xcode, CMake,
# Make, etc. interpret escape characters inconsistently
# This script is compliant with the old POSIX shell standard in case building happens
# in some odd Linux environment.

set -eu

# iOS related
unset TARGET_DEVICE_MODEL
unset TARGET_DEVICE_OS_VERSION
unset SDKROOT 
unset SDK_DIR 
unset DEPLOYMENT_TARGET_CLANG_ENV_NAME 
unset IPHONEOS_DEPLOYMENT_TARGET 

# Pyenv related
export SHIMS="$HOME/.pyenv/shims"
export PATH="$SHIMS:$PATH"

# Verification of paths
P_PYPY3="$(which pypy3 || echo fail)"
P_PYTHON3="$(which python3 || echo fail)"

if test "$P_PYPY3" = "${P_PYPY3#$SHIMS}"; then
	printf "\033[31mWarning! pyenv is misconfigured for pypy3\033[0m\n"
fi


if test "$P_PYTHON3" = "${P_PYTHON3#$SHIMS}"; then
	printf "\033[31mWarning! pyenv is misconfigured for python3\033[0m\n"
fi



printf "Environment reset within current shell.\n"

