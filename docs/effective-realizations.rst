The concept of effective realizations
==============================================

The management of the so-called logic trees is the most complex
concept in the OpenQuake-engine. The difficulty lie in optimization
concerns: it is necessary to implement logic trees in an efficient way,
otherwise the engine will not be able to cope with large computations.

To this aim we introduced the concept of *effective realizations*:
there are very common situations in which it is possible to reduce the
full logic tree of a computation to a much smaller tree, containing
much less effective realizations (i.e. paths) than the potential
realizations.

The reduction of the full logic tree happens when the actual
sources do not span the full range of tectonic region types in the
GMPE logic tree file. This happens practically always in SHARE calculations.
The SHARE GMPE logic tree potentially contains 1280 realizations,
coming from 7 different tectonic region types:

Active_Shallow: 4 GMPEs
Stable_Shallow: 5 GMPEs
Shield: 2 GMPEs
Subduction_Interface: 4 GMPEs
Subduction_InSlab: 4 GMPEs
Volcanic: 1 GMPE
Deep: 2 GMPEs

The number of paths in the full logic tree is 4 * 5 * 2 * 4 * 4 * 1 *
2 = 1280, pretty large. However, in practice, in most computation
users are interested only in a subset of the tectonic region type. For
instance, if the sources in your model are only of kind Active_Shallow
and Stable_Shallow, you should consider only 4 * 5  = 20 effective
realizations instead of 1280. Doing so will improve the computation
time and the neeed storage by a factor of 1280 / 20 = 64, which is
very significant.

Having motivated the need for the concept of effective realizations,
let explain how it works in practice. For sake of simplicity let us
consider the simplest possible situation, when there are two tectonic
region types in the logic tree file, but the engine contains only
sources of one tectonic region type.  Let us assume that for the first
tectonic region type (T1) the GMPE logic tree file contains 3 GMPEs A,
B, C and for the second tectonic region type (T2) the GMPE logic tree
file contains 2 GMPEs D, E. The total number of realizations is

total_num_rlzs = 3 * 2 = 6

The realizations are identified by an ordered pair of GMPEs, one for each
tectonic region type. Let's number the realizations, starting from zero,
and let's identify the logic tree path with the notation
`<GMPE of first region type>_<GMPE of second region type>`:

# | lt_path
--+--------
0 | A_D
1 | B_D
2 | C_D
3 | A_E
4 | B_E
5 | C_E

Now assume that the source model does not contain sources of tectonic region
type T1, or that such sources are filtered away since they are too distant
to have an effect: in such a situation we would expect to have only 2
effective realizations corresponding to the GMPEs in the second
tectonic region type. The weight of each effective realizations will be
three times the weight of a regular representation, since three different paths
in the first tectonic region type will produce exactly the same result.
It is not important which GMPE was chosen for the first tectonic region
type because there are no sources of kind T1; so let's denote the
path of the effective realizations with the notation
`*_<GMPE of second region type>`:

# | path
--+------
0 | *_D
1 | *_E

The engine lite will export two files with a name like

hazard_curve-smltp_sm-gsimltp_*_D-ltr_0.csv
hazard_curve-smltp_sm-gsimltp_*_E-ltr_1.csv
