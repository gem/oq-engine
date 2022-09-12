#!/bin/bash
ENGINE_VERS="$1"
sed -i 's@](LICENSE)@](https://github.com/gem/oq-engine/blob/'"$ENGINE_VERS"'/LICENSE)@g;s@](\.\./@](https://github.com/gem/oq-engine/blob/@g;s@](doc/@](https://github.com/gem/oq-engine/blob/'"$ENGINE_VERS"'/doc/@g' README.md
