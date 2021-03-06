# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for SinhArcsinh Bijector."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np

# pylint: disable=g-importing-member
from tensorflow.contrib.distributions.python.ops.bijectors.sinh_arcsinh import SinhArcsinh
from tensorflow.python.ops.distributions.bijector_test_util import assert_bijective_and_finite
from tensorflow.python.ops.distributions.bijector_test_util import assert_scalar_congruency
from tensorflow.python.platform import test

# pylint: enable=g-importing-member


class SinhArcsinhBijectorTest(test.TestCase):
  """Tests correctness of the power transformation."""

  def testBijectorVersusNumpyRewriteOfBasicFunctions(self):
    with self.test_session():
      skewness = 0.2
      tailweight = 2.0
      bijector = SinhArcsinh(
          skewness=skewness,
          tailweight=tailweight,
          event_ndims=1,
          validate_args=True)
      self.assertEqual("sinh_arcsinh", bijector.name)
      x = np.array([[[-2.01], [2.], [1e-4]]]).astype(np.float32)
      y = np.sinh((np.arcsinh(x) + skewness) * tailweight)
      self.assertAllClose(y, bijector.forward(x).eval())
      self.assertAllClose(x, bijector.inverse(y).eval())
      self.assertAllClose(
          np.sum(
              np.log(np.cosh(np.arcsinh(y) / tailweight - skewness)) -
              np.log(tailweight) - np.log(np.sqrt(y**2 + 1)),
              axis=-1), bijector.inverse_log_det_jacobian(y).eval())
      self.assertAllClose(
          -bijector.inverse_log_det_jacobian(y).eval(),
          bijector.forward_log_det_jacobian(x).eval(),
          rtol=1e-4,
          atol=0.)

  def testLargerTailWeightPutsMoreWeightInTails(self):
    with self.test_session():
      # Will broadcast together to shape [3, 2].
      x = [-1., 1.]
      tailweight = [[0.5], [1.0], [2.0]]
      bijector = SinhArcsinh(tailweight=tailweight, validate_args=True)
      y = bijector.forward(x).eval()

      # x = -1, 1 should be mapped to points symmetric about 0
      self.assertAllClose(y[:, 0], -1. * y[:, 1])

      # forward(1) should increase as tailweight increases, since higher
      # tailweight should map 1 to a larger number.
      forward_1 = y[:, 1]  # The positive values of y.
      self.assertLess(forward_1[0], forward_1[1])
      self.assertLess(forward_1[1], forward_1[2])

  def testSkew(self):
    with self.test_session():
      # Will broadcast together to shape [3, 2].
      x = [-1., 1.]
      skewness = [[-1.], [0.], [1.]]
      bijector = SinhArcsinh(skewness=skewness, validate_args=True)
      y = bijector.forward(x).eval()

      # For skew < 0, |forward(-1)| > |forward(1)|
      self.assertGreater(np.abs(y[0, 0]), np.abs(y[0, 1]))

      # For skew = 0, |forward(-1)| = |forward(1)|
      self.assertAllClose(np.abs(y[1, 0]), np.abs(y[1, 1]))

      # For skew > 0, |forward(-1)| < |forward(1)|
      self.assertLess(np.abs(y[2, 0]), np.abs(y[2, 1]))

  def testScalarCongruencySkewness1Tailweight0p5(self):
    with self.test_session():
      bijector = SinhArcsinh(skewness=1.0, tailweight=0.5, validate_args=True)
      assert_scalar_congruency(bijector, lower_x=-2., upper_x=2.0, rtol=0.05)

  def testScalarCongruencySkewnessNeg1Tailweight1p5(self):
    with self.test_session():
      bijector = SinhArcsinh(skewness=-1.0, tailweight=1.5, validate_args=True)
      assert_scalar_congruency(bijector, lower_x=-2., upper_x=2.0, rtol=0.05)

  def testBijectiveAndFiniteSkewnessNeg1Tailweight0p5(self):
    with self.test_session():
      bijector = SinhArcsinh(skewness=-1., tailweight=0.5, validate_args=True)
      # Increasing upper logspace limit to 10 results in Inf due to y**2 being
      # Inf.
      x = np.concatenate((-np.logspace(-2, 9, 1000), [0], np.logspace(
          -2, 9, 1000))).astype(np.float32)
      assert_bijective_and_finite(bijector, x, x, rtol=1e-3)

  def testBijectiveAndFiniteSkewness2Tailweight3(self):
    with self.test_session():
      bijector = SinhArcsinh(skewness=1., tailweight=3., validate_args=True)
      x = np.concatenate((-np.logspace(-2, 5, 1000), [0], np.logspace(
          -2, 5, 1000))).astype(np.float32)
      assert_bijective_and_finite(bijector, x, x, rtol=1e-3)

  def testZeroTailweightRaises(self):
    with self.test_session():
      with self.assertRaisesOpError("not positive"):
        SinhArcsinh(tailweight=0., validate_args=True).forward(1.0).eval()


if __name__ == "__main__":
  test.main()
