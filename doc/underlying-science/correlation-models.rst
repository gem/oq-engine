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

Principal-component joint models
--------------------------------

Some direct joint models use principal component analysis (PCA) to represent
the residual vector through latent spatial fields, often using fewer fields
than IMTs. Let
:math:`\boldsymbol{z}(s)` contain the residuals for the IMTs at site :math:`s`,
:math:`A` be a loading matrix, and :math:`\boldsymbol{u}(s)` contain the
principal-component fields. The representation is

.. math::

   \boldsymbol{z}(s) \simeq A\boldsymbol{u}(s).

The scaling of :math:`A` and :math:`\boldsymbol{u}` depends on the convention
used by the model: eigenvalue scaling may be carried by the loadings, the
component covariances, or both. When the retained components are mutually
uncorrelated and component :math:`k` has spatial covariance
:math:`C_k(s,t)`, the reconstructed IM covariance is

.. math::

   C_{ij}(s,t) = \sum_{k=1}^{K} A_{ik} A_{jk} C_k(s,t).

More generally, a model may specify a non-diagonal latent covariance and use
:math:`A C_u(s,t) A^{\mathsf{T}}`. The component covariance functions need not
have identical forms or spatial ranges. Their definitions and the loading
normalization must be taken from the publication or its reference
implementation rather than transferred between models.

If each retained component defines a valid spatial covariance, the joint
matrix assembled from the sum above is positive semidefinite. It is converted
to correlation by its reconstructed marginal variances,

.. math::

   \rho_{ij}(s,t) =
   \frac{C_{ij}(s,t)}
        {\sqrt{C_{ii}(s,s) C_{jj}(t,t)}}.

This positive diagonal rescaling preserves positive semidefiniteness and
produces a unit diagonal when all marginal variances are positive.

Retaining every component avoids the rank loss caused by truncation and can
reproduce the covariance represented by the full PCA basis when its component
scaling is retained. A truncation to :math:`K` components instead gives a
low-rank approximation in the IMT dimension: at one site its rank is at most
:math:`K`. It can capture the dominant dependence with fewer fitted spatial
models, but discards the omitted components and generally changes the
reconstructed covariance. Across multiple sites the rank also depends on the
spatial rank of each component covariance. Whether to use a full or truncated
basis, and whether that choice is configurable, is model-specific. Du and
Ning (2021), for example, publish a recommended truncated construction.

When a model exposes interpolation between calibrated IMT coordinates, it is
preferable to interpolate a covariance-generating representation and then
reconstruct and normalize the matrix. For example, interpolating loading
vectors while retaining valid component covariances preserves the
positive-semidefinite construction for the new coordinates. Interpolating
component covariance parameters can serve the same purpose only when the
result remains in a valid covariance family. By contrast, interpolating each
pairwise correlation independently does not in general preserve joint
consistency, positive semidefiniteness, or even a unit diagonal. The
interpolation coordinate and its allowed domain still require scientific
support; the PCA construction alone does not justify extrapolation.

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
large multi-IMT field.

Scalable sampling on regular grids
----------------------------------

For a stationary model evaluated on a regular two-dimensional grid, the
spatial covariance has repeated block-Toeplitz structure. Circulant embedding
places that covariance inside a larger periodic block-circulant matrix, whose
spatial modes can be diagonalized with fast Fourier transforms (FFTs). Only a
small IMT-by-IMT spectral covariance must then be factorized at each Fourier
mode. If :math:`P` is the number of cells in the embedded grid, constructing
the factor requires :math:`P` small :math:`M \times M` factorizations and each
field requires FFTs and small matrix products at those frequencies. For the
small, fixed number of IMTs typical of a calculation, the work therefore grows
approximately as :math:`P\log P`, rather than cubically with :math:`MN`, and
does not require storing a dense :math:`MN \times MN` matrix.

The repeated structure follows from stationarity: covariance depends on the
separation between two grid cells, rather than on their absolute coordinates.
Consequently, every row of the spatial covariance is a shifted version of the
same set of covariance lags. A finite rectangular grid has a block-Toeplitz
with Toeplitz blocks (BTTB) covariance. Extending and reflecting those lags on
a larger periodic grid produces a block-circulant with circulant blocks (BCCB)
covariance while preserving all covariances between cells in the original
grid.

An FFT changes the spatial representation from grid cells to sinusoidal
spatial frequencies. In this representation, the large BCCB matrix separates
into one small :math:`M \times M` spectral covariance matrix for every
frequency, where :math:`M` is the number of IMTs. OpenQuake computes a square
root of each of these matrices. To draw a field, it transforms independent
Gaussian noise to the frequency domain, applies the corresponding spectral
root, transforms the result back, and retains the original grid. This can be
viewed as efficiently combining random spatial waves whose amplitudes and
cross-IMT dependence are prescribed by the correlation model.

The periodic extension must itself be a valid covariance, which means that
all of its spectral covariance matrices must be positive semidefinite. A valid
stationary model on the requested grid does not guarantee this for the first
periodic extension. OpenQuake therefore increases the size of the embedding
until the condition is met. Once it is met, cropping the simulated periodic
field recovers the covariance specified by the model on the original grid;
the embedding does not replace the model with a periodic approximation there.

The engine uses this path automatically for sufficiently large compatible
models and regular grids. Grid cells may be unoccupied, provided the enclosing
rectangle is not excessively larger than the requested site collection. The
periodic embedding is enlarged until its spectrum is positive semidefinite;
the calculation stops with an explanatory error when that cannot be achieved
within the supported enlargement.

For station-conditioned fields, OpenQuake combines circulant embedding with
Matheron substitution. If :math:`U_T` and :math:`U_O` are paired unconditional
draws at the targets and observations, respectively, a conditional draw is

.. math::

   Y_{T|O} = \mu_T + U_T +
   \Sigma_{TO}\Sigma_{OO}^{+}(y_O - \mu_O - U_O).

This avoids constructing or factorizing the dense target posterior covariance.
The target-to-station regression weights are built once in memory-bounded site
chunks and reused for every realization batch.

Circulant embedding samples directly only on the grid. Observations that
coincide with grid cells use the same simulated values exactly. Off-grid
stations follow the local-kriging approximation of Bailey et al. (2022): each
is sampled conditionally on a fourth-order grid neighborhood, and stations in
the same grid box are sampled jointly across all IMTs. Conditional errors from
different grid boxes are assumed independent. The regular-grid field itself
is exact for the embedded covariance; this conditional-independence assumption
is the approximation introduced for irregular station locations.

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

* Bailey, M. D., Bandyopadhyay, S., Nychka, D. W., Thompson, E. M., and
  Worden, C. B. (2022). Adapting conditional simulation using circulant
  embedding for irregularly spaced spatial data. *Stat*, 11(1), e446.
  https://doi.org/10.1002/sta4.446
* Baker, J. W., and Cornell, C. A. (2006). Correlation of response spectral
  values for multicomponent ground motions. *Bulletin of the Seismological
  Society of America*, 96(1), 215-227.
  https://doi.org/10.1785/0120050060
* Baker, J. W., and Jayaram, N. (2008). Correlation of spectral acceleration
  values from NGA ground motion models. *Earthquake Spectra*, 24(1), 299-317.
  https://doi.org/10.1193/1.2857544
* Bradley, B. A. (2012). Empirical correlations between peak ground velocity
  and spectrum-based intensity measures. *Earthquake Spectra*, 28(1), 17-35.
  https://doi.org/10.1193/1.3675582
* Chan, G., and Wood, A. T. A. (1999). Simulation of stationary Gaussian
  vector fields. *Statistics and Computing*, 9, 265-268.
  https://doi.org/10.1023/A:1008903804954
* Dietrich, C. R., and Newsam, G. N. (1993). A fast and exact method for
  multidimensional Gaussian stochastic simulations. *Water Resources
  Research*, 29(8), 2861-2869. https://doi.org/10.1029/93WR01070
* Du, W., and Ning, C.-L. (2021). Modeling spatial cross-correlation of
  multiple ground motion intensity measures (SAs, PGA, PGV, Ia, CAV, and
  significant durations) based on principal component and geostatistical
  analyses. *Earthquake Spectra*, 37(1), 486-504.
  https://doi.org/10.1177/8755293020952442
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
