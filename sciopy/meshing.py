"""*WIP* module for mesh generation and plotting"""

from typing import Union
import matplotlib.pyplot as plt
import numpy as np

import pyeit.mesh as mesh
from pyeit.mesh import PyEITMesh
from pyeit.mesh.wrapper import PyEITAnomaly_Circle


def create_empty_2d_mesh(
    n_el: int = 16,
    h0: float = 0.1,
    z_level: Union[int, float] = 0,
    default_perm: float = 1.0,
) -> PyEITMesh:
    """
    Creates an empty mesh object.
    With a view to 3D reconstruction, a z-level can also be assigned.

    Parameters
    ----------
    n_el : int, optional
        number of used electrodes, by default 16
    h0 : float, optional
        mesh refinement, by default 0.1
    z_level : Union[int, float], optional
        z-level of this 2d mesh, by default 0
    default_perm : float
        empty ground permittivity value

    Returns
    -------
    PyEITMesh
        pyeit mesh object
    """
    mesh_obj = mesh.create(n_el=n_el, h0=h0)
    mesh_obj.node[:, 2] = z_level
    mesh_obj.el_pos = np.roll(np.arange(16)[::-1], -3)
    if default_perm != 1.0:
        mesh_obj.perm_array = mesh_obj.perm_array * default_perm
        mesh_obj.perm = default_perm

    return mesh_obj


def add_circle_anomaly(
    mesh_obj: PyEITMesh,
    x_center: float,
    y_center: float,
    radius: float,
    perm: float = 10,
) -> PyEITMesh:
    """
    Add a circle anomaly to an input PyEITMesh object.

    Parameters
    ----------
    mesh_obj : PyEITMesh
        input mesh object
    x_center : float
        x-center point of the circle anomaly
    y_center : float
        y-center point of the circle anomaly
    radius : float
        radius of the anomaly in percent relating the unit circle
    perm : float, optional
        permittivity of the circle anomaly, by default 10

    Returns
    -------
    PyEITMesh
        _description_
    """
    anomaly = PyEITAnomaly_Circle(center=[x_center, y_center], r=radius, perm=perm)
    mesh_new = mesh.set_perm(mesh_obj, anomaly=anomaly, background=mesh_obj.perm)

    return mesh_new


def plot_mesh(
    mesh_obj: PyEITMesh, figsize: tuple = (6, 4), title: str = "mesh"
) -> None:
    """
    Plot a given PyEITMesh mesh object.

    Parameters
    ----------
    mesh_obj : PyEITMesh
        mesh object
    figsize : tuple, optional
        figsize, by default (6, 4)
    title : str, optional
        title of the figure, by default "mesh"
    """
    plt.style.use("default")
    pts = mesh_obj.node
    tri = mesh_obj.element
    x, y = pts[:, 0], pts[:, 1]
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)
    ax.tripcolor(
        x,
        y,
        tri,
        np.real(mesh_obj.perm_array),
        edgecolors="k",
        shading="flat",
        alpha=0.5,
        cmap=plt.cm.viridis,
    )
    # draw electrodes
    ax.plot(x[mesh_obj.el_pos], y[mesh_obj.el_pos], "ro")
    for i, e in enumerate(mesh_obj.el_pos):
        ax.text(x[e], y[e], str(i + 1), size=12)
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_ylim([-1.2, 1.2])
    ax.set_xlim([-1.2, 1.2])
    fig.set_size_inches(6, 6)
    plt.show()


def mesh_sample(
    sample: np.lib.npyio.NpzFile,
    h0: float = 0.05,
    empty_perm: float = 1.0,
    obj_perm: float = 10.0,
    x_y_offset: float = 180,
    tank_r_inner: float = 97.0,
) -> PyEITMesh:
    """
    Generate the 2D mesh of a single measured sample.

    Parameters
    ----------
    sample : np.lib.npyio.NpzFile
        loaded sample
    h0 : float, optional
        mesh refinement, by default 0.05
    empty_perm : float, optional
        permittivity of the empty area, by default 1.0
    obj_perm : float, optional
        permittivity of the object, by default 10.0
    x_y_offset : float, optional
        x,y offset due to the Ender 5, by default 180
    tank_r_inner : float, optional
        inner radius of the ScioSpecEIT phantom tank, by default 97.0

    Returns
    -------
    PyEITMesh
        _description_
    """
    ender_stat = sample["enderstat"].tolist()
    abs_x_pos = (ender_stat["abs_x_pos"] - x_y_offset) / tank_r_inner
    abs_y_pos = (ender_stat["abs_y_pos"] - x_y_offset) / tank_r_inner
    abs_z_pos = ender_stat["abs_z_pos"]
    print(f"{abs_x_pos=},{abs_y_pos=}")
    cnfg = sample["config"].tolist()

    mesh_obj = create_empty_2d_mesh(
        n_el=cnfg.n_el, h0=h0, z_level=abs_z_pos, default_perm=empty_perm
    )

    if cnfg.object == "circle":
        mesh_obj = add_circle_anomaly(
            mesh_obj, abs_x_pos, abs_y_pos, cnfg.size, obj_perm
        )
        return mesh_obj
    else:
        # TBD: Implementing other geometries
        print("This kind of object geometry has to be implementet.")
        print("\tReturn empty mesh")
        return mesh_obj
