# use a script like this:
# for i in $(grep data/ ./openquakeplatform_ipt/static/ipt/js/examples/5*.js | sed 's@.*data@data@g;s@\.xml.*@.xml@g') ; do touch ~/git/oq-platform-standalone/$i ; done
# to generate files used by tests

