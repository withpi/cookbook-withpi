"""update_masthead inserts the Pi logo, docs, and headers into each Colab notebook.

run this script from the root of the repository with `python3.11 utils/update_masthead.py`
"""

import json
from pathlib import Path

MASTHEAD = {  "cell_type": "markdown",
      "source": [
        "<a href=\"https://withpi.ai\"><img src=\"https://withpi.ai/logoFullBlack.svg\" width=\"240\"></a>\n",
        "\n",
        "<a href=\"https://code.withpi.ai\"><font size=\"4\">Documentation</font></a>\n",
        "\n",
        "<a href=\"https://play.withpi.ai\"><font size=\"4\">Technique Catalog</font></a>"
      ],
      "metadata": {
        "id": "pi-masthead"
      }
    }

def main():
    all_files = list(Path("./colabs").glob("*.ipynb"))
    if len(all_files) == 0:
        raise ValueError("No Colab notebooks found. Please run this script from the root of the repository.")
    for f in all_files:
        colab = json.loads(f.read_text())
        if colab["cells"][1]["metadata"].get("id") == "pi-masthead":
            colab["cells"][1] = MASTHEAD
        else:
            colab["cells"].insert(1, MASTHEAD)
        f.write_text(json.dumps(colab))

if __name__ == "__main__":
    main()
