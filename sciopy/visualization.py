import matplotlib.pyplot as plt
import numpy as np
import math
import os
from typing import Tuple
from .prepare_data import comp_tank_relative_r_phi
from sciopy.prepare_data import norm_data


def plot_potential_matrix(sample: np.lib.npyio.NpzFile) -> None:
    """
    Plot the potential matrix of a prepared sample.

    Parameters
    ----------
    sample : np.lib.npyio.NpzFile
        prepared sample
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12, 4))
    ax1.set_title(r"$\Re\{P_m\}$")
    ax1.imshow(np.real(sample["potential_matrix"]))
    ax2.set_title(r"$\Im\{P_m\}$")
    ax2.imshow(np.imag(sample["potential_matrix"]))
    ax3.set_title(r"$|P_m|$")
    ax3.imshow(np.abs(sample["potential_matrix"]))
    fig.tight_layout()
    plt.show()


def plot_el_sign(sample: np.lib.npyio.NpzFile, norm: bool = False) -> None:
    """
    Plot the real, imaginary and absolute part of a sample.

    Parameters
    ----------
    sample : np.lib.npyio.NpzFile
        prepared sample
    norm : bool, optional
        normalization between 0 and 1, by default False
    """

    n_el = sample["config"].tolist()["n_el"]
    steps = len(sample["v_without_ext"]) / n_el

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 9))
    ax1.set_title(r"Real signal part without excitation electrodes")
    ax1.set_ylabel(r"$\Re\{\phi\}$")
    ax2.set_title(r"Imaginary signal part without excitation electrodes")
    ax2.set_ylabel(r"$\Im\{\phi\}$")
    ax3.set_title(r"Absolute signal without excitation electrodes")
    ax3.set_ylabel(r"$|\phi|$")
    if norm is False:
        real = np.real(sample["v_without_ext"])
        imag = np.imag(sample["v_without_ext"])
        absol = np.abs(sample["v_without_ext"])
        ax1.stem(real)
        ax2.stem(imag)
        ax3.stem(absol)
        for el in range(n_el):
            ax1.fill_betweenx(
                (np.min(real), np.max(real)),
                el * (n_el - 2),
                (el + 1) * (n_el - 2),
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
            ax2.fill_betweenx(
                (np.min(imag), np.max(imag)),
                el * (n_el - 2),
                (el + 1) * (n_el - 2),
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
            ax3.fill_betweenx(
                (0, np.max(absol)),
                el * (n_el - 2),
                (el + 1) * (n_el - 2),
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
        # ax1.legend(bbox_to_anchor=(1.1, 1.05))
    if norm is True:
        ax1.stem(norm_data(np.real(sample["v_without_ext"])))
        ax2.stem(norm_data(np.imag(sample["v_without_ext"])))
        ax3.stem(norm_data(np.abs(sample["v_without_ext"])))
        for el in range(n_el):
            ax1.fill_betweenx(
                (0, 1),
                el * steps,
                (el + 1) * steps,
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
            ax2.fill_betweenx(
                (0, 1),
                el * steps,
                (el + 1) * steps,
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
            ax3.fill_betweenx(
                (0, 1),
                el * steps,
                (el + 1) * steps,
                facecolor=f"C{el%2}",
                alpha=0.4,
                label=f"group {el+1}",
            )
    fig.tight_layout()
    plt.show()
