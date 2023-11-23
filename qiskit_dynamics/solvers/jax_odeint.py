# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
# pylint: disable=invalid-name

"""
Wrapper for jax.experimental.ode.odeint
"""

from typing import Callable, Optional, Union, Tuple, List
import numpy as np
from scipy.integrate._ivp.ivp import OdeResult

from qiskit_dynamics.dispatch import requires_backend
from qiskit_dynamics.array import Array, wrap

from .solver_utils import merge_t_args_jax, trim_t_results_jax

try:
    from jax.experimental.ode import odeint as _odeint

    odeint = wrap(_odeint)
except ImportError:
    pass

lambda_map = {} 

@requires_backend("jax")
def jax_odeint(
    rhs: Callable,
    t_span: Array,
    y0: Array,
    t_eval: Optional[Union[Tuple, List, Array]] = None,
    **kwargs,
):
    """Routine for calling `jax.experimental.ode.odeint`

    Args:
        rhs: Callable of the form :math:`f(t, y)`
        t_span: Interval to solve over.
        y0: Initial state.
        t_eval: Optional list of time points at which to return the solution.
        **kwargs: Optional arguments to be passed to ``odeint``.

    Returns:
        OdeResult: Results object.
    """
    global lambda_map 

    t_list = merge_t_args_jax(t_span, t_eval)

    # determine direction of integration
    t_direction = np.sign(Array(t_list[-1] - t_list[0], backend="jax", dtype=complex))
    print("rhs id ",id(rhs))
    if rhs in lambda_map:
        rhs_lambda = lambda_map[rhs]
    else:
        wrhs = wrap(rhs)
        lambda_map[rhs] = (lambda y, t: wrhs(np.real(t_direction * t), y) * t_direction)
        rhs_lambda = lambda_map[rhs]
    print("rhs lambda id", id(rhs_lambda))

    results = odeint(
        #lambda y, t: rhs(np.real(t_direction * t), y) * t_direction,
        rhs_lambda,
        y0=Array(y0, dtype=complex),
        t=np.real(t_direction) * Array(t_list),
        **kwargs,
    )

    results = OdeResult(t=t_list, y=Array(results, backend="jax", dtype=complex))

    return trim_t_results_jax(results, t_eval)
