"""Parser for Track3P output files."""

import re
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers import Parser


class Track3pParser(Parser):
    """Parse Track3P particle tracking solver output.

    Extracts particle statistics, impact counts, and multipacting indicators.
    """

    def parse(self, **kwargs):
        """Parse Track3P output and store tracking results."""
        try:
            output_folder = self.retrieved
            with output_folder.open("track3p.out", "r") as f:
                content = f.read()
        except (FileNotFoundError, OSError):
            return self.exit_codes.ERROR_NO_OUTPUT

        # Parse particle statistics
        n_emitted = None
        n_absorbed = None
        n_impacts = None

        emitted_match = re.search(r"Total.*emitted.*?(\d+)", content, re.IGNORECASE)
        absorbed_match = re.search(r"Total.*absorbed.*?(\d+)", content, re.IGNORECASE)
        impacts_match = re.search(r"Total.*impacts.*?(\d+)", content, re.IGNORECASE)

        if emitted_match:
            n_emitted = int(emitted_match.group(1))
        if absorbed_match:
            n_absorbed = int(absorbed_match.group(1))
        if impacts_match:
            n_impacts = int(impacts_match.group(1))

        if n_emitted is not None and n_emitted == 0:
            return self.exit_codes.ERROR_NO_PARTICLES

        # Parse SEY (secondary emission yield) if available
        sey_match = re.search(r"Average SEY.*?([\d.]+)", content, re.IGNORECASE)
        avg_sey = float(sey_match.group(1)) if sey_match else None

        results = {
            "n_emitted": n_emitted,
            "n_absorbed": n_absorbed,
            "n_impacts": n_impacts,
            "average_sey": avg_sey,
            "multipacting_detected": avg_sey is not None and avg_sey > 1.0,
        }

        self.out("results", Dict(dict=results))
        return ExitCode(0)
