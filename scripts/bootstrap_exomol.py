import click
from urllib.request import urlretrieve
import pathlib
import time
import sys

molecules = {
    "H2O": "https://exomol.com/db/H2O/1H2-16O/POKAZATEL/1H2-16O__POKAZATEL__R15000_0.3-50mu.xsec.TauREx.h5",
    "CH4": "https://exomol.com/db/CH4/12C-1H4/MM/12C-1H4__MM.R15000_0.3-50mu.xsec.TauREx.h5",
    "NH3": "https://exomol.com/db/NH3/14N-1H3/CoYuTe/14N-1H3__CoYuTe.R15000_0.3-50mu.xsec.TauREx.h5",
    "CO2": "https://exomol.com/db/CO2/12C-16O2/UCL-4000/12C-16O2__UCL-4000.R15000_0.3-50mu.xsec.TauREx.h5",
    "SO3": "https://exomol.com/db/H2O2/1H2-16O2/APTY/1H2-16O2__APTY.R15000_0.3-50mu.xsec.TauREx.h5",
    "SO2": "https://exomol.com/db/SO2/32S-16O2/ExoAmes/32S-16O2__ExoAmes.R15000_0.3-50mu.xsec.TauREx.h5",
    "H2CO": "https://exomol.com/db/H2CO/1H2-12C-16O/AYTY/1H2-12C-16O__AYTY.R15000_0.3-50mu.xsec.TauREx.h5",
    "PH3": "https://exomol.com/db/PH3/31P-1H3/SAlTY/31P-1H3__SAlTY.R15000_0.3-50mu.xsec.TauREx.h5",
    "HCN": "https://exomol.com/db/HCN/1H-12C-14N/Harris/1H-12C-14N__Harris.R15000_0.3-50mu.xsec.TauREx.h5",
    "TiO": "https://exomol.com/db/TiO/48Ti-16O/Toto/48Ti-16O__Toto.R15000_0.3-50mu.xsec.TauREx.h5",
    "VO": "https://exomol.com/db/VO/51V-16O/HyVO/51V-16O__HyVO.R15000_0.3-50mu.xsec.TauREx.h5",
}


# From https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html
def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write(
        "\r...%d%%, %d MB, %d KB/s, %d seconds passed"
        % (percent, progress_size / (1024 * 1024), speed, duration)
    )
    sys.stdout.flush()


@click.command()
@click.option(
    "--molecule",
    "-m",
    multiple=True,
    type=click.Choice(list(molecules.keys()) + ["all"]),
)
@click.option(
    "--output-dir", "-o", type=click.Path(exists=False, dir_okay=True, file_okay=False)
)
def download_exomol_data(molecule, output_dir):
    if "all" in molecule:
        molecule = molecules.keys()

    for m in molecule:
        print(f"Downloading {m}")
        url = molecules[m]
        output_dir = pathlib.Path(output_dir)
        filename = url.split("/")[-1]
        output_file = output_dir / filename
        urlretrieve(url, output_file, reporthook=reporthook)


if __name__ == "__main__":
    download_exomol_data()
