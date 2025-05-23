
import struct
import matplotlib.pyplot as plt
import pathlib
import io
import numpy as np
from typing import Generator
from taurex.opacity import InterpolatingOpacity, InterpModeType
from typing import Optional, TypedDict
import numpy.typing as npt


class HitranCrossSectionData(TypedDict):
    """TypedDict for HITRAN cross section data."""
    molecule_name: str
    min_wavenumber: float
    max_wavenumber: float
    number_of_points: int
    temperature: float
    pressure: float
    max_cross_section_value: float
    instrument_resolution: float
    common_name: str
    empty: str
    broadener: str
    reference: str
    grid: npt.NDArray[np.float64]
    cross_sections: npt.NDArray[np.float64]

def read_hitran_header_format(line: str) ->dict :
    """Read the header format.
    
    The Header format is a string line defined by there parameters and field lengths:

    - Molecule name (20 characters)
    - Minimum wavenumber cm-1 (10 characters)
    - Maximum wavenumber cm-1 (10 characters)
    - Number of points (7 characters)
    - Temperature (7 characters)
    - Pressure (6 characters)
    - Maximum cross-section-value  (10 characters)
    - Instrument resolution (5 characters)
    - Common name (15 characters)
    - Empty (4 characters)
    - Broadener (3 characters)
    - Reference (3 characters)
    
    
    """
    # Define the format string for unpacking
    format_string = '>20s10s10s7s7s6s10s5s15s4s3s3s'
    # Unpack the line using the defined format
    unpacked_data = struct.unpack(format_string, line.encode('utf-8'))
    # Convert bytes to strings and strip whitespace
    unpacked_data = [data.decode('utf-8').strip() if isinstance(data, bytes) else data for data in unpacked_data]
    
    fields= ["molecule_name", "min_wavenumber", "max_wavenumber", "number_of_points", "temperature", "pressure", "max_cross_section_value", "instrument_resolution", "common_name", "empty", "broadener", "reference"]

    result = {field: value for field, value in zip(fields, unpacked_data)}

    if not result["broadener"]:
        result["broadener"] = "self"

    result["min_wavenumber"] = float(result["min_wavenumber"])
    result["max_wavenumber"] = float(result["max_wavenumber"])
    result["number_of_points"] = int(result["number_of_points"])
    result["temperature"] = float(result["temperature"])
    result["pressure"] = float(result["pressure"])
    result["max_cross_section_value"] = float(result["max_cross_section_value"])
    result["instrument_resolution"] = float(result["instrument_resolution"])



    return result


def create_grid_from_header(header: dict) -> dict:
    """Create a grid from the header information.
    
    The grid is created based on the minimum and maximum wavenumber, number of points, and temperature.

    deltav = (max_wavenumber - min_wavenumber) / (number_of_points-1)

    """
    import numpy as np
    
    delta_v = (header["max_wavenumber"] - header["min_wavenumber"]) / (header["number_of_points"] - 1)

    grid = np.arange(header["min_wavenumber"], header["max_wavenumber"] + delta_v, delta_v)

    if grid.size != header["number_of_points"]:
        raise ValueError(f"Grid size {grid.size} does not match number of points {header['number_of_points']}")

    return grid



def read_cross_section_pair(filebuffer: io.BufferedIOBase)-> Generator[HitranCrossSectionData, None, None]:

    while True:
        header_data = filebuffer.readline()
        if not header_data:
            break
        
        header = read_hitran_header_format(header_data[:100])
        grid = create_grid_from_header(header)

        total_points_read = 0

        cross_sections = []

        while True:
            data_points = filebuffer.readline().split()
            cross_sections.extend([float(f) for f in data_points])
            total_points_read += len(data_points)
            if total_points_read >= header["number_of_points"]:
                break

        cross_sections = np.array(cross_sections)[:header["number_of_points"]]

        
        yield {
            **header,
            "grid": grid,
            "cross_sections": cross_sections,
        }
    

def load_hitran_cross_section(filename: pathlib.Path | str) -> list[dict]:
    """Load a HITRAN cross section file and return the data as a dictionary."""
    filename = pathlib.Path(filename)
    with open(filename, "r") as f:
        data = []
        for cross_section in read_cross_section_pair(f):
            data.append(cross_section)
    return data


def find_hitran_cross_section_files(directory: pathlib.Path | str) -> list[pathlib.Path]:
    """Find all HITRAN cross section files in a directory."""
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        raise ValueError(f"{directory} is not a directory")
    return list(directory.glob("*.xsc"))

def find_and_map_cross_section_files(directory: pathlib.Path | str) -> dict[str, list[pathlib.Path]]:
    """Find all HITRAN cross section files in a directory and map them to their corresponding molecules."""
    directory = pathlib.Path(directory)
    if not directory.is_dir():
        raise ValueError(f"{directory} is not a directory")
    
    files = find_hitran_cross_section_files(directory)

    molecule_map = {}
    for file in files:
        with open(file, "r") as f:
            header_data = f.readline()
            header = read_hitran_header_format(header_data[:100])
        molecule_name = header["molecule_name"].strip()
        if molecule_name not in molecule_map:
            molecule_map[molecule_name] = []
        molecule_map[molecule_name].append(file)
    
    return molecule_map




class HitranCrossSection(InterpolatingOpacity):
    @classmethod
    def discover(cls) -> list[str, tuple[pathlib.Path, str]]:
        from taurex.cache import GlobalCache
        from taurex.util import sanitize_molecule_string
        path = GlobalCache()["xsec_path"]
        if path is None:
            return []
        path = pathlib.Path(path)
        try:
            molecule_map = find_and_map_cross_section_files(path)
        except ValueError:
            return []

        interp = GlobalCache()["xsec_interpolation"] or "linear"

        discovery = [
            (sanitize_molecule_string(molecule_name), (files, interp))
            for molecule_name, files in molecule_map.items()
        ]
        return discovery

    def __init__(self, files: list[pathlib.Path], interp: InterpModeType = "linear"):
        """Initialize the HitranCrossSection class.
        
        Parameters
        ----------
        files : list[pathlib.Path]
            List of HITRAN cross section files.

        interp : str
            Interpolation mode. Can be 'linear', 'exp'
        
        """
        from taurex.util import sanitize_molecule_string
        super().__init__(self.__class__.__name__, interp)

        self.dataset = [
            load_hitran_cross_section(f)
            for f in files
        ]

        temperatures = np.array([data["temperature"] for data in self.dataset  for gridpoint in data])
        pressures = np.array([data["pressure"] for data in self.dataset  for gridpoint in data])

        grids = np.array([data["grid"] for data in self.dataset  for gridpoint in data])
        cross_sections = np.array([data["cross_sections"] for data in self.dataset  for gridpoint in data])

        # Sort by pressure first, then by temperature
        sorted_indices = np.lexsort((temperatures, pressures))

        self.temperatures = np.unique(temperatures[sorted_indices])
        self.pressures = np.unique(pressures[sorted_indices])
        self.grids = grids[sorted_indices]

        # Check if all the grid points are the same
        # Greate a merged grid and reinterpolate the cross-sections
        if not np.all(np.isclose(self.grids[0], self.grids)):
            # Merge the grids
            flat_grid = flat_grid.ravel()
            unique_grid = np.unique(flat_grid)
            # Interpolate the cross-sections to the new grid
            cross_sections = np.array([
                np.interp(unique_grid, grid, cross_section)
                for grid, cross_section in zip(self.grids, cross_sections)
            ])
            self.wngrid = unique_grid
        else:
            self.wngrid= self.grids[0]

        self.cross_sections = cross_sections[sorted_indices]

        # Reshape the cross-sections to P, T, grid
        self.cross_sections = self.cross_sections.reshape(
            len(self.pressures),
            len(self.temperatures),
            -1,
        )

        self._resolution = np.average(np.diff(self._wavenumber_grid))

        # Convert Torr to Pa
        self.pressures = self.pressures * 133.322368

        molecule = self.dataset[0][0]["molecule_name"]
        molecule_name = sanitize_molecule_string(molecule.split()[0].strip())


        self.molecule_name = molecule_name
        self.files = files
        self.interp = interp

    @property
    def moleculeName(self) -> str:  # noqa: N802
        """Molecule name."""
        return self.molecule_name

    @property
    def xsecGrid(self) -> npt.NDArray[np.float64]:  # noqa: N802
        """Opacity grid."""
        return self.cross_sections
    
    @property
    def wavenumberGrid(self) -> npt.NDArray[np.float64]:  # noqa: N802
        """Wavenumber grid."""
        return self.wngrid

    @property
    def temperatureGrid(self) -> npt.NDArray[np.float64]:  # noqa: N802
        """Temperature grid."""
        return self.temperatures

    @property
    def pressureGrid(self) -> npt.NDArray[np.float64]:  # noqa: N802
        return self.pressures

    @property
    def resolution(self) -> float:  # noqa: N802
        """Resolution of opacity."""
        return self._resolution