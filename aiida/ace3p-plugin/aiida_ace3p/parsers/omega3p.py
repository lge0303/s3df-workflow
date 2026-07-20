"""Parser for Omega3P output files."""

import re
from aiida.engine import ExitCode
from aiida.orm import Dict
from aiida.parsers import Parser


class Omega3pParser(Parser):
    """Parse Omega3P eigenmode solver output.

    Extracts eigenvalues, frequencies, residuals, and mesh statistics
    from the solver output file.
    """

    def parse(self, **kwargs):
        """Parse Omega3P output and store eigenvalues."""
        try:
            output_folder = self.retrieved
            with output_folder.open("omega3p.out", "r") as f:
                content = f.read()
        except (FileNotFoundError, OSError):
            return self.exit_codes.ERROR_NO_OUTPUT

        eigenvalues = []
        frequencies = []
        residuals = []

        # Parse eigenvalue blocks
        eigenvalue_pattern = re.compile(
            r"Eigenvalue:\s+([\d.eE+\-]+)\s+"
            r"Frequency:\s+([\d.eE+\-]+)\s+"
            r"Residual:\s+([\d.eE+\-]+)"
        )
        for match in eigenvalue_pattern.finditer(content):
            eigenvalues.append(float(match.group(1)))
            frequencies.append(float(match.group(2)))
            residuals.append(float(match.group(3)))

        if not eigenvalues:
            return self.exit_codes.ERROR_NO_EIGENVALUES

        # Parse mesh info
        n_elements = None
        n_dofs = None
        elem_match = re.search(r"Total Number of Elements used:\s+(\d+)", content)
        dof_match = re.search(r"Total Number of DOFs:\s+(\d+)", content)
        if elem_match:
            n_elements = int(elem_match.group(1))
        if dof_match:
            n_dofs = int(dof_match.group(1))

        results = {
            "eigenvalues": eigenvalues,
            "frequencies": frequencies,
            "residuals": residuals,
            "n_modes": len(eigenvalues),
            "n_elements": n_elements,
            "n_dofs": n_dofs,
            "converged": all(r < 1e-7 for r in residuals),
        }

        self.out("eigenvalues", Dict(dict=results))
        return ExitCode(0)
