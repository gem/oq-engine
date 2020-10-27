Classical PSHA Logic Tree Demo for Latin Hypercube Sampling

This calculation demo exercises the Classical hazard calculator with a
source model logic tree, containing a site and four point sources A,
B, C, D on a square around it. The GMPE logic tree is trivial, while
the source model logic tree is complex and includes three values of
the parameter `bGRRelative` for each of the 4 sources, thus giving
3**4=81 potential paths. Of those, only 12 are sampled:

rlz_id,branch_path,weight
00,00_10_20_30_42~0,8.333334E-02
01,00_10_21_31_40~0,8.333334E-02
02,00_10_21_32_42~0,8.333334E-02
03,00_10_22_30_42~0,8.333334E-02
04,00_11_20_30_41~0,8.333334E-02
05,00_11_20_31_42~0,8.333334E-02
06,00_11_22_32_41~0,8.333334E-02
07,00_11_22_32_41~0,8.333334E-02
08,00_12_20_31_40~0,8.333334E-02
09,00_12_21_30_40~0,8.333334E-02
10,00_12_21_31_40~0,8.333334E-02
11,00_12_22_32_41~0,8.333334E-02

Expected runtime: 2 seconds
Number of sites: 1
Number of logic tree realizations: 12
GMPEs: BooreAtkinson2008
IMTs: PGA
Outputs: Hazard Curve
