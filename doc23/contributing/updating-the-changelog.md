## Updating the changelog

Starting from `oq-engine 1.4`, `hazardlib 0.14.0` it is possible to add new items with the description of new functionalities and/or bug fixes to the `debian/changelog` file without breaking the continuous integration and including these items in the nightly-build packages changelog when merged.

### keep debian/changelog updated

New items in ```debian/changelog``` are **mandatory** for any pull request with new major functionalities and/or important bug fixes.

New items must be added at the top of the file.

### debian/changelog items format

***
__⎵⎵[__*\<author name and surname\>*__]\<newline (␤)\>__

__⎵⎵\*⎵__*\<feature-bugfix description not exceeding 80 characters\>*__<␤>__

__⎵⎵⎵⎵__*\<optional description continuation\>*__\<␤\>__

__⎵⎵\*⎵__*\<another feature-bugfix description of the same author\>*__\<␤\>__

_... other features-bugfix descriptions of the same author ..._

__\<␤\>__

***

### Example

```
  [Yen-Shin Chen]
  * enable to change the hypocentre location.

  [Marco Pagani]
  * Gridsource added
  * Another important feature to show a coupled item of the
    same author

  [Michele Simionato]
  * Added a test sensitive to the underlying distance libraries
    that allow us to have a more long comment

```
#### Notes
  * a good item description length is between 1 and 3 or 4 lines
  * no empty lines before a new item
  * just one empty line after a new item

