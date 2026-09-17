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
from scipy import integrate, special

from induction_heating.core.geometry import SolenoidCoil
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
