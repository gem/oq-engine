for app in oq-platform-*; do 
    pip install -e . 
    if [ "$app" = "oq-platform-taxtweb" ]; then 
        export PYBUILD_NAME="oq-taxonomy" 
        pip install -e . 
        unset PYBUILD_NAME 
    fi 
done
