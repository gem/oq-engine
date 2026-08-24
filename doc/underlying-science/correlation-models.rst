.. _ground-motion-correlation:

Ground-Motion Correlation Models
================================

Ground-motion models predict a median logarithmic intensity and its aleatory
variability. Ground-motion correlation models describe the dependence between
the residuals sampled around that median. This dependence matters when ground
motions are generated at multiple sites, for multiple intensity measure types
(IMTs), or when observations are used to condition a simulated field.

Residual components
-------------------

For event :math:`e`, site :math:`s` and IMT :math:`i`, the logarithmic ground
motion can be written as

.. math::

   \ln Y_{e,s,i} = \mu_{e,s,i} + \tau_i \eta_{e,i}
                   + \phi_{s,i} \epsilon_{e,s,i},

where :math:`\mu` is the median predicted by the ground-motion model,
:math:`\eta` is a standardized between-event residual and :math:`\epsilon` is
a standardized within-event residual. The corresponding standard deviations
are :math:`\tau` and :math:`\phi`; the total standard deviation is commonly
written as

.. math::

   \sigma_i = \sqrt{\tau_i^2 + \phi_i^2}.

The residual components have different dependence structures and must not be
interchanged:

* A **within-event** model describes residual variation between sites during
  the same earthquake. It may also describe dependence between IMTs.
* A **between-event** model describes dependence between the event terms of
  different IMTs. An event term is shared by all sites affected by that event.
* A **total-residual** model describes dependence between the sum of the two
  residual components. It is commonly used in conditional-spectrum methods.

If between-event and within-event correlations are known separately, the
same-site total-residual correlation is

.. math::

   \rho_{T,ij} =
   \frac{\tau_i\tau_j\rho_{B,ij} +
         \phi_i\phi_j\rho_{W,ij}}
        {\sigma_i\sigma_j}.

A published total-residual model does not, by itself, identify the separate
between-event and within-event correlations.

Dimensions of correlation
-------------------------

The OpenQuake hazard library distinguishes three geometric capabilities.

Spatial correlation
*******************

A spatial model gives the correlation of one IMT between two sites, usually as
a function of their separation :math:`h`:

.. math::

   \rho_i(s,t) = \rho_i(h_{st}).

When a spatial-only model is used for multiple IMTs, it correlates the sites
independently for each IMT. It does not supply the off-diagonal cross-IMT
blocks.

Cross-IMT correlation
*********************

A cross-IMT model gives the correlation between two IMTs at the same site:

.. math::

   \rho_{ij}(s) = \operatorname{Corr}(Z_{s,i}, Z_{s,j}).

The residual component for which the model was calibrated remains essential.
For example, a total-residual cross-IMT model must not be substituted for a
between-event model merely because both return an IMT-by-IMT matrix.

Joint spatial and cross-IMT correlation
***************************************

A direct joint model gives the dependence between any two site-and-IMT pairs:

.. math::

   \rho_W((s,i),(t,j)) =
   \operatorname{Corr}(\epsilon_{e,s,i}, \epsilon_{e,t,j}).

For :math:`M` IMTs and :math:`N` sites, OpenQuake orders the joint vector by
IMT, so the correlation matrix has shape :math:`MN \times MN`. Direct joint
models can also return rectangular blocks between target and observation
locations. Those blocks are required for station conditioning.

Separate spatial and cross-IMT models are sometimes combined using a separable
approximation,

.. math::

   \rho_W((s,i),(t,j)) \simeq
   \rho_{S}(h_{st})\rho_{I}(i,j).

This is a modelling assumption, not a general identity. A direct joint model
is preferable when one has been calibrated for the application.

Baker and Bradley (2017) total residuals
----------------------------------------

Baker and Bradley (2017) estimated within- and between-event correlations
from NGA-West2 residuals, then combined them into total-residual correlation
using the :math:`\tau`, :math:`\phi` and :math:`\sigma` weighting shown above.
The corrected electronic supplement provides aggregate RotD50 correlations
for PGA, PGV and 5%-damped SA at 105 periods from 0.01 to 10 seconds. PGA and
PGV are direct empirical IMTs rather than spectral-period proxies.

The paper reports using active-shallow-crustal records with :math:`M>5` and
:math:`R<100` km. The corrected author code implements inclusive limits of
:math:`M\geq5` and :math:`R_{JB}\leq100` km. It found no practically
significant dependence on magnitude, distance or :math:`V_{S30}`. The paper
also found that RotD50 and RotD100 SA correlations are essentially identical,
but the aggregate table and the implementation metadata retain RotD50 as the
calibrated component.

No interpolation rule was published. A later author-maintained Matlab
calculator supports bilinear interpolation in log period over the
positive-definite SA table, but ``BakerBradley2017`` deliberately accepts only
the 105 tabulated periods and does not extrapolate or substitute IMTs. The
authors' analysis pipeline applies ``nearestCorrelationMatrix`` to the complete
109-IMT empirical matrix and exports both raw and positive-definite tables.
The model loads the corrected positive-definite export before extracting its
supported PGA, PGV and SA subset. Although the authors computed separate
residual components during their analysis, the supplement does not publish a
between-event matrix. The implemented total-residual table must therefore not
be used or labelled as a between-event model.

Covariance and sampling
-----------------------

For within-event residuals, a correlation coefficient becomes a covariance
through the site- and IMT-dependent standard deviations:

.. math::

   \Sigma_W[(s,i),(t,j)] =
   \phi_{s,i}\phi_{t,j}\rho_W((s,i),(t,j)).

The equivalent expression for between-event residuals uses :math:`\tau`, while
total-residual covariance uses :math:`\sigma`. The OpenQuake correlation-model
interfaces operate primarily on standardized correlations; calculators apply
the corresponding standard deviations when constructing covariance or
residual ground motions.

The default sampler forms a dense correlation matrix and uses a Cholesky
factorization. Its memory requirement grows quadratically and its factorization
cost grows cubically with :math:`MN`. Consequently, a calculation that is
tractable for one IMT or a small site collection can become infeasible for a
large multi-IMT field. Structured methods and alternative factorizations are
needed for substantially larger calculations.

Configuration examples are provided in the User Guide for
:ref:`scenario hazard <scenario-hazard-params>`,
:ref:`event-based PSHA <event-based-psha-params>`,
:ref:`ShakeMap workflows <scenarios-from-shakemaps>`, and
:ref:`advanced calculations <advanced-calculations>`. The implemented model
classes and interfaces are listed in the
:ref:`hazardlib API reference <openquake-hazardlib-correlation-models>`.

Conditioning on observations
----------------------------

Conditioning requires more than marginal posterior standard deviations. If
:math:`T` denotes target values and :math:`O` observations, the posterior
within-event covariance contains the full joint blocks
:math:`\Sigma_{TT}`, :math:`\Sigma_{TO}` and :math:`\Sigma_{OO}`:

.. math::

   \Sigma_{T|O} = \Sigma_{TT} -
   \Sigma_{TO}\Sigma_{OO}^{-1}\Sigma_{OT}.

This is why direct joint models expose rectangular correlation blocks. See
:doc:`conditioning-gmf` for the complete conditioning workflow.

The current compatibility path uses Jayaram and Baker (2009) when no
within-event model is configured and Goda and Atkinson (2009) when no
between-event model is configured. If the selected within-event model is
spatial-only, the off-diagonal IMT blocks are completed with a fixed Baker and
Jayaram (2008) separable approximation. That model describes total-residual
correlation, so its use for the within-event blocks is a legacy approximation.
A direct joint within-event model bypasses this construction. Loth and Baker
(2013) is the first such model distributed with hazardlib. It was calibrated
jointly across sites and 5%-damped spectral-acceleration periods from 0.01 to
10 seconds. PGA is supported using SA(0.01) as a correlation proxy, following
the operational ShakeMap convention. This changes only the correlation
coefficients; PGA medians and standard deviations still come from the GSIM.
The model rejects simultaneous PGA and SA(0.01), which would otherwise create
duplicate residual fields, and does not support PGV or other IMTs.

The implementation uses the coefficient tables corrected by the 2020 erratum
and follows the authors' 2022 Matlab refinements. These preserve the diagonal
ridge during interpolation and use a revised, higher-precision nugget matrix
to retain positive definiteness.

Conditional spectra require an explicitly configured total-residual model;
omitting it does not request an independent calculation.

ShakeMap limitation
-------------------

The legacy ShakeMap XML workflow supplies median ground motions and marginal
total standard deviations. For reproducibility, OpenQuake currently retains a
workflow that applies configured spatial and total-residual cross-IMT models to
those quantities. Applying a total-residual correlation model in this way does
not reconstruct the station-conditioned posterior covariance and should not be
interpreted as exact ShakeMap-consistent sampling.

`Issue #11706 <https://github.com/gem/oq-engine/issues/11706>`_ tracks a future
workflow based on richer ShakeMap products. That workflow will need to
distinguish covariance information exported by ShakeMap from any approximate
cross-IMT reconstruction used during posterior sampling.

References
----------

* Baker, J. W., and Cornell, C. A. (2006). Correlation of response spectral
  values for multicomponent ground motions. *Bulletin of the Seismological
  Society of America*, 96(1), 215-227.
  https://doi.org/10.1785/0120050060
* Baker, J. W., and Bradley, B. A. (2017). Intensity measure correlations
  observed in the NGA-West2 database, and dependence of correlations on
  rupture and site parameters. *Earthquake Spectra*, 33(1), 145-156.
  https://doi.org/10.1193/060716EQS095M
* Baker, J. W., and Bradley, B. A. (2025). Corrigendum. *Earthquake Spectra*,
  41(2), 1825-1827. https://doi.org/10.1177/87552930241245554
* Baker, J. W., and Jayaram, N. (2008). Correlation of spectral acceleration
  values from NGA ground motion models. *Earthquake Spectra*, 24(1), 299-317.
  https://doi.org/10.1193/1.2857544
* Bradley, B. A. (2012). Empirical correlations between peak ground velocity
  and spectrum-based intensity measures. *Earthquake Spectra*, 28(1), 17-35.
  https://doi.org/10.1193/1.3675582
* Goda, K., and Atkinson, G. M. (2009). Probabilistic characterization of
  spatially correlated response spectra for earthquakes in Japan. *Bulletin
  of the Seismological Society of America*, 99(5), 3003-3020.
  https://doi.org/10.1785/0120090007
* Heresi Venegas, P. C., and Miranda Mijares, E. (2019). Uncertainty in
  intraevent spatial correlation of elastic pseudo-acceleration spectral
  ordinates. *Bulletin of Earthquake Engineering*, 17(3), 1099-1115.
  https://doi.org/10.1007/s10518-018-0506-6
* Jayaram, N., and Baker, J. W. (2009). Correlation model for spatially
  distributed ground-motion intensities. *Earthquake Engineering & Structural
  Dynamics*, 38(15), 1687-1708. https://doi.org/10.1002/eqe.922
* Loth, C., and Baker, J. W. (2013). A spatial cross-correlation model of
  spectral accelerations at multiple periods. *Earthquake Engineering &
  Structural Dynamics*, 42(3), 397-417. https://doi.org/10.1002/eqe.2212
* Loth, C., and Baker, J. W. (2020). Erratum: A spatial cross-correlation model
  for ground motion spectral accelerations at multiple periods. *Earthquake
  Engineering & Structural Dynamics*, 49(3), 315-316.
  https://doi.org/10.1002/eqe.3233
