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
"""Unit tests for the TensorBox functional API in pennylane.tensorbox.fn
"""
import itertools
import numpy as onp
import pytest

import pennylane as qml
from pennylane import numpy as np
from pennylane.tensorbox import fn


tf = pytest.importorskip("tensorflow", minversion="2.1")
torch = pytest.importorskip("torch")


class TestGetMultiTensorbox:
    """Tests for the _get_multi_tensorbox utility function"""

    def test_exception_tensorflow_and_torch(self):
        """Test that an exception is raised if the sequence of tensors contains
        tensors from incompatible dispatch libraries"""
        x = tf.Variable([1.0, 2.0, 3.0])
        y = onp.array([0.5, 0.1])
        z = torch.tensor([0.6])

        with pytest.raises(ValueError, match="Tensors contain mixed types"):
            fn._get_multi_tensorbox([x, y, z])

    def test_warning_tensorflow_and_autograd(self):
        """Test that a warning is raised if the sequence of tensors contains
        both tensorflow and autograd tensors."""
        x = tf.Variable([1.0, 2.0, 3.0])
        y = np.array([0.5, 0.1])

        with pytest.warns(UserWarning, match="Consider replacing Autograd with vanilla NumPy"):
            fn._get_multi_tensorbox([x, y])

    def test_warning_torch_and_autograd(self):
        """Test that a warning is raised if the sequence of tensors contains
        both torch and autograd tensors."""
        x = torch.tensor([1.0, 2.0, 3.0])
        y = np.array([0.5, 0.1])

        with pytest.warns(UserWarning, match="Consider replacing Autograd with vanilla NumPy"):
            fn._get_multi_tensorbox([x, y])

    def test_return_tensorflow_box(self):
        """Test that TensorFlow is correctly identified as the dispatching library."""
        x = tf.Variable([1.0, 2.0, 3.0])
        y = onp.array([0.5, 0.1])

        res = fn._get_multi_tensorbox([y, x])
        assert res.interface == "tf"

    def test_return_torch_box(self):
        """Test that Torch is correctly identified as the dispatching library."""
        x = torch.tensor([1.0, 2.0, 3.0])
        y = onp.array([0.5, 0.1])

        res = fn._get_multi_tensorbox([y, x])
        assert res.interface == "torch"

    def test_return_autograd_box(self):
        """Test that autograd is correctly identified as the dispatching library."""
        x = np.array([1.0, 2.0, 3.0])
        y = [0.5, 0.1]

        res = fn._get_multi_tensorbox([y, x])
        assert res.interface == "autograd"

    def test_return_numpy_box(self):
        """Test that NumPy is correctly identified as the dispatching library."""
        x = onp.array([1.0, 2.0, 3.0])
        y = [0.5, 0.1]

        res = fn._get_multi_tensorbox([y, x])
        assert res.interface == "numpy"


test_data = [
    (1, 2, 3),
    [1, 2, 3],
    onp.array([1, 2, 3]),
    np.array([1, 2, 3]),
    torch.tensor([1, 2, 3]),
    tf.Variable([1, 2, 3]),
    tf.constant([1, 2, 3]),
]


@pytest.mark.parametrize("t1,t2", list(itertools.combinations(test_data, r=2)))
def test_allequal(t1, t2):
    """Test that the allequal function works for a variety of inputs."""
    res = fn.allequal(t1, t2)

    if isinstance(t1, tf.Variable):
        t1 = tf.convert_to_tensor(t1)

    if isinstance(t2, tf.Variable):
        t2 = tf.convert_to_tensor(t2)

    expected = all(float(x) == float(y) for x, y in zip(t1, t2))
    assert res == expected


@pytest.mark.parametrize("t1,t2", list(itertools.combinations(test_data, r=2)))
def test_allclose(t1, t2):
    """Test that the allclose function works for a variety of inputs."""
    res = fn.allclose(t1, t2)

    if isinstance(t1, tf.Variable):
        t1 = tf.convert_to_tensor(t1)

    if isinstance(t2, tf.Variable):
        t2 = tf.convert_to_tensor(t2)

    expected = all(float(x) == float(y) for x, y in zip(t1, t2))
    assert res == expected


class TestCast:
    """Tests for the cast function"""

    @pytest.mark.parametrize("t", test_data)
    def test_cast_numpy(self, t):
        """Test that specifying a NumPy dtype results in proper casting
        behaviour"""
        res = fn.cast(t, onp.float64)
        assert fn.get_interface(res) == fn.get_interface(t)

        if hasattr(res, "numpy"):
            # if tensorflow or pytorch, extract view of underlying data
            res = res.numpy()
            t = t.numpy()

        assert onp.issubdtype(onp.asarray(t).dtype, onp.integer)
        assert res.dtype.type is onp.float64

    @pytest.mark.parametrize("t", test_data)
    def test_cast_numpy_dtype(self, t):
        """Test that specifying a NumPy dtype object results in proper casting
        behaviour"""
        res = fn.cast(t, onp.dtype("float64"))
        assert fn.get_interface(res) == fn.get_interface(t)

        if hasattr(res, "numpy"):
            # if tensorflow or pytorch, extract view of underlying data
            res = res.numpy()
            t = t.numpy()

        assert onp.issubdtype(onp.asarray(t).dtype, onp.integer)
        assert res.dtype.type is onp.float64

    @pytest.mark.parametrize("t", test_data)
    def test_cast_numpy_string(self, t):
        """Test that specifying a NumPy dtype via a string results in proper casting
        behaviour"""
        res = fn.cast(t, "float64")
        assert fn.get_interface(res) == fn.get_interface(t)

        if hasattr(res, "numpy"):
            # if tensorflow or pytorch, extract view of underlying data
            res = res.numpy()
            t = t.numpy()

        assert onp.issubdtype(onp.asarray(t).dtype, onp.integer)
        assert res.dtype.type is onp.float64

    def test_cast_tensorflow_dtype(self):
        """If the tensor is a TensorFlow tensor, casting using a TensorFlow dtype
        will also work"""
        t = tf.Variable([1, 2, 3])
        res = fn.cast(t, tf.complex128)
        assert isinstance(res, tf.Tensor)
        assert res.dtype is tf.complex128

    def test_cast_torch_dtype(self):
        """If the tensor is a Torch tensor, casting using a Torch dtype
        will also work"""
        t = torch.tensor([1, 2, 3], dtype=torch.int64)
        res = fn.cast(t, torch.float64)
        assert isinstance(res, torch.Tensor)
        assert res.dtype is torch.float64


cast_like_test_data = [
    (1, 2, 3),
    [1, 2, 3],
    onp.array([1, 2, 3], dtype=onp.int64),
    np.array([1, 2, 3], dtype=np.int64),
    torch.tensor([1, 2, 3], dtype=torch.int64),
    tf.Variable([1, 2, 3], dtype=tf.int64),
    tf.constant([1, 2, 3], dtype=tf.int64),
    (1.0, 2.0, 3.0),
    [1.0, 2.0, 3.0],
    onp.array([1, 2, 3], dtype=onp.float64),
    np.array([1, 2, 3], dtype=np.float64),
    torch.tensor([1, 2, 3], dtype=torch.float64),
    tf.Variable([1, 2, 3], dtype=tf.float64),
    tf.constant([1, 2, 3], dtype=tf.float64),
]


@pytest.mark.parametrize("t1,t2", list(itertools.combinations(cast_like_test_data, r=2)))
def test_cast_like(t1, t2):
    """Test that casting t1 like t2 results in t1 being cast to the same datatype as t2"""
    res = fn.cast_like(t1, t2)

    # if tensorflow or pytorch, extract view of underlying data
    if hasattr(res, "numpy"):
        res = res.numpy()

    if hasattr(t2, "numpy"):
        t2 = t2.numpy()

    assert fn.allequal(res, t1)
    assert onp.asarray(res).dtype.type is onp.asarray(t2).dtype.type


class TestConvertLike:
    """tests for the convert like function"""

    @pytest.mark.parametrize("t1,t2", list(itertools.combinations(test_data, r=2)))
    def test_convert_tensor_like(self, t1, t2):
        """Test that converting t1 like t2 results in t1 being cast to the same tensor type as t2"""
        res = fn.convert_like(t1, t2)

        # if tensorflow or pytorch, extract view of underlying data
        if hasattr(res, "numpy"):
            res = res.numpy()

        if hasattr(t2, "numpy"):
            t2 = t2.numpy()

        assert fn.allequal(res, t1)
        assert isinstance(res, np.ndarray if isinstance(t2, (list, tuple)) else t2.__class__)

    @pytest.mark.parametrize("t_like", [np.array([1]), tf.constant([1]), torch.tensor([1])])
    def test_convert_scalar(self, t_like):
        """Test that a python scalar is converted to a scalar tensor"""
        res = fn.convert_like(5, t_like)
        assert isinstance(res, t_like.__class__)
        assert res.ndim == 0
        assert fn.allequal(res, [5])


# the following test data is of the form
# [original shape, axis to expand, new shape]
expand_dims_test_data = [
    [tuple(), 0, (1,)],
    [(3,), 0, (1, 3)],
    [(3,), 1, (3, 1)],
    [(2, 2), 0, (1, 2, 2)],
    [(2, 2), 1, (2, 1, 2)],
    [(2, 2), 2, (2, 2, 1)],
]


@pytest.mark.parametrize("shape,axis,new_shape", expand_dims_test_data)
class TestExpandDims:
    """Tests for the expand_dims function"""

    def test_expand_dims_sequence(self, shape, axis, new_shape):
        """Test that expand_dimensions works correctly
        when given a sequence"""
        if not shape:
            pytest.skip("Cannot expand the dimensions of a Python scalar!")

        t1 = np.empty(shape).tolist()
        t2 = fn.expand_dims(t1, axis=axis)
        assert t2.shape == new_shape

    def test_expand_dims_array(self, shape, axis, new_shape):
        """Test that expand_dimensions works correctly
        when given an array"""
        t1 = np.empty(shape)
        t2 = fn.expand_dims(t1, axis=axis)
        assert t2.shape == new_shape
        assert isinstance(t2, np.ndarray)

    def test_expand_dims_torch(self, shape, axis, new_shape):
        """Test that the expand dimensions works correctly
        when given a torch tensor"""
        t1 = torch.empty(shape)
        t2 = fn.expand_dims(t1, axis=axis)
        assert t2.shape == new_shape
        assert isinstance(t2, torch.Tensor)

    def test_expand_dims_tf(self, shape, axis, new_shape):
        """Test that the expand dimensions works correctly
        when given a TF tensor"""
        t1 = tf.ones(shape)
        t2 = fn.expand_dims(t1, axis=axis)
        assert t2.shape == new_shape
        assert isinstance(t2, tf.Tensor)


interface_test_data = [
    [(1, 2, 3), "numpy"],
    [[1, 2, 3], "numpy"],
    [onp.array([1, 2, 3]), "numpy"],
    [np.array([1, 2, 3]), "autograd"],
    [torch.tensor([1, 2, 3]), "torch"],
    [tf.Variable([1, 2, 3]), "tf"],
    [tf.constant([1, 2, 3]), "tf"],
]


@pytest.mark.parametrize("t,interface", interface_test_data)
def test_get_interface(t, interface):
    """Test that the interface of a tensor-like object

    is correctly returned."""
    res = fn.get_interface(t)
    assert res == interface


@pytest.mark.parametrize("t", test_data)
def test_toarray(t):
    """Test that the toarray method correctly converts the input
    tensor into a NumPy array."""
    res = fn.toarray(t)
    assert fn.allequal(res, t)
    assert isinstance(res, onp.ndarray)


class TestOnesLike:
    """Tests for the ones_like function"""

    @pytest.mark.parametrize("t", cast_like_test_data)
    def test_ones_like_inferred_dtype(self, t):
        """Test that the ones like function creates the correct
        shape and type tensor."""
        res = fn.ones_like(t)

        if isinstance(t, (list, tuple)):
            t = onp.asarray(t)

        assert res.shape == t.shape
        assert fn.get_interface(res) == fn.get_interface(t)
        assert fn.allclose(res, np.ones(t.shape))

        # if tensorflow or pytorch, extract view of underlying data
        if hasattr(res, "numpy"):
            res = res.numpy()
            t = t.numpy()

        assert onp.asarray(res).dtype.type is onp.asarray(t).dtype.type

    @pytest.mark.parametrize("t", cast_like_test_data)
    def test_ones_like_explicit_dtype(self, t):
        """Test that the ones like function creates the correct
        shape and type tensor."""
        res = fn.ones_like(t, dtype=np.float16)

        if isinstance(t, (list, tuple)):
            t = onp.asarray(t)

        assert res.shape == t.shape
        assert fn.get_interface(res) == fn.get_interface(t)
        assert fn.allclose(res, np.ones(t.shape))

        # if tensorflow or pytorch, extract view of underlying data
        if hasattr(res, "numpy"):
            res = res.numpy()
            t = t.numpy()

        assert onp.asarray(res).dtype.type is np.float16


class TestRequiresGrad:
    """Tests for the requires_grad function"""

    @pytest.mark.parametrize("t", [(1, 2, 3), [1, 2, 3], onp.array([1, 2, 3])])
    def test_numpy(self, t):
        """Vanilla NumPy arrays, sequences, and lists will always return False"""
        assert not fn.requires_grad(t)

    def test_autograd(self):
        """Autograd arrays will simply return their requires_grad attribute"""
        t = np.array([1.0, 2.0], requires_grad=True)
        assert fn.requires_grad(t)

        t = np.array([1.0, 2.0], requires_grad=False)
        assert not fn.requires_grad(t)

    def test_torch(self):
        """Torch tensors will simply return their requires_grad attribute"""
        t = torch.tensor([1.0, 2.0], requires_grad=True)
        assert fn.requires_grad(t)

        t = torch.tensor([1.0, 2.0], requires_grad=False)
        assert not fn.requires_grad(t)

    def test_tf(self):
        """TensorFlow tensors will True *if* they are being watched by a gradient tape"""
        t1 = tf.Variable([1.0, 2.0])
        t2 = tf.constant([1.0, 2.0])
        assert not fn.requires_grad(t1)
        assert not fn.requires_grad(t2)

        with tf.GradientTape():
            # variables are automatically watched within a context,
            # but constants are not
            assert fn.requires_grad(t1)
            assert not fn.requires_grad(t2)

        with tf.GradientTape() as tape:
            # watching makes all tensors trainable
            tape.watch([t1, t2])
            assert fn.requires_grad(t1)
            assert fn.requires_grad(t2)


shape_test_data = [
    tuple(),
    (3,),
    (2, 2),
    (3, 2, 2),
    (2, 1, 1, 2),
]


@pytest.mark.parametrize(
    "interface,create_array",
    [
        ("sequence", lambda shape: np.empty(shape).tolist()),
        ("autograd", np.empty),
        ("torch", torch.empty),
        ("tf", tf.ones),
    ],
)
@pytest.mark.parametrize("shape", shape_test_data)
def test_shape(shape, interface, create_array):
    """Test that the shape of tensors is correctly returned"""
    if interface == "sequence" and not shape:
        pytest.skip("Cannot expand the dimensions of a Python scalar!")

    t = create_array(shape)
    assert fn.shape(t) == shape


class TestStack:
    """Tests for the stack function"""

    def test_stack_array(self):
        """Test that stack, called without the axis arguments, stacks vertically"""
        t1 = [0.6, 0.1, 0.6]
        t2 = np.array([0.1, 0.2, 0.3])
        t3 = onp.array([5.0, 8.0, 101.0])

        res = fn.stack([t1, t2, t3])
        assert isinstance(res, np.ndarray)
        assert np.all(res == np.stack([t1, t2, t3]))

    def test_stack_tensorflow(self):
        """Test that stack, called without the axis arguments, stacks vertically"""
        t1 = tf.constant([0.6, 0.1, 0.6])
        t2 = tf.Variable([0.1, 0.2, 0.3])
        t3 = onp.array([5.0, 8.0, 101.0])

        res = fn.stack([t1, t2, t3])
        assert isinstance(res, tf.Tensor)
        assert np.all(res.numpy() == np.stack([t1.numpy(), t2.numpy(), t3]))

    def test_stack_torch(self):
        """Test that stack, called without the axis arguments, stacks vertically"""
        t1 = onp.array([5.0, 8.0, 101.0], dtype=np.float64)
        t2 = torch.tensor([0.6, 0.1, 0.6], dtype=torch.float64)
        t3 = torch.tensor([0.1, 0.2, 0.3], dtype=torch.float64)

        res = fn.stack([t1, t2, t3])
        assert isinstance(res, torch.Tensor)
        assert np.all(res.numpy() == np.stack([t1, t2.numpy(), t3.numpy()]))

    @pytest.mark.parametrize("t1", [onp.array([1, 2]), torch.tensor([1, 2]), tf.constant([1, 2])])
    def test_stack_axis(self, t1):
        """Test that passing the axis argument allows for stacking along
        a different axis"""
        t2 = onp.array([3, 4])
        res = fn.stack([t1, t2], axis=1)

        # if tensorflow or pytorch, extract view of underlying data
        if hasattr(res, "numpy"):
            res = res.numpy()

        assert fn.allclose(res, np.array([[1, 3], [2, 4]]))


@pytest.mark.parametrize("t", test_data)
def test_T(t):
    """Test the simple transpose (T) function"""
    res = fn.T(t)

    if isinstance(t, (list, tuple)):
        t = onp.asarray(t)

    assert fn.get_interface(res) == fn.get_interface(t)

    # if tensorflow or pytorch, extract view of underlying data
    if hasattr(res, "numpy"):
        res = res.numpy()
        t = t.numpy()

    assert np.all(res.T == t.T)
