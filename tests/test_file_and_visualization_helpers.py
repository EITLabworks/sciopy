import pickle
from types import SimpleNamespace

import numpy as np

from sciopy.doteit import list_eit_files, load_pickle_to_dict
from sciopy.visualization import norm_data


def test_list_eit_files_is_filtered_case_insensitively_and_sorted(tmp_path):
    (tmp_path / "b.eit").touch()
    (tmp_path / "A.EIT").touch()
    (tmp_path / "ignored.txt").touch()

    assert list_eit_files(tmp_path) == ["A.EIT", "b.eit"]


def test_load_pickle_to_dict_reads_pickled_objects(tmp_path):
    path = tmp_path / "sample.pickle"
    with path.open("wb") as file:
        pickle.dump(SimpleNamespace(value=42), file)

    assert load_pickle_to_dict(path) == {"value": 42}


def test_norm_data_handles_constant_arrays():
    assert np.array_equal(norm_data(np.array([5.0, 5.0])), np.array([0.0, 0.0]))


def test_norm_data_scales_to_unit_interval():
    assert np.allclose(norm_data(np.array([2.0, 4.0, 6.0])), [0.0, 0.5, 1.0])
