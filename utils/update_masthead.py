"""update_masthead inserts the Pi logo, docs, and headers into each Colab notebook.

run this script from the root of the repository with `python3.11 utils/update_masthead.py`
"""

import json
from pathlib import Path

def get_colab_link(filename: str) -> dict:
  return {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        f"<a href=\"https://colab.research.google.com/github/withpi/cookbook-withpi/blob/main/colabs/{filename}.ipynb\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    }

MASTHEAD = {  "cell_type": "markdown",
      "source": [
        "<a href=\"https://withpi.ai\"><img src=\"https://play.withpi.ai/logo/logoFullBlack.svg\" width=\"240\"></a>\n",
        "\n",
        "<a href=\"https://code.withpi.ai\"><font size=\"4\">Documentation</font></a>\n",
        "\n",
        "<a href=\"https://build.withpi.ai\"><font size=\"4\">Copilot</font></a>"
      ],
      "metadata": {
        "id": "pi-masthead"
      }
    }
  
PI_SETUP_MARKDOWN = {
      "cell_type": "markdown",
      "source": [
        "## Install and initialize SDK\n",
        "\n",
        "You'll need a `WITHPI_API_KEY` from https://build.withpi.ai/account.  Add it to your notebook secrets (the key symbol) on the left.\n",
        "\n",
        "Run the cell below to install packages and load the SDK"
      ],
      "metadata": {
        "id": "pi-setup-markdown"
      }
    }

#PI_SETUP_GPU_MARKDOWN = {
#      "cell_type": "markdown",
#      "source": [
#        "## Install and initialize SDK\n",
#        "\n",
#        "This notebook needs a T4 GPU.  Make sure to select this explicitly above before proceeding.\n",
#        "\n",
#        "You'll need a WITHPI_API_KEY from https://play.withpi.ai.  Add it to your notebook secrets (the key symbol) on the left.\n",
#        "\n",
#        "Run the cell below to install packages and load the SDK"
#      ],
#      "metadata": {
#        "id": "pi-setup-markdown"
#      }
#    }

#SHARED_SOURCE = Path("utils/shared.py.txt").read_text().strip().split("\n")
#GPU_SOURCE = Path("utils/gpu.py.txt").read_text().strip().split("\n")

#PI_SETUP_GPU = {
#      "cell_type": "code",
#      "metadata": {
#        "id": "pi-setup"
#      },
#      "outputs": [],
#      "execution_count": None,
#      "source": [f"{line}\n" for line in SHARED_SOURCE + [''] + GPU_SOURCE]
#    }

#PI_SETUP = {
#      "cell_type": "code",
#      "metadata": {
#        "id": "pi-setup"
#      },
#      "outputs": [],
#      "execution_count": None,
#      "source": [f"{line}\n" for line in SHARED_SOURCE]
#    }
  
#GPU_NOTEBOOKS = [
#  "Low_Rank_Adaptation"
#]

def write_cell(colab, cell, index):
  identifier = cell["metadata"]["id"]
  if colab["cells"][index]["metadata"]["id"] == identifier:
    colab["cells"][index] = cell
  else:
    colab["cells"].insert(index, cell)
  

def main():
    all_files = list(Path("./colabs").glob("*.ipynb"))
    if len(all_files) == 0:
        raise ValueError("No Colab notebooks found. Please run this script from the root of the repository.")
    for f in all_files:
        colab = json.loads(f.read_text())
        write_cell(colab, get_colab_link(f.stem), 0)
        write_cell(colab, MASTHEAD, 1)
        # 2 should be the introduction cell specific to the notebook

        #write_cell(colab, PI_SETUP_MARKDOWN, 3)
        #write_cell(colab, PI_SETUP, 4)
        #write_cell(colab, PI_SETUP_GPU_MARKDOWN if f.stem in GPU_NOTEBOOKS else PI_SETUP_MARKDOWN, 3)
        #write_cell(colab, PI_SETUP_GPU if f.stem in GPU_NOTEBOOKS else PI_SETUP, 4)
        # For cleanliness, purge outputs and execution counts from all cells.
        for cell in colab["cells"]:
            #if "outputs" in cell:
            #  cell["outputs"] = []
            if "execution_count" in cell:
              cell["execution_count"] = None
        colab["metadata"]["language_info"] = { "name": "python" }
        f.write_text(json.dumps(colab, indent=2))

if __name__ == "__main__":
    main()
