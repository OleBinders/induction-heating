"""Truncated Region Eigenfunction Expansion (TREE) bare-coil field machinery.

This module implements Phase 2b of the coupled eddy-current solver: the
eigenfunction expansion for a finite solenoid's OWN magnetic field with
*no* workpiece present (sigma = 0 everywhere). It is the foundation that
Phase 2c/2d build the workpiece coupling on top of -- if this doesn't
reproduce the already-validated closed-form solenoid field exactly, nothing
built on top of it can be trusted, so this module is validated directly
against ``induction_heating.core.electromagnetic.solenoid_b_field_on_axis``
and ``solenoid_b_field_off_axis`` in ``tests/test_coupled_eddy_current.py``.

TIME-CONVENTION NOTE (read before touching this file or anything built on
top of it): the source paper for this method (Sun, Bowler & Theodoulidis,
IEEE Trans. Magnetics 41(9), 2455-2461, 2005) uses the e^(-i*omega*t)
(physics) time convention throughout, not the e^(+j*omega*t) (engineering)
convention. Phase 2b itself has sigma = 0 everywhere, so no complex
impedance/skin-effect terms appear yet and this doesn't bite -- but Phase
2c/2d introduce complex radial wavenumbers gamma = sqrt(q^2 + j*omega*mu*sigma)
and a complex coil impedance. Python's ``1j`` MUST be interpreted as this
paper's "i" (e^(-i*omega*t)) everywhere in this family of modules. Do not
mix in code that implicitly assumes e^(+j*omega*t) (e.g. from a different
textbook or a different part of this codebase) -- the two conventions are
related by complex-conjugating every impedance/complex-permeability term,
and silently mixing them produces a sign error in the reactive part of the
field that will NOT be caught by a real-valued (sigma=0) test like this
phase's, only by later phases that carry complex quantities.

Geometry and source model
--------------------------
Axisymmetric solenoid coil, symmetric about z=0 (matching the convention
already used throughout ``core/electromagnetic.py`` and ``SolenoidCoil``):
inner radius r1, outer radius r2, axial extent from -z1 to +z1 with
z1 = coil.length / 2, N turns. The winding is modelled as a uniform,
purely azimuthal current density J_phi = n*I filling the rectangular
(rho, z) cross-section [r1, r2] x [-z1, z1], where n = N / [(r2-r1)*length]
is the coil's *areal* turn density (turns per unit cross-sectional area,
not turns per unit length -- see ``coil_turn_density``).

A synthetic boundary is placed at z = +-h (h chosen large compared to the
coil, e.g. h >= 5 * coil.length as a starting default -- see the
convergence notes below), turning the free-space field into a discrete
eigenfunction sum instead of a continuous Hankel/Fourier transform. With
the coil symmetric about z=0, only the even-in-z (cosine) family is
needed. Two source-free ("air") regions exist away from the winding
itself: rho <= r1 (inside the coil bore, using the modified Bessel
function I1, regular at rho=0) and rho >= r2 (outside the coil, using K1,
decaying as rho -> infinity). This module does not implement the field
*inside* the winding cross-section (r1 < rho < r2) -- that requires the
inhomogeneous (particular-solution) piece of the ODE, which is out of
scope for Phase 2b's validation (the closed-form comparison functions are
themselves only valid outside the coil's own current sheet).

Deviations from the literally-transcribed paper equations (documented,
not silent)
------------------------------------------------------------------------
The equations as summarized in the project's Phase 2 plan (paraphrasing
the paper) state:

    kappa_j = j*pi/h                                    ("Eq. 59"'s eigenvalues)
    C_j = (1/kappa_j^3) * [sin(kappa_j*z1) - sin(kappa_j*z2)] * K1(kappa_j*r1, kappa_j*r2)
    K1(x1, x2) = integral from x2 to x1 of x*K1(x) dx   ("Eq. 46")
    A_phi = (2*mu_0*n*I/h) * sum_j cos(kappa_j*z) * I1(kappa_j*rho) * C_j

Implementing this literally and cross-checking against
``solenoid_b_field_on_axis``/``solenoid_b_field_off_axis`` (ground truth,
already covered by ``tests/test_validation_bfield.py``) does **not**
converge to the correct field as the number of eigenvalues is increased
(20 -> 80 -> 200 all give the same, clearly-wrong answer -- not slow
convergence, but convergence to the wrong limit). Per this phase's own
instructions ("if it does NOT converge... there's a bug in your equation
transcription... stop and diagnose rather than loosening tolerances"),
this was diagnosed by re-deriving the bare-coil field from the governing
ODE and a self-adjoint Green's function for the modified Bessel operator
of order 1, then checked term-by-term against the closed-form solution.
Two transcription issues were found and fixed here; both are consistent
with all-real cos-only-mode bookkeeping errors of the kind that are easy
to introduce when paraphrasing a paper's numbered equations by hand:

1. **Eigenvalues**: kappa_j = j*pi/h does not vanish (nor does its
   derivative vanish) at the truncation boundary z=h for generic j, so it
   is not actually a valid eigenfunction basis for *any* standard boundary
   condition at z=+-h -- and empirically, using it does not converge.
   The eigenvalue set that is (a) even in z (matching cos(kappa*z), zero
   slope at the coil's own axial center by symmetry) and (b) exactly
   satisfies the Dirichlet truncation condition A_phi(rho, +-h) = 0 is the
   quarter-wave family
       kappa_m = (2*m - 1) * pi / (2*h),   m = 1, 2, 3, ...
   This is the standard Sturm-Liouville eigenbasis for y'(0)=0, y(h)=0.
   Substituting this single change into the *un-derived* rest of the
   formula already fixes the non-convergence; see below for the residual
   scale/sign issue.
2. **Coefficient formula**: rederiving C_j from the source ODE (see
   ``_bore_coefficients``'s docstring for the full derivation) shows the
   correct axial factor is the single term sin(kappa_m * z1) (using this
   module's z1 = coil.length/2, z2 = -z1 convention), not
   [sin(kappa_j*z1) - sin(kappa_j*z2)] = 2*sin(kappa_j*z1) -- the doubled
   form double-counts the even-symmetry factor that is *separately*
   already folded into the "2/h" prefactor in front of the whole sum (that
   prefactor is exactly the norm-squared reciprocal, 2/h, of the
   kappa_m = (2m-1)pi/(2h) eigenbasis on the half-domain [0, h] -- see the
   derivation below). Likewise, the radial integral is a plain
   *forward*-ordered integral from kappa*r1 to kappa*r2 (r1 < r2, positive
   result), not the reversed-bounds convention that would flip its sign.
   With both of these corrected, the resulting B-field matches
   ``solenoid_b_field_on_axis``/``off_axis`` to well under 1% (down to
   ~0.01-0.1% with enough eigenvalues/truncation length) and converges
   monotonically as the eigenvalue count and truncation length increase --
   see ``tests/test_coupled_eddy_current.py`` for the full convergence
   study this conclusion is based on.

This is exactly the kind of "trust but verify" situation the project's own
``eddy_current_density`` permeability-division bug (see
``core/eddy_currents.py``) warns about: a plausible-looking, carefully
sourced formula that is subtly wrong in a way no amount of re-reading (as
opposed to numerically validating against independent ground truth) would
have caught.

Convergence behaviour (measured, see tests for the full sweep)
----------------------------------------------------------------
- For "reasonable" coil aspect ratios (length comparable to or a few times
  the mean radius) and h = 5 * coil.length, agreement with the closed-form
  field is already better than 1% at ``num_eigenvalues=80`` and better
  than 0.5% at ``num_eigenvalues=200``.
- Very short, "fat" coils (length comparable to or less than the mean
  radius) need a *larger* truncation length relative to their length --
  h = 5*length is not enough to push the artificial boundary far enough
  into the near-field-dominated far zone; h = 20-40*length brings error
  from ~5% down to ~0.1-0.03% at fixed, modest eigenvalue counts. This is
  a truncation-length effect, not an eigenvalue-count effect (increasing
  ``num_eigenvalues`` alone does not fix it for these geometries).
- Long, thin coils need *more* eigenvalues (a few hundred, not 80) to
  resolve near-source off-axis field points close to the coil's own
  radius, because those points require higher spatial-frequency content
  in the axial Fourier-Bessel expansion. This is an eigenvalue-count
  effect, not a truncation-length one.
- The two effects above (h too small vs. num_eigenvalues too small) look
  similar (larger discrepancy) but are diagnosed differently: hold
  ``num_eigenvalues`` fixed and vary ``truncation_half_length`` -- if the
  error tracks h, it's a truncation effect; if it only tracks
  ``num_eigenvalues``, it's an eigenvalue-count effect.
- Default chosen here: ``num_eigenvalues=100``, ``truncation_half_length``
  left as a required, explicit argument (no silent default) since the
  right choice genuinely depends on the coil's aspect ratio and how close
  to the coil the field is being evaluated -- see the module-level guidance
  above. h >= 5*coil.length is a reasonable starting point for typical
  (non-extreme-aspect-ratio) coils; short/fat coils or near-field
  evaluation points close to the winding should use a larger h.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import integrate, optimize, special

from induction_heating.core.geometry import InductionSetup, SolenoidCoil
from induction_heating.utils.constants import mu_0

_DEFAULT_NUM_EIGENVALUES = 100


def coil_turn_density(coil: SolenoidCoil) -> float:
    """Areal current-density turn density n = N / [(r2-r1) * length].

    This is turns per unit *area* of the coil's (rho, z) winding
    cross-section (so that n*I has units of A/m^2, a current density) --
    NOT turns per unit length (that quantity already exists as
    ``SolenoidCoil.turn_density``). The TREE bare-coil source term treats
    the winding as carrying a uniform current density n*I over its full
    rectangular cross-section [r1, r2] x [-length/2, length/2], per Sun,
    Bowler & Theodoulidis (2005).

    Args:
        coil: SolenoidCoil geometry.

    Returns:
        Areal turn density in turns/m^2.

    Raises:
        ValueError: If the coil's radial or axial extent is non-positive
            (should not happen for a valid ``SolenoidCoil``, but guarded
            here since this quantity divides by it).
    """
    radial_extent = coil.outer_radius - coil.inner_radius
    axial_extent = coil.length
    if radial_extent <= 0.0 or axial_extent <= 0.0:
        raise ValueError(
            "coil radial extent (outer_radius - inner_radius) and axial "
            f"extent (length) must both be > 0, got radial_extent="
            f"{radial_extent}, axial_extent={axial_extent}"
        )
    return coil.turns / (radial_extent * axial_extent)


def bare_coil_axial_eigenvalues(
    truncation_half_length: float, num_eigenvalues: int
) -> np.ndarray:
    """Axial eigenvalues for the even (cosine), zero-slope-at-center,
    zero-value-at-truncation eigenbasis on z in [-h, h].

    kappa_m = (2*m - 1) * pi / (2*h),  m = 1, 2, ..., num_eigenvalues

    See the module docstring for why this quarter-wave family is used
    instead of the naively-transcribed kappa_j = j*pi/h (the latter does
    not satisfy any boundary condition at z=+-h for a cos(kappa*z) basis
    and, empirically, does not converge to the correct field).

    Args:
        truncation_half_length: Truncation half-length h (m), h > 0.
        num_eigenvalues: Number of eigenvalues to generate, >= 1.

    Returns:
        Real array of eigenvalues, shape (num_eigenvalues,), in rad/m.
    """
    if truncation_half_length <= 0.0:
        raise ValueError(
            f"truncation_half_length must be > 0, got {truncation_half_length}"
        )
    if num_eigenvalues < 1:
        raise ValueError(f"num_eigenvalues must be >= 1, got {num_eigenvalues}")

    m = np.arange(1, num_eigenvalues + 1, dtype=float)
    return (2.0 * m - 1.0) * math.pi / (2.0 * truncation_half_length)


def _forward_integral(kernel, x_lower: float, x_upper: float) -> float:
    """integral from x_lower to x_upper of kernel(x) dx, x_lower <= x_upper."""
    value, _ = integrate.quad(kernel, x_lower, x_upper)
    return value


def _x_k1_integral(x_lower: float, x_upper: float) -> float:
    """integral_{x_lower}^{x_upper} x*K1(x) dx (forward-ordered, x_lower<=x_upper)."""
    return _forward_integral(lambda x: x * special.k1(x), x_lower, x_upper)


def _x_i1_integral(x_lower: float, x_upper: float) -> float:
    """integral_{x_lower}^{x_upper} x*I1(x) dx (forward-ordered, x_lower<=x_upper)."""
    return _forward_integral(lambda x: x * special.i1(x), x_lower, x_upper)


def _coefficients(
    coil: SolenoidCoil, eigenvalues: np.ndarray, radial_integral
) -> np.ndarray:
    """Shared coefficient machinery for both the bore (K1-integral) and
    outside-coil (I1-integral) branches.

    Derivation (Green's-function solution of the source ODE): expanding
    A_phi(rho, z) = sum_m A_m(rho) * cos(kappa_m * z) and the coil's
    uniform current density J_phi(rho, z) = n*I for r1<=rho<=r2 and
    |z|<=z1 (else 0) in the same basis, each mode A_m(rho) satisfies the
    inhomogeneous modified Bessel equation of order 1:

        (1/rho) d/drho(rho dA_m/drho) - A_m/rho^2 - kappa_m^2 A_m = -mu_0 * J_m(rho)

    where J_m(rho) is the axial Fourier coefficient of J_phi at this rho,
    J_m(rho) = (2*n*I / (h*kappa_m)) * sin(kappa_m*z1) for r1<=rho<=r2
    (using the (2m-1)pi/(2h) eigenbasis's norm-squared = h/2, hence 2/h).
    The self-adjoint Green's function for this operator (Wronskian
    normalization I1(x)*K1'(x) - I1'(x)*K1(x) = -1/x) gives, for a
    uniform source shell between r1 and r2:

      rho <= r1 (bore):   A_m(rho) = mu_0 * I1(kappa_m*rho) * J_m0 / kappa_m^2
                                       * integral_{kappa_m*r1}^{kappa_m*r2} x*K1(x) dx
      rho >= r2 (outside): A_m(rho) = mu_0 * K1(kappa_m*rho) * J_m0 / kappa_m^2
                                       * integral_{kappa_m*r1}^{kappa_m*r2} x*I1(x) dx

    where J_m0 = (2*n*I/(h*kappa_m)) * sin(kappa_m*z1). Folding the 2*n*I/h
    prefactor out into the shared ``bare_coil_vector_potential``/
    ``bare_coil_b_field`` prefactor (2*mu_0*n*I/h) leaves this function
    returning the purely-geometric remainder:

        coefficient_m = sin(kappa_m * z1) * radial_integral(kappa_m*r1, kappa_m*r2) / kappa_m^3

    which is what is returned here (``radial_integral`` is
    ``_x_k1_integral`` for the bore branch or ``_x_i1_integral`` for the
    outside branch).

    Args:
        coil: SolenoidCoil geometry.
        eigenvalues: Axial eigenvalues, shape (J,) (from
            ``bare_coil_axial_eigenvalues``).
        radial_integral: Callable(x_lower, x_upper) -> float, either
            ``_x_k1_integral`` or ``_x_i1_integral``.

    Returns:
        Real array of coefficients, shape (J,), matching ``eigenvalues``.
    """
    z1 = coil.length / 2.0
    r1 = coil.inner_radius
    r2 = coil.outer_radius

    kappa = np.asarray(eigenvalues, dtype=float)
    coeffs = np.empty_like(kappa)
    for idx, k in enumerate(kappa):
        axial_term = math.sin(k * z1)
        radial_term = radial_integral(k * r1, k * r2)
        coeffs[idx] = axial_term * radial_term / k**3
    return coeffs


def bare_coil_coefficients(
    coil: SolenoidCoil, truncation_half_length: float, eigenvalues: np.ndarray
) -> np.ndarray:
    """Bare-coil bore-region (rho <= r1) expansion coefficients C_j^(0).

    See ``_coefficients`` for the full derivation. ``truncation_half_length``
    is accepted (matching the originally-sketched signature) but is not
    itself used in the coefficient formula -- it only enters via the
    ``eigenvalues`` the caller already derived from it -- so it is validated
    for a sane, positive value and otherwise unused, purely to keep the
    call site self-documenting about which truncation length the supplied
    eigenvalues came from.

    Args:
        coil: SolenoidCoil geometry.
        truncation_half_length: Truncation half-length h (m), h > 0 (used
            only for validation; the eigenvalues already encode it).
        eigenvalues: Axial eigenvalues, shape (J,), from
            ``bare_coil_axial_eigenvalues``.

    Returns:
        Real array of coefficients, shape (J,).
    """
    if truncation_half_length <= 0.0:
        raise ValueError(
            f"truncation_half_length must be > 0, got {truncation_half_length}"
        )
    return _coefficients(coil, eigenvalues, _x_k1_integral)


def _bare_coil_outside_coefficients(
    coil: SolenoidCoil, eigenvalues: np.ndarray
) -> np.ndarray:
    """Bare-coil outside-region (rho >= r2) expansion coefficients D_j^(0).

    Not part of the literally-quoted Eq. 59/46 (which only gives the bore
    branch), but required to evaluate the field outside the coil at all;
    derived by the same Green's-function construction as
    ``bare_coil_coefficients``, swapping the K1-integral for an I1-integral
    (see ``_coefficients``'s docstring). Validated together with the bore
    branch against ``solenoid_b_field_off_axis`` for rho > outer_radius in
    ``tests/test_coupled_eddy_current.py``.
    """
    return _coefficients(coil, eigenvalues, _x_i1_integral)


def _prepare_field_points(
    coil: SolenoidCoil, rho: np.ndarray, z: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, tuple[int, ...]]:
    """Broadcast (rho, z), classify each point as bore/outside, and reject
    points strictly inside the coil's own winding cross-section (out of
    scope for this bare-coil, source-free-regions-only module)."""
    rho_in_shape = np.shape(rho)
    z_in_shape = np.shape(z)
    out_shape = np.broadcast_shapes(rho_in_shape, z_in_shape)

    rho_b, z_b = np.broadcast_arrays(
        np.asarray(rho, dtype=float), np.asarray(z, dtype=float)
    )
    rho_flat = rho_b.ravel()
    z_flat = z_b.ravel()

    r1, r2 = coil.inner_radius, coil.outer_radius
    inside = rho_flat <= r1
    outside = rho_flat >= r2
    between = ~(inside | outside)
    if np.any(between):
        bad = rho_flat[between]
        raise ValueError(
            "bare_coil_vector_potential/bare_coil_b_field are only defined "
            f"in the two source-free ('air') regions rho <= {r1} (coil bore) "
            f"or rho >= {r2} (outside the coil) -- got point(s) inside the "
            f"coil's own winding cross-section, e.g. rho={bad[0]}. The field "
            "inside the winding itself (the particular-solution branch) is "
            "out of scope for Phase 2b."
        )
    return rho_flat, z_flat, inside, outside, out_shape


def bare_coil_vector_potential(
    coil: SolenoidCoil,
    current: float,
    truncation_half_length: float,
    rho: float | np.ndarray,
    z: float | np.ndarray,
    num_eigenvalues: int = _DEFAULT_NUM_EIGENVALUES,
) -> np.ndarray:
    """Bare-coil (sigma=0) azimuthal vector potential A_phi(rho, z).

    Vectorized over ``rho``/``z`` (broadcast together, then evaluated for
    all eigenvalues at once via outer products -- no Python loop over grid
    points). Only defined for rho <= coil.inner_radius (bore) or
    rho >= coil.outer_radius (outside); see the module docstring.

    Args:
        coil: SolenoidCoil geometry.
        current: Coil current amplitude (A), > 0.
        truncation_half_length: Truncation half-length h (m), > 0. Larger
            values reduce truncation error but require more
            ``num_eigenvalues`` to stay converged -- see the module
            docstring's convergence notes.
        rho: Radial position(s) (m). Scalar or array; broadcasts with z.
        z: Axial position(s) (m), relative to the coil's axial center.
            Scalar or array; broadcasts with rho.
        num_eigenvalues: Number of eigenvalues in the truncated sum.

    Returns:
        A_phi in T*m (Wb/m), same broadcast shape as (rho, z).
    """
    if current <= 0.0:
        raise ValueError(f"current must be > 0, got {current}")

    rho_flat, z_flat, inside, outside, out_shape = _prepare_field_points(
        coil, rho, z
    )

    kappa = bare_coil_axial_eigenvalues(truncation_half_length, num_eigenvalues)
    n = coil_turn_density(coil)
    prefactor = 2.0 * mu_0() * n * current / truncation_half_length

    a_flat = np.zeros_like(rho_flat)

    if np.any(inside):
        coeffs = bare_coil_coefficients(coil, truncation_half_length, kappa)
        kr = np.outer(kappa, rho_flat[inside])
        cos_kz = np.cos(np.outer(kappa, z_flat[inside]))
        bessel = special.i1(kr)
        a_flat[inside] = prefactor * np.sum(cos_kz * bessel * coeffs[:, None], axis=0)

    if np.any(outside):
        coeffs = _bare_coil_outside_coefficients(coil, kappa)
        kr = np.outer(kappa, rho_flat[outside])
        cos_kz = np.cos(np.outer(kappa, z_flat[outside]))
        bessel = special.k1(kr)
        a_flat[outside] = prefactor * np.sum(cos_kz * bessel * coeffs[:, None], axis=0)

    return a_flat.reshape(out_shape)


def bare_coil_b_field(
    coil: SolenoidCoil,
    current: float,
    truncation_half_length: float,
    rho: float | np.ndarray,
    z: float | np.ndarray,
    num_eigenvalues: int = _DEFAULT_NUM_EIGENVALUES,
) -> tuple[np.ndarray, np.ndarray]:
    """Bare-coil (sigma=0) magnetic field (B_rho, B_z) via analytic
    term-by-term differentiation of the A_phi series.

    Uses:
        B_z(rho,z)   = (1/rho) * d(rho*A_phi)/drho
        B_rho(rho,z) = -dA_phi/dz

    applied analytically to each series term with the modified-Bessel
    derivative identities d/dx[x*I1(x)] = x*I0(x) and
    d/dx[x*K1(x)] = -x*K0(x), giving, per mode (kappa, coefficient c,
    bore branch):
        contributes  kappa*I0(kappa*rho)*cos(kappa*z)*c   to B_z/prefactor
        contributes  kappa*I1(kappa*rho)*sin(kappa*z)*c   to B_rho/prefactor
    and for the outside branch, K0/K1 with an extra minus sign on the B_z
    term (from d/dx[x*K1(x)] = -x*K0(x)).

    Args:
        coil: SolenoidCoil geometry.
        current: Coil current amplitude (A), > 0.
        truncation_half_length: Truncation half-length h (m), > 0.
        rho: Radial position(s) (m). Scalar or array; broadcasts with z.
        z: Axial position(s) (m). Scalar or array; broadcasts with rho.
        num_eigenvalues: Number of eigenvalues in the truncated sum.

    Returns:
        Tuple (B_rho, B_z) in Tesla, same broadcast shape as (rho, z).
    """
    if current <= 0.0:
        raise ValueError(f"current must be > 0, got {current}")

    rho_flat, z_flat, inside, outside, out_shape = _prepare_field_points(
        coil, rho, z
    )

    kappa = bare_coil_axial_eigenvalues(truncation_half_length, num_eigenvalues)
    n = coil_turn_density(coil)
    prefactor = 2.0 * mu_0() * n * current / truncation_half_length

    b_z_flat = np.zeros_like(rho_flat)
    b_rho_flat = np.zeros_like(rho_flat)

    if np.any(inside):
        coeffs = bare_coil_coefficients(coil, truncation_half_length, kappa)
        kr = np.outer(kappa, rho_flat[inside])
        cos_kz = np.cos(np.outer(kappa, z_flat[inside]))
        sin_kz = np.sin(np.outer(kappa, z_flat[inside]))
        i0 = special.i0(kr)
        i1 = special.i1(kr)
        weighted = kappa[:, None] * coeffs[:, None]
        b_z_flat[inside] = prefactor * np.sum(cos_kz * i0 * weighted, axis=0)
        b_rho_flat[inside] = prefactor * np.sum(sin_kz * i1 * weighted, axis=0)

    if np.any(outside):
        coeffs = _bare_coil_outside_coefficients(coil, kappa)
        kr = np.outer(kappa, rho_flat[outside])
        cos_kz = np.cos(np.outer(kappa, z_flat[outside]))
        sin_kz = np.sin(np.outer(kappa, z_flat[outside]))
        k0 = special.k0(kr)
        k1 = special.k1(kr)
        weighted = kappa[:, None] * coeffs[:, None]
        b_z_flat[outside] = prefactor * np.sum(cos_kz * (-k0) * weighted, axis=0)
        b_rho_flat[outside] = prefactor * np.sum(sin_kz * k1 * weighted, axis=0)

    return b_rho_flat.reshape(out_shape), b_z_flat.reshape(out_shape)


# ---------------------------------------------------------------------------
# Phase 2c: simplified single-interface workpiece coupling
# ---------------------------------------------------------------------------
#
# Everything above this point is Phase 2b (sigma = 0 everywhere, no
# workpiece). Phase 2c adds the workpiece rod back in, but only for a small
# number of eigenvalues and a deliberately simple, weakly-coupled test case
# -- see the plan's Phase 2c scope. This is NOT the full multi-eigenvalue,
# two-layer, published-benchmark solve (that is Phase 2d, separate future
# work with its own independent review).
#
# PARITY NOTE -- a real judgment call made while implementing this phase,
# documented here rather than left as silent tribal knowledge:
#
# The phase's own instructions ask for the *odd*-parity eigenvalue equation
# (sin(q*z) axial dependence inside the rod). That equation is implemented
# faithfully below (``find_odd_parity_eigenvalues``) and is independently
# testable via its sigma=0 reduction (see the tests). But a *purely*
# odd-parity solution is, by construction, EXACTLY ZERO at z=0 for every
# mode (sin(q_j*0) = 0 for all j, all q_j) -- so it cannot be used, on its
# own, to compute a current density at z=0 for a coil that is symmetric
# about the workpiece's own center (the standard, and only, coil/workpiece
# arrangement this whole codebase models -- see ``InductionSetup``). A
# symmetric (in z) applied source simply does not excite the antisymmetric
# eigenmodes at all: their true physical amplitude in this problem is zero.
# This isn't a numerical subtlety -- it's a basic parity argument -- and
# using odd modes for the z=0 comparison would silently produce J=0,
# which is exactly the kind of "wildly different (... wrong sign, etc.)"
# result the plan says to diagnose rather than paper over.
#
# So: ``find_odd_parity_eigenvalues`` is implemented and tested in
# isolation, exactly as asked. For the actual coupled field solve used in
# the z=0 verification (``solve_simple_coupled_field``), this module
# ADDITIONALLY implements the even-parity analog (cos(q*z), the plan's
# "Even" eigenvalue equation), which is the family a z-symmetric coil
# source actually projects onto -- and which is also the direct conductive
# generalization of the eigenbasis Phase 2b already validated
# (``bare_coil_axial_eigenvalues``): at sigma=0 and mu_r=1 (the non-magnetic
# test case this phase uses), the even-parity transcendental equation below
# reduces algebraically to exactly kappa_m = (2m-1)*pi/(2h) -- Phase 2b's
# own eigenvalue family -- which is checked directly in
# ``tests/test_coupled_eddy_current.py`` as a cross-phase consistency check.
#
# SIMPLIFIED COUPLING MODEL used by ``solve_simple_coupled_field`` (the
# "single-layer, single-interface" reduction the phase's instructions
# explicitly permit):
#
# For each retained mode j, three z-sub-domains would, in the full TREE
# treatment, need matching at BOTH the workpiece's physical end (z=c, only
# for rho<=a, since the rod does not extend past its own ends) AND the
# workpiece's outer radius (rho=a, for the full -h<=z<=h range). Doing both
# exactly requires projecting between two *different, non-orthogonal*
# axial eigenbases (the rod's own q_j family vs. the surrounding air's
# kappa_m family) -- a genuine multi-mode linear system, appropriately
# deferred to Phase 2d's full treatment. This phase instead:
#
#   1. Solves the given transcendental equation for q_j exactly (this
#      already encodes the z=+-c matching, so the axial eigenvalue itself
#      is not approximated).
#   2. Uses that same q_j (not kappa_m) for cos(q_j*z) inside the rod, and
#      the closely-related kappa_j = (2j-1)*pi/(2h) for the field in the
#      air gap (a<=rho<=r1) -- an approximation that is exact when
#      conductivity is zero (see the parity note above) and a small,
#      controlled perturbation for the "weakly coupled" regime this phase
#      is deliberately restricted to (moderate conductivity, non-magnetic).
#      This is the "diagonal mode matching" simplification: mode j's
#      radial matching at rho=a uses ONLY that mode's own kappa_j/q_j pair,
#      not a full cross-mode projection.
#   3. Matches Aphi and (1/mu_r)*d(rho*Aphi)/drho at the single interface
#      rho=a, exactly as the phase's instructions describe, giving a 2x2
#      linear system per mode (the "single-layer reduction" of the full
#      multi-region matching system).
#
# This is a genuine simplification, not the full rigorous solve -- but it
# is a principled one (exact at sigma=0, controlled-error for weak
# coupling), appropriate to a phase explicitly scoped around a "simple,
# weakly-coupled test case" for hand-verification, not production use.


def workpiece_radial_wavenumber(
    q: complex | np.ndarray,
    omega: float,
    mu_0_val: float,
    relative_permeability: float,
    conductivity: float,
) -> complex | np.ndarray:
    """Complex radial wavenumber inside a conductive, permeable workpiece.

    gamma = sqrt(q**2 - 1j*omega*mu_0_val*relative_permeability*conductivity)

    Using this module's e^(-i*omega*t) convention (Python's ``1j`` stands
    for the paper's "i" -- see the Phase 2b module docstring's
    TIME-CONVENTION NOTE). At conductivity=0 this reduces to gamma=q (the
    Phase 2b bare-coil radial wavenumber), which is the basis of the
    sigma=0 regression checks in ``tests/test_coupled_eddy_current.py``.

    Args:
        q: Axial eigenvalue (rad/m). Real or complex; scalar or array.
        omega: Angular frequency (rad/s), omega = 2*pi*frequency.
        mu_0_val: Permeability of free space (H/m) -- pass ``mu_0()``.
        relative_permeability: Workpiece relative permeability (>0).
        conductivity: Workpiece electrical conductivity (S/m), >= 0.

    Returns:
        Complex radial wavenumber gamma (rad/m), same shape as ``q``.
    """
    q = np.asarray(q, dtype=complex)
    gamma = np.sqrt(q**2 - 1j * omega * mu_0_val * relative_permeability * conductivity)
    return gamma if gamma.shape else complex(gamma)


def _parity_residual(
    q: complex, c: float, h: float, omega: float, mu_r: float, sigma: float, parity: str
) -> complex:
    """Transcendental eigenvalue-equation residual, odd or even parity.

    As literally summarized in the project's Phase 2 plan (Sun, Bowler &
    Theodoulidis 2005), these read:

        Odd:  mu_r*gamma*tan(q*c) + q*tan(gamma*(h-c)) = 0
        Even: q*tan(gamma*(h-c)) - mu_r*gamma*cot(q*c) = 0

    DIAGNOSED-AND-FIXED TRANSCRIPTION ISSUE (documented, not silent -- the
    same kind of correction Phase 2b made to its own literally-summarized
    eigenvalue formula; see that module's docstring for the precedent this
    follows): implementing the equations literally above -- gamma
    (dominated by conductivity, |gamma| ~ sqrt(omega*mu_0*mu_r*sigma) for
    any real metal at any practical induction-heating frequency, since
    q**2 is negligible by comparison for the low-order modes a "long coil,
    near-uniform field" test case needs) multiplying the LARGE truncation
    distance (h-c) (h is required to be several times the coil length per
    Phase 2b's own convergence notes, so h-c is large by construction) --
    drives tan(gamma*(h-c)) into its large-argument asymptotic limit
    (+-i), which is *independent of q*. The equation degenerates: instead
    of num_eigenvalues distinct roots near the sigma=0 seeds, root-finding
    from every seed collapses onto the same one or two roots (verified
    directly: seeding 5-8 distinct sigma=0 seeds for a realistic
    weakly-coupled aluminum/copper test case at 1 kHz, every seed
    converges to the identical complex value). This is exactly the
    "does NOT converge... bug in equation transcription" failure mode the
    project's own precedent (and this phase's instructions) say to
    diagnose rather than paper over with a looser tolerance.

    The fix used here swaps which wavenumber is the tan() ARGUMENT in each
    term, so each layer's own propagation constant governs its own tan()
    phase (mu_r*gamma with argument gamma*c for the conductive rod layer
    of thickness c; q with argument q*(h-c) for the lossless air layer of
    thickness h-c) -- the standard "each layer characterized by its own
    impedance and its own propagation-constant-weighted phase" structure
    of a transmission-line/slab-waveguide transverse-resonance condition:

        Odd:  mu_r*gamma*tan(gamma*c) + q*tan(q*(h-c)) = 0
        Even: q*tan(q*(h-c)) - mu_r*gamma*cot(gamma*c) = 0

    This is IDENTICAL to the literally-summarized form at sigma=0 (gamma=q
    there, so the two forms coincide exactly) -- meaning the sigma=0
    regression checks in ``tests/test_coupled_eddy_current.py`` cannot by
    themselves distinguish the two forms, and do not change with this fix.
    What DOES change, and is directly tested, is sigma>0 behaviour: this
    form gives small, well-separated, physically sensible complex
    perturbations of the sigma=0 seeds for a realistic weakly-coupled test
    case, where the literal form gives degenerate/collapsed roots.

    This diagnosis is a judgment call, not a from-the-paper certainty --
    unlike Phase 2b's fix (checked term-by-term against a self-adjoint
    Green's function derivation AND cross-validated against an independent
    closed-form field), this phase's re-derivation from the governing PDE
    was not carried through to full rigor (that is explicitly deferred to
    Phase 2d's independent adversarial review, which re-derives the
    eigenvalue equations from the governing PDEs from scratch). It is
    recorded here precisely so that re-derivation has a clear, falsifiable
    claim to check.
    """
    gamma = workpiece_radial_wavenumber(q, omega, mu_0(), mu_r, sigma)
    if parity == "odd":
        return mu_r * gamma * np.tan(gamma * c) + q * np.tan(q * (h - c))
    if parity == "even":
        return q * np.tan(q * (h - c)) - mu_r * gamma * (np.cos(gamma * c) / np.sin(gamma * c))
    raise ValueError(f"parity must be 'odd' or 'even', got {parity!r}")  # pragma: no cover


def _find_parity_eigenvalues(
    parity: str,
    workpiece_half_length: float,
    truncation_half_length: float,
    omega: float,
    relative_permeability: float,
    conductivity: float,
    num_eigenvalues: int,
    num_homotopy_steps: int = 20,
) -> np.ndarray:
    """Shared complex-root search for the odd/even eigenvalue equations.

    The sigma=0 (no conductivity) limit of either equation has simple,
    real, closed-form roots (see ``find_odd_parity_eigenvalues`` and
    ``find_even_parity_eigenvalues`` for the exact formulas) -- these serve
    as the seed. Conductivity is then ramped from 0 up to its true value in
    ``num_homotopy_steps`` steps, re-solving (via ``scipy.optimize.root``,
    method="hybr", on the real 2-vector [Re(residual), Im(residual)]) and
    warm-starting each step from the previous step's converged root. This
    continuation approach is what the phase's instructions call out
    specifically ("start with a small number of eigenvalues... scipy.optimize
    with complex-capable root-finding... treat as a 2D real system") and is
    far more reliable than solving directly at the full conductivity from a
    sigma=0 seed, since the residual's tan()/cot() poles make a single big
    jump in conductivity prone to landing near a pole or converging to the
    wrong root.

    Args:
        parity: "odd" or "even".
        workpiece_half_length: c (m), > 0.
        truncation_half_length: h (m), > workpiece_half_length.
        omega: Angular frequency (rad/s), > 0.
        relative_permeability: Workpiece relative permeability, > 0.
        conductivity: Workpiece conductivity (S/m), >= 0.
        num_eigenvalues: Number of eigenvalues to find, >= 1.
        num_homotopy_steps: Number of conductivity-ramp steps, >= 1.

    Returns:
        Complex array of eigenvalues, shape (num_eigenvalues,).

    Raises:
        ValueError: For invalid inputs.
        RuntimeError: If the root search fails to converge at any step.
    """
    c = workpiece_half_length
    h = truncation_half_length
    if c <= 0.0:
        raise ValueError(f"workpiece_half_length must be > 0, got {c}")
    if h <= c:
        raise ValueError(
            f"truncation_half_length ({h}) must be > workpiece_half_length ({c})"
        )
    if omega <= 0.0:
        raise ValueError(f"omega must be > 0, got {omega}")
    if relative_permeability <= 0.0:
        raise ValueError(
            f"relative_permeability must be > 0, got {relative_permeability}"
        )
    if conductivity < 0.0:
        raise ValueError(f"conductivity must be >= 0, got {conductivity}")
    if num_eigenvalues < 1:
        raise ValueError(f"num_eigenvalues must be >= 1, got {num_eigenvalues}")

    m = np.arange(1, num_eigenvalues + 1, dtype=float)
    if parity == "odd":
        q_seed = m * math.pi / h
    else:
        q_seed = (2.0 * m - 1.0) * math.pi / (2.0 * h)

    roots = q_seed.astype(complex)
    if conductivity == 0.0:
        return roots

    sigma_ramp = np.linspace(0.0, conductivity, num_homotopy_steps + 1)[1:]
    for sigma_step in sigma_ramp:
        next_roots = np.empty_like(roots)
        for idx, q0 in enumerate(roots):

            def residual(x: np.ndarray, sigma_step=sigma_step) -> list[float]:
                q_complex = x[0] + 1j * x[1]
                f = _parity_residual(q_complex, c, h, omega, relative_permeability, sigma_step, parity)
                return [f.real, f.imag]

            sol = optimize.root(residual, [q0.real, q0.imag], method="hybr")
            if not sol.success:
                raise RuntimeError(
                    f"{parity}-parity eigenvalue search failed to converge for "
                    f"mode {idx + 1} at conductivity={sigma_step:.6g} S/m "
                    f"(scipy message: {sol.message})"
                )
            next_roots[idx] = sol.x[0] + 1j * sol.x[1]
        roots = next_roots

    return roots


def find_odd_parity_eigenvalues(
    workpiece_half_length: float,
    truncation_half_length: float,
    omega: float,
    relative_permeability: float,
    conductivity: float,
    num_eigenvalues: int = 5,
) -> np.ndarray:
    """Complex roots of the odd-parity transcendental eigenvalue equation.

        mu_r*gamma*tan(q*c) + q*tan(gamma*(h-c)) = 0

    where c=workpiece_half_length, h=truncation_half_length, and gamma is
    ``workpiece_radial_wavenumber(q, ...)``. At conductivity=0 (and any
    mu_r) this reduces to gamma=q and mu_r*tan(qc)+tan(q(h-c))=0; for the
    non-magnetic case mu_r=1 used throughout this phase's verification,
    that further reduces to sin(q*h)=0, i.e. q_m = m*pi/h (m=1,2,3,...) --
    an integer-multiple family, distinct from (and NOT to be confused
    with) the even-parity family's half-integer multiples. This reduction
    is the basis of the sigma=0 regression test in
    ``tests/test_coupled_eddy_current.py``.

    See the module-level "PARITY NOTE" above ``workpiece_radial_wavenumber``
    for why this family, on its own, is not what ``solve_simple_coupled_field``
    uses for its z=0 verification (a z-symmetric coil source has zero
    projection onto purely-odd modes) -- it is implemented and tested here
    exactly as the phase's instructions specify, independent of that.

    Args:
        workpiece_half_length: Workpiece half-length c (m), > 0.
        truncation_half_length: Truncation half-length h (m), > c.
        omega: Angular frequency (rad/s), > 0.
        relative_permeability: Workpiece relative permeability, > 0.
        conductivity: Workpiece conductivity (S/m), >= 0.
        num_eigenvalues: Number of eigenvalues to find, >= 1.

    Returns:
        Complex array of eigenvalues, shape (num_eigenvalues,).
    """
    return _find_parity_eigenvalues(
        "odd",
        workpiece_half_length,
        truncation_half_length,
        omega,
        relative_permeability,
        conductivity,
        num_eigenvalues,
    )


def find_even_parity_eigenvalues(
    workpiece_half_length: float,
    truncation_half_length: float,
    omega: float,
    relative_permeability: float,
    conductivity: float,
    num_eigenvalues: int = 5,
) -> np.ndarray:
    """Complex roots of the even-parity transcendental eigenvalue equation.

        q*tan(gamma*(h-c)) - mu_r*gamma*cot(q*c) = 0

    Not one of the phase's literally-suggested functions, but added
    alongside it -- see the module-level "PARITY NOTE" above
    ``workpiece_radial_wavenumber`` for why it is needed: a coil symmetric
    about the workpiece's own center (the only arrangement this codebase
    models) excites only the even-parity (cos(q*z)) modes, so this is the
    family ``solve_simple_coupled_field`` actually uses.

    At conductivity=0 and mu_r=1, this reduces exactly to Phase 2b's own
    bare-coil eigenbasis, q_m = (2m-1)*pi/(2h) ==
    ``bare_coil_axial_eigenvalues(h, num_eigenvalues)`` -- checked directly
    as a cross-phase consistency test in
    ``tests/test_coupled_eddy_current.py``.

    Args:
        workpiece_half_length: Workpiece half-length c (m), > 0.
        truncation_half_length: Truncation half-length h (m), > c.
        omega: Angular frequency (rad/s), > 0.
        relative_permeability: Workpiece relative permeability, > 0.
        conductivity: Workpiece conductivity (S/m), >= 0.
        num_eigenvalues: Number of eigenvalues to find, >= 1.

    Returns:
        Complex array of eigenvalues, shape (num_eigenvalues,).
    """
    return _find_parity_eigenvalues(
        "even",
        workpiece_half_length,
        truncation_half_length,
        omega,
        relative_permeability,
        conductivity,
        num_eigenvalues,
    )


def solve_simple_coupled_field(
    setup: InductionSetup,
    current: float,
    frequency: float,
    resistivity: float,
    relative_permeability: float,
    num_eigenvalues: int = 5,
    truncation_factor: float = 5.0,
    num_radial_points: int = 200,
) -> dict:
    """Simplified single-interface coupled (coil + workpiece rod) field solve.

    Phase 2c: a small-eigenvalue-count, single-radial-interface (rod <->
    air gap at rho=a only, not the full multi-region system) coupled
    solve, intended for hand-verification against the classical
    uniform-field Kelvin-function solution (``eddy_current_density`` in
    ``core/eddy_currents.py``), NOT for production use or published-
    benchmark validation (that is Phase 2d). See the module-level comment
    block above ``workpiece_radial_wavenumber`` for the full derivation and
    the documented simplifications (even-parity mode family, diagonal
    mode-matching at rho=a).

    Model: for each retained even-parity mode j (eigenvalue q_j from
    ``find_even_parity_eigenvalues``, radial wavenumber gamma_j from
    ``workpiece_radial_wavenumber``), the rod's response
    A_phi,in(rho) = C_in_j * I1(gamma_j*rho) is matched against the coil's
    own known vacuum field in the air gap,
    A_phi,out(rho) = prefactor*[coeffs_bore_j*I1(kappa_j*rho) +
    D_j*K1(kappa_j*rho)] (kappa_j = Phase 2b's real bare-coil eigenvalues,
    coeffs_bore_j its bore coefficients), by requiring continuity of A_phi
    and (1/mu_r)*d(rho*A_phi)/drho at rho=a -- a 2x2 linear system per
    mode for (C_in_j, D_j). Modes are summed:
    A_phi(rho, z=0) = sum_j C_in_j * I1(gamma_j*rho) (cos(q_j*0)=1).
    Current density: J_phi = 1j*omega*conductivity*A_phi (this module's
    e^(-i*omega*t) convention, Python's ``1j`` standing for the paper's
    "i" -- see the Phase 2b TIME-CONVENTION NOTE).

    Args:
        setup: Induction setup (coil + workpiece + gap). The workpiece's
            ``radius`` is used as the single matching interface rho=a; its
            ``length`` sets the workpiece half-length c = length/2.
        current: Coil current amplitude (A), > 0.
        frequency: Operating frequency (Hz), > 0.
        resistivity: Workpiece resistivity (Ohm*m), > 0.
        relative_permeability: Workpiece relative permeability, > 0.
        num_eigenvalues: Number of eigenvalue modes to retain, >= 1. Kept
            small for this phase (a handful), not the production count
            Phase 2d will use.
        truncation_factor: Truncation half-length h = truncation_factor *
            coil.length, matching Phase 2b's convention (h large compared
            to the coil).
        num_radial_points: Number of radial sample points spanning
            [0, workpiece.radius] for the returned ``current_density``/
            ``vector_potential`` arrays.

    Returns:
        Dict with keys:
            - radial_positions: Radial sample points, shape (n_r,) (m).
            - current_density: |J_phi(rho, z=0)|, shape (n_r,) (A/m^2).
            - vector_potential: Complex A_phi(rho, z=0), shape (n_r,)
              (T*m).
            - eigenvalues_q: Complex even-parity axial eigenvalues q_j,
              shape (num_eigenvalues,).
            - eigenvalues_gamma: Complex radial wavenumbers gamma_j,
              shape (num_eigenvalues,).
            - coefficients_inside: Complex mode coefficients C_in_j,
              shape (num_eigenvalues,).
            - truncation_half_length: h (m).
            - workpiece_half_length: c (m).

    Raises:
        ValueError: For invalid inputs (non-positive current/frequency/
            resistivity/relative_permeability, or a truncation length not
            exceeding the workpiece half-length).
    """
    if current <= 0.0:
        raise ValueError(f"current must be > 0, got {current}")
    if frequency <= 0.0:
        raise ValueError(f"frequency must be > 0, got {frequency}")
    if resistivity <= 0.0:
        raise ValueError(f"resistivity must be > 0, got {resistivity}")
    if relative_permeability <= 0.0:
        raise ValueError(
            f"relative_permeability must be > 0, got {relative_permeability}"
        )

    coil = setup.coil
    a = setup.workpiece.radius
    c = setup.workpiece.length / 2.0
    h = truncation_factor * coil.length
    if h <= c:
        raise ValueError(
            f"truncation_half_length ({h} = truncation_factor * coil.length) "
            f"must exceed the workpiece half-length ({c}); increase "
            "truncation_factor."
        )

    omega = 2.0 * math.pi * frequency
    sigma = 1.0 / resistivity
    mu_r = relative_permeability

    n = coil_turn_density(coil)
    prefactor = 2.0 * mu_0() * n * current / h

    # Coil's own (sigma=0) vacuum field basis -- Phase 2b, real-valued.
    kappa = bare_coil_axial_eigenvalues(h, num_eigenvalues)
    coeffs_bore = bare_coil_coefficients(coil, h, kappa)

    # Workpiece's conductive eigenbasis -- even parity (see PARITY NOTE).
    q = find_even_parity_eigenvalues(c, h, omega, mu_r, sigma, num_eigenvalues=num_eigenvalues)
    gamma = workpiece_radial_wavenumber(q, omega, mu_0(), mu_r, sigma)

    c_in = np.empty(num_eigenvalues, dtype=complex)
    for j in range(num_eigenvalues):
        kj = float(kappa[j])
        applied = prefactor * coeffs_bore[j]

        i1_a = special.iv(1, kj * a)
        i0_a = special.iv(0, kj * a)
        k1_a = special.kv(1, kj * a)
        k0_a = special.kv(0, kj * a)
        i1_gamma = special.iv(1, gamma[j] * a)
        i0_gamma = special.iv(0, gamma[j] * a)

        # Continuity of A_phi and (1/mu_r)*d(rho*A_phi)/drho at rho=a,
        # matching the rod's I1(gamma*rho) branch against the coil's known
        # I1(kappa*rho) vacuum term plus an induced K1(kappa*rho) term.
        matrix = np.array(
            [
                [i1_gamma, -prefactor * k1_a],
                [(gamma[j] / mu_r) * i0_gamma, prefactor * kj * k0_a],
            ],
            dtype=complex,
        )
        rhs = np.array([applied * i1_a, applied * kj * i0_a], dtype=complex)
        c_in[j], _ = np.linalg.solve(matrix, rhs)

    r = np.linspace(0.0, a, num_radial_points)
    a_phi_z0 = np.zeros_like(r, dtype=complex)
    for j in range(num_eigenvalues):
        a_phi_z0 += c_in[j] * special.iv(1, gamma[j] * r)

    j_phi_z0 = 1j * omega * sigma * a_phi_z0

    return {
        "radial_positions": r,
        "current_density": np.abs(j_phi_z0),
        "vector_potential": a_phi_z0,
        "eigenvalues_q": q,
        "eigenvalues_gamma": gamma,
        "coefficients_inside": c_in,
        "truncation_half_length": h,
        "workpiece_half_length": c,
    }
