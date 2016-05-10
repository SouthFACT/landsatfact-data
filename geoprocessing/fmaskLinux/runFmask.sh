#! /bin/bash

DIRECTORY=`dirname $0`
echo $DIRECTORY

cd $DIRECTORY
cd ../..
#get the config file and make sure it will not do something delete all...
configfile=./bash_config.cfg
configfile_secured=./tmp_bash_config.cfg

# check if the file contains something we don't want
if egrep -q -v '^#|^[^ ]*=[^;]*' "$configfile"; then
  # filter the original to a new file
  egrep '^#|^[^ ]*=[^;&]*'  "$configfile" > "$configfile_secured"
  configfile="$configfile_secured"
fi

#  now source it, either the original or the filtered variant
source "$configfile"

export LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/bin/glnxa64:/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/sys/java/jre/glnxa64/jre/lib/amd64/native_threads:/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/sys/java/jre/glnxa64/jre/lib/amd64/server:/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/sys/java/jre/glnxa64/jre/lib/amd64
export XAPPLRESDIR=/usr/local/MATLAB/MATLAB_Compiler_Runtime/v80/X11/app-defaults
echo $LD_LIBRARY_PATH
echo $XAPPLRESDIR
$path_projects/geoprocessing/fmaskLinux/Fmask_Linux
# ./Fmask_Linux
