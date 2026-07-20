"""AiiDA CalcJob for Omega3P eigenmode solver."""

from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.orm import Dict, Int, Float, SinglefileData, RemoteData


class Omega3pCalculation(CalcJob):
    """CalcJob to run Omega3P eigenmode solver.

    Prepares the .omega3p input file, submits the calculation,
    and retrieves eigenvalue results with full provenance tracking.
    """

    _INPUT_FILE = "run.omega3p"
    _OUTPUT_FILE = "omega3p.out"
    _ERROR_FILE = "omega3p.err"

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Inputs
        spec.input("mesh", valid_type=SinglefileData, help="Mesh file (.ncdf)")
        spec.input(
            "parameters",
            valid_type=Dict,
            help="Solver parameters: fe_order, num_eigenvalues, freq_shift, boundaries",
        )
        spec.input(
            "surface_material",
            valid_type=Dict,
            required=False,
            help="Surface material properties (sigma, reference_number)",
        )

        # Outputs
        spec.output("eigenvalues", valid_type=Dict, help="Computed eigenvalues and frequencies")
        spec.output(
            "remote_results",
            valid_type=RemoteData,
            help="Remote directory with mode files",
        )

        # Parser
        spec.input("metadata.options.parser_name", valid_type=str, default="ace3p.omega3p")

        # Resources defaults
        spec.input("metadata.options.resources", valid_type=dict, default={"num_machines": 1, "num_mpiprocs_per_machine": 128})
        spec.input("metadata.options.max_wallclock_seconds", valid_type=int, default=1800)

        # Exit codes
        spec.exit_code(300, "ERROR_NO_OUTPUT", "Omega3P output file not found")
        spec.exit_code(301, "ERROR_NO_EIGENVALUES", "No eigenvalues found in output")
        spec.exit_code(400, "ERROR_SOLVER_FAILED", "Omega3P solver reported an error")

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare input files and submission script."""
        params = self.inputs.parameters.get_dict()

        # Generate .omega3p input file
        mesh_filename = self.inputs.mesh.filename
        input_content = self._generate_input(params, mesh_filename)
        with folder.open(self._INPUT_FILE, "w") as f:
            f.write(input_content)

        # Copy mesh file
        folder.insert_path(self.inputs.mesh.get_file_abs_path(), mesh_filename)

        # Code info
        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = [self._INPUT_FILE]
        codeinfo.stdout_name = self._OUTPUT_FILE
        codeinfo.stderr_name = self._ERROR_FILE

        # Calc info
        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.retrieve_list = [
            self._OUTPUT_FILE,
            self._ERROR_FILE,
            "omega3p_results",
        ]
        return calcinfo

    def _generate_input(self, params: dict, mesh_filename: str) -> str:
        """Generate .omega3p input file content from parameters."""
        boundaries = params.get("boundaries", {})
        magnetic = boundaries.get("magnetic", "1, 2")
        exterior = boundaries.get("exterior", "6")

        content = f"""ModelInfo : {{
  File: ./{mesh_filename}

  BoundaryCondition : {{
    Magnetic: {magnetic}
    Exterior: {exterior}
  }}
"""
        # Surface material (optional)
        if "surface_material" in self.inputs:
            mat = self.inputs.surface_material.get_dict()
            content += f"""
  SurfaceMaterial : {{
    ReferenceNumber: {mat.get('reference_number', 6)}
    Sigma: {mat.get('sigma', 5.8e7)}
  }}
"""
        content += f"""}}

FiniteElement: {{
  Order:           {params.get('fe_order', 2)}
  CurvedSurfaces: {params.get('curved_surfaces', 'on')}
}}

EigenSolver : {{
  NumEigenvalues: {params.get('num_eigenvalues', 2)}
  FrequencyShift:  {params.get('freq_shift', 1.0e9)}
}}

PostProcess : {{
  Toggle: on
  ModeFile: mode
}}
"""
        return content
