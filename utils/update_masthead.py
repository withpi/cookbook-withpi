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
  
PI_SETUP_MARKDOWN = {
      "cell_type": "markdown",
      "source": [
        "## Install and initialize SDK\n",
        "\n",
        "Connect to a regular CPU Python 3 runtime.  You won't need GPUs for this notebook.\n",
        "\n",
        "You'll need a WITHPI_API_KEY from https://play.withpi.ai.  Add it to your notebook secrets (the key symbol) on the left.\n",
        "\n",
        "Run the cell below to install packages and load the SDK"
      ],
      "metadata": {
        "id": "pi-setup-markdown"
      }
    }

PI_SETUP = {
      "cell_type": "code",
      "metadata": {
        "id": "pi-setup"
      },
      "outputs": [],
      "execution_count": None,
      "source": [
        "%%capture\n",
        "\n",
        "%pip install withpi litellm httpx datasets jinja2\n",
        "\n",
        "import os\n",
        "import json\n",
        "from google.colab import userdata\n",
        "from litellm import completion\n",
        "from withpi import PiClient\n",
        "from withpi.types import Contract\n",
        "from pathlib import Path\n",
        "from google.colab import files\n",
        "import datasets\n",
        "import httpx\n",
        "import jinja2\n",
        "\n",
        "os.environ[\"WITHPI_API_KEY\"] = userdata.get('WITHPI_API_KEY')\n",
        "\n",
        "client = PiClient()\n",
        "\n",
        "def print_contract(contract):\n",
        "  for dimension in contract.dimensions:\n",
        "    print(dimension.label)\n",
        "    for sub_dimension in dimension.sub_dimensions:\n",
        "      print(f\"\\t{sub_dimension.description}\")\n",
        "\n",
        "def generate(system: str, user: str, model: str) -> str:\n",
        "  messages = [\n",
        "    {\n",
        "      \"content\": system,\n",
        "      \"role\": \"system\"\n",
        "    },\n",
        "    {\n",
        "      \"content\": user,\n",
        "      \"role\": \"user\"\n",
        "    }\n",
        "  ]\n",
        "  return completion(model=model,\n",
        "                    messages=messages).choices[0].message.content\n",
        "\n",
        "class printer(str):\n",
        "  def __repr__(self):\n",
        "    return self\n",
        "def print_response(response: str):\n",
        "  display(printer(response))\n",
        "\n",
        "def print_scores(pi_scores):\n",
        "  for dimension_name, dimension_scores in pi_scores.dimension_scores.items():\n",
        "    print(f\"{dimension_name}: {dimension_scores.total_score}\")\n",
        "    for subdimension_name, subdimension_score in dimension_scores.subdimension_scores.items():\n",
        "      print(f\"\\t{subdimension_name}: {subdimension_score}\")\n",
        "    print(\"\\n\")\n",
        "  print(\"---------------------\")\n",
        "  print(f\"Total score: {pi_scores.total_score}\")\n",
        "\n",
        "def save_file(filename: str, model):\n",
        "  filename = 'aesop_ai.json'\n",
        "  Path(filename).write_text(model.model_dump_json(indent=2))\n",
        "  files.download(filename)\n",
        "\n",
        "def load_contract(url: str) -> Contract:\n",
        "  resp = httpx.get(url)\n",
        "  return Contract.model_validate_json(resp.content)\n",
        "\n",
        "def load_and_split_dataset(url: str) -> datasets.DatasetDict:\n",
        "  return datasets.load_dataset('parquet', data_files=url, split=\"train\").train_test_split(test_size=0.1)",
      ]
    }

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
        write_cell(colab, PI_SETUP_MARKDOWN, 3)
        write_cell(colab, PI_SETUP, 4)
        # For cleanliness, purge outputs and execution counts from all cells.
        for cell in colab["cells"]:
            if "outputs" in cell:
              cell["outputs"] = []
            if "execution_count" in cell:
              cell["execution_count"] = None
        colab["metadata"]["language_info"] = { "name": "python" }
        f.write_text(json.dumps(colab, indent=2))

if __name__ == "__main__":
    main()
