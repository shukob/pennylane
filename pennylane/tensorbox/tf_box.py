# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This module contains the TensorFlowBox implementation of the TensorBox API.
"""
import tensorflow as tf


try:
    from tensorflow.python.eager.tape import should_record_backprop
except ImportError:
    from tensorflow.python.eager.tape import should_record as should_record_backprop


import pennylane as qml


class TensorFlowBox(qml.TensorBox):
    """Implements the :class:`~.TensorBox` API for TensorFlow tensors.

    For more details, please refer to the :class:`~.TensorBox` documentation.
    """

    @property
    def interface(self):
        return "tf"

    def __len__(self):
        if isinstance(self.unbox(), tf.Variable):
            return len(tf.convert_to_tensor(self.unbox()))

        return super().__len__()

    @staticmethod
    def stack(values, axis=0):
        res = tf.stack(TensorFlowBox.unbox_list(values), axis=axis)
        return TensorFlowBox(res)

    @property
    def shape(self):
        return tuple(self.unbox().shape)

    def expand_dims(self, axis):
        return TensorFlowBox(tf.expand_dims(self.unbox(), axis=axis))

    def numpy(self):
        return self.unbox().numpy()

    def ones_like(self):
        return TensorFlowBox(tf.ones_like(self.unbox()))

    @property
    def T(self):
        return TensorFlowBox(tf.transpose(self.unbox()))

    @property
    def requires_grad(self):
        return should_record_backprop([self.astensor(self.unbox())])

    @staticmethod
    def astensor(tensor):
        return tf.convert_to_tensor(tensor)
