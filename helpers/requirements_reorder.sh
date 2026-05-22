#!/bin/bash
echo "BEGIN"
IFS='
'
REQ_MASTER=/tmp/requirements_master.$$
for fin in $(ls requirements-*.txt); do
    echo "Processing $fin"
    NEW_REQ=/tmp/new_req.$$
    rm -rf "$NEW_REQ"
    git show master:$fin >$REQ_MASTER
    for r in $(cat "$REQ_MASTER"); do
        # echo "ROW: $r"
        if $(echo "$r" | grep -q '^\s*#'); then
            echo "$r" >> $NEW_REQ
            continue
        elif $(echo "$r" | grep -q '^\s$'); then
            echo "$r" >> $NEW_REQ
            continue
        else
            package="$(echo "$r" | sed 's@^.*/@@g;s@-.*@@g')"
        fi
        
        if grep -q -o "/${package}-" $fin; then
            lin="$(grep -n -o "/${package}-" "$fin" | cut -d: -f1)"
            n_lin="$(echo "$lin" | wc -l)"
            if [ $n_lin -ne 1 ]; then
                echo "Multiple entry on file $fin, for package $package"
                exit 1
            fi
            # echo "${fin}: FOUND $package AT LINE $lin"
            cat "$fin" | sed -n ${lin}p >> $NEW_REQ
        else
            echo "${fin}: OLD $package NOT FOUND: add it commented with the name of this branch"
            echo "# Package '$package' removed at branch '$(git branch --show-current)'" >> $NEW_REQ
            echo "# $r" >> $NEW_REQ
        fi
    done

    for r in $(cat "$fin"); do
        # echo "ROW: $r"
        if $(echo "$r" | grep -q '^\s*#'); then
            echo "$fin: ALERT, THIS COMMENT: [$r] WILL BE SKIPPED, INTRODUCE AGAIN MANUALLY IF REQUIRED"
            continue
        elif $(echo "$r" | grep -q '^\s$'); then
            continue
        else
            package="$(echo "$r" | sed 's@^.*/@@g;s@-.*@@g')"
        fi
        
        if ! grep -q -o "/${package}-" "$REQ_MASTER"; then
            echo "${fin}, ALERT, entry: [$r] NOT FOUND, append at the end of the file"
            echo "# Package '${package}' added at branch '$(git branch --show-current)'" >> $NEW_REQ
            echo "$r" >> $NEW_REQ
        fi
    done
    
    cp "$NEW_REQ" "$fin"
    echo
    echo
done
rm $REQ_MASTER
