"""Convert a .eit file to python sctructured data"""

import os
import numpy as np
import pickle
from .sciopy_dataclasses import SingleEitFrame


header_keys = [
    "number_of_header",
    "file_version_number",
    "setup_name",
    "date_time",
    "f_min",
    "f_max",
    "f_scale",
    "f_count",
    "current_amplitude",
    "framerate",
    "phase_correct_parameter",
    "uknwn_1",  # TBD: Sadly an unknown parameter.
    "uknwn_2",  # TBD: Sadly an unknown parameter.
    "uknwn_3",  # TBD: Sadly an unknown parameter.
    "uknwn_4",  # TBD: Sadly an unknown parameter.
    "uknwn_5",  # TBD: Sadly an unknown parameter.
    "MeasurementChannels",
    "MeasurementChannelsIndependentFromInjectionPattern",
]


def doteit_in_SingleEitFrame(read_content: list) -> SingleEitFrame:
    """
    Returns single object without saving anything.

    Parameters
    ----------
    read_content : list
        the 1st param name `first`

    Returns
    -------
    SingleEitFrame
        class object
    """
    frame = SingleEitFrame()

    for content, key in zip(read_content, header_keys):
        # Inserting header part
        setattr(frame, key, content)
    frame.f_scale = "linear" if frame.f_scale == 0 else "logarithmic"

    for i in range(len(header_keys), len(read_content) - 1, 2):
        el_cmb = read_content[i].split(" ")
        el_cmb = f"{el_cmb[0]}_{el_cmb[1]}"
        lct = read_content[i + 1].split("\t")
        lct = [ele.replace("E", "e") for ele in lct]
        lct = [float(ele) for ele in lct]
        fin_val = np.zeros(len(lct) // 2, dtype=complex)
        for idx, cmpl in enumerate(range(0, len(lct), 2)):
            fin_val[idx] = complex(lct[cmpl], lct[cmpl + 1])
        setattr(frame, el_cmb, np.array(fin_val))
    return frame


def list_eit_files(path: str) -> list:
    """
    Returns a list of all .eit files in the directory path.

    Parameters
    ----------
    path : str
        Path to the directory

    Returns
    -------
    list
        list of files with .eit ending
    """
    global src_list
    try:
        src_list = [_ for _ in os.listdir(path) if _.endswith(".eit")]
        return src_list
    except BaseException:
        print(f"Can not find a .eit file in:\n {path}")


def list_all_files(path: str) -> None:
    """
    Print a list of all files inside a directory.

    Parameters
    ----------
    path : str
        path to the directory

    Returns
    -------
    None
    """
    print(os.listdir(path))


def single_eit_in_pickle(fname: str, s_path: str) -> None:
    """
    Dumps the .eit information to a pickle file.

    Parameters
    ----------
    fname : str
        name of the file
    s_path : str
        save path

    Returns
    -------
    None
    """
    with open(fname, "r") as file:
        read_content = file.read().split("\n")

    frame = doteit_in_SingleEitFrame(read_content)

    with open(f"{s_path}/{frame.setup_name}.pickle", "wb") as f:
        pickle.dump(frame, f)


def load_pickle_to_dict(path: str) -> dict:
    """
    Load a pickle file into a python dictionary.

    Parameters
    ----------
    path : str
        path to the file

    Returns
    -------
    dict
        dicionary of the loaded pickle file
    """
    tmp = np.load(path, allow_pickle=True).__dict__
    return tmp


def convert_fulldir_doteit_to_pickle(lpath: str, spath: str) -> None:
    """
    Converts all .eit files in a directory to .pickle files in a directory spath.

    Parameters
    ----------
    lpath : str
        load path
    spath : str
        save path

    Returns
    -------
    None
    """
    objects = list_eit_files(lpath)
    for obj in objects:
        fname = lpath + obj
        single_eit_in_pickle(fname, spath)
        print("converted:", obj)
    print("\t Saved in", spath)


def convert_fulldir_doteit_to_npz(lpath: str, spath: str) -> None:
    """
    Converts all .eit files in a directory to .npz files in a directory spath.

    Parameters
    ----------
    lpath : str
        load path
    spath : str
        save path

    Returns
    -------
    None
    """
    objects = list_eit_files(lpath)
    for obj in objects:
        fname = lpath + obj
        with open(fname, "r") as file:
            read_content = file.read().split("\n")

        frame = doteit_in_SingleEitFrame(read_content)
        np.savez(f"{spath}{frame.setup_name}.npz", **(frame.__dict__))
