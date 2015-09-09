Event-based PSHA with logic tree sampling
=========================================

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 100        
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      10         
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.2        
area_source_discretization   20.0       
random_seed                  23         
master_seed                  0          
concurrent_tasks             32         
============================ ===========

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================ ===========
smlt_path weight source_model_file                        gsim_logic_tree num_realizations num_sources
========= ====== ======================================== =============== ================ ===========
b11       0.01   `source_model1.xml <source_model1.xml>`_ simple(3)       63/3             307        
b12       0.01   `source_model2.xml <source_model2.xml>`_ simple(3)       37/3             307        
========= ====== ======================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(6)
  0,BooreAtkinson2008: ['33 realizations']
  0,CampbellBozorgnia2008: ['22 realizations']
  0,ChiouYoungs2008: ['<0,b11,CY,w=0.01>', '<1,b11,CY,w=0.01>', '<2,b11,CY,w=0.01>', '<24,b11,CY,w=0.01>', '<40,b11,CY,w=0.01>', '<47,b11,CY,w=0.01>', '<58,b11,CY,w=0.01>', '<61,b11,CY,w=0.01>']
  1,BooreAtkinson2008: ['19 realizations']
  1,CampbellBozorgnia2008: ['<63,b12,CB,w=0.01>', '<69,b12,CB,w=0.01>', '<70,b12,CB,w=0.01>', '<78,b12,CB,w=0.01>', '<79,b12,CB,w=0.01>', '<92,b12,CB,w=0.01>', '<93,b12,CB,w=0.01>', '<96,b12,CB,w=0.01>', '<98,b12,CB,w=0.01>', '<99,b12,CB,w=0.01>']
  1,ChiouYoungs2008: ['<65,b12,CY,w=0.01>', '<71,b12,CY,w=0.01>', '<72,b12,CY,w=0.01>', '<74,b12,CY,w=0.01>', '<76,b12,CY,w=0.01>', '<82,b12,CY,w=0.01>', '<89,b12,CY,w=0.01>', '<95,b12,CY,w=0.01>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b11       Active Shallow Crust 480         
1   b11       Active Shallow Crust 535         
2   b11       Active Shallow Crust 462         
3   b11       Active Shallow Crust 457         
4   b11       Active Shallow Crust 473         
5   b11       Active Shallow Crust 524         
6   b11       Active Shallow Crust 510         
7   b11       Active Shallow Crust 512         
8   b11       Active Shallow Crust 448         
9   b11       Active Shallow Crust 463         
10  b11       Active Shallow Crust 486         
11  b11       Active Shallow Crust 471         
12  b11       Active Shallow Crust 529         
13  b11       Active Shallow Crust 515         
14  b11       Active Shallow Crust 473         
15  b11       Active Shallow Crust 464         
16  b11       Active Shallow Crust 457         
17  b11       Active Shallow Crust 467         
18  b11       Active Shallow Crust 498         
19  b11       Active Shallow Crust 483         
20  b11       Active Shallow Crust 477         
21  b11       Active Shallow Crust 477         
22  b11       Active Shallow Crust 462         
23  b11       Active Shallow Crust 470         
24  b11       Active Shallow Crust 489         
25  b11       Active Shallow Crust 476         
26  b11       Active Shallow Crust 489         
27  b11       Active Shallow Crust 471         
28  b11       Active Shallow Crust 466         
29  b11       Active Shallow Crust 478         
30  b11       Active Shallow Crust 449         
31  b11       Active Shallow Crust 484         
32  b11       Active Shallow Crust 531         
33  b11       Active Shallow Crust 471         
34  b11       Active Shallow Crust 483         
35  b11       Active Shallow Crust 493         
36  b11       Active Shallow Crust 506         
37  b11       Active Shallow Crust 461         
38  b11       Active Shallow Crust 465         
39  b11       Active Shallow Crust 477         
40  b11       Active Shallow Crust 481         
41  b11       Active Shallow Crust 509         
42  b11       Active Shallow Crust 483         
43  b11       Active Shallow Crust 491         
44  b11       Active Shallow Crust 470         
45  b11       Active Shallow Crust 488         
46  b11       Active Shallow Crust 451         
47  b11       Active Shallow Crust 480         
48  b11       Active Shallow Crust 461         
49  b11       Active Shallow Crust 470         
50  b11       Active Shallow Crust 524         
51  b11       Active Shallow Crust 501         
52  b11       Active Shallow Crust 504         
53  b11       Active Shallow Crust 471         
54  b11       Active Shallow Crust 501         
55  b11       Active Shallow Crust 495         
56  b11       Active Shallow Crust 461         
57  b11       Active Shallow Crust 490         
58  b11       Active Shallow Crust 498         
59  b11       Active Shallow Crust 449         
60  b11       Active Shallow Crust 484         
61  b11       Active Shallow Crust 497         
62  b11       Active Shallow Crust 516         
63  b12       Active Shallow Crust 47          
64  b12       Active Shallow Crust 57          
65  b12       Active Shallow Crust 57          
66  b12       Active Shallow Crust 57          
67  b12       Active Shallow Crust 48          
68  b12       Active Shallow Crust 55          
69  b12       Active Shallow Crust 47          
70  b12       Active Shallow Crust 50          
71  b12       Active Shallow Crust 46          
72  b12       Active Shallow Crust 45          
73  b12       Active Shallow Crust 45          
74  b12       Active Shallow Crust 53          
75  b12       Active Shallow Crust 56          
76  b12       Active Shallow Crust 35          
77  b12       Active Shallow Crust 35          
78  b12       Active Shallow Crust 52          
79  b12       Active Shallow Crust 41          
80  b12       Active Shallow Crust 51          
81  b12       Active Shallow Crust 52          
82  b12       Active Shallow Crust 36          
83  b12       Active Shallow Crust 54          
84  b12       Active Shallow Crust 48          
85  b12       Active Shallow Crust 46          
86  b12       Active Shallow Crust 47          
87  b12       Active Shallow Crust 49          
88  b12       Active Shallow Crust 49          
89  b12       Active Shallow Crust 34          
90  b12       Active Shallow Crust 48          
91  b12       Active Shallow Crust 43          
92  b12       Active Shallow Crust 48          
93  b12       Active Shallow Crust 44          
94  b12       Active Shallow Crust 44          
95  b12       Active Shallow Crust 55          
96  b12       Active Shallow Crust 42          
97  b12       Active Shallow Crust 52          
98  b12       Active Shallow Crust 51          
99  b12       Active Shallow Crust 53          
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
1           1           
2           2           
3           3           
4           4           
5           5           
6           6           
7           7           
8           8           
9           9           
10          10          
11          11          
12          12          
13          13          
14          14          
15          15          
16          16          
17          17          
18          18          
19          19          
20          20          
21          21          
22          22          
23          23          
24          24          
25          25          
26          26          
27          27          
28          28          
29          29          
30          30          
31          31          
32          32          
33          33          
34          34          
35          35          
36          36          
37          37          
38          38          
39          39          
40          40          
41          41          
42          42          
43          43          
44          44          
45          45          
46          46          
47          47          
48          48          
49          49          
50          50          
51          51          
52          52          
53          53          
54          54          
55          55          
56          56          
57          57          
58          58          
59          59          
60          60          
61          61          
62          62          
63          63          
64          64          
65          65          
66          66          
67          67          
68          68          
69          69          
70          70          
71          71          
72          72          
73          73          
74          74          
75          75          
76          76          
77          77          
78          78          
79          79          
80          80          
81          81          
82          82          
83          83          
84          84          
85          85          
86          86          
87          87          
88          88          
89          89          
90          90          
91          91          
92          92          
93          93          
94          94          
95          95          
96          96          
97          97          
98          98          
99          99          
=========== ============

Expected data transfer for the sources
--------------------------------------
================================== ========
Number of tasks to generate        34      
Estimated sources to send          190.8 KB
Estimated hazard curves to receive 90 KB   
================================== ========