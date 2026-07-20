"""AiiDA CalcJob for Track3P particle tracking solver."""

from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.orm import Dict, SinglefileData, RemoteData


class Track3pCalculation(CalcJob):
    """CalcJob to run Track3P multipacting/dark current simulation.

    Requires mode fields from a prior Omega3P calculation.
    Tracks particle trajectories and records surface impacts.
    """

    _INPUT_FILE = "run.track3p"
    _OUTPUT_FILE = "track3p.out"
    _ERROR_FILE = "track3p.err"

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Inputs
        spec.input("mesh", valid_type=SinglefileData, help="Mesh file (.ncdf)")
        spec.input(
            "parameters",
            valid_type=Dict,
            help="Track3P parameters: emission, tracking, material settings",
        )
        spec.input(
            "mode_fields",
            valid_type=RemoteData,
            help="Remote directory containing Omega3P mode files",
        )

        # Outputs
        spec.output("results", valid_type=Dict, help="Tracking statistics and impact counts")
        spec.output(
            "remote_results",
            valid_type=RemoteData,
            help="Remote directory with trajectory and impact files",
        )

        # Parser
        spec.input("metadata.options.parser_name", valid_type=str, default="ace3p.track3p")

        # Resources
        spec.input("metadata.options.resources", valid_type=dict, default={"num_machines": 1, "num_mpiprocs_per_machine": 128})
        spec.input("metadata.options.max_wallclock_seconds", valid_type=int, default=3600)

        # Exit codes
        spec.exit_code(300, "ERROR_NO_OUTPUT", "Track3P output file not found")
        spec.exit_code(301, "ERROR_NO_PARTICLES", "No particles emitted")
        spec.exit_code(400, "ERROR_SOLVER_FAILED", "Track3P solver reported an error")

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare input files and submission script."""
        params = self.inputs.parameters.get_dict()

        input_content = self._generate_input(params)
        with folder.open(self._INPUT_FILE, "w") as f:
            f.write(input_content)

        # Copy mesh
        mesh_filename = self.inputs.mesh.filename
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
        calcinfo.remote_symlink_list = [
            (self.inputs.mode_fields.computer.uuid,
             self.inputs.mode_fields.get_remote_path(),
             "omega3p_results"),
        ]
        calcinfo.retrieve_list = [
            self._OUTPUT_FILE,
            self._ERROR_FILE,
            "track3p_results",
        ]
        return calcinfo

    def _generate_input(self, params: dict) -> str:
        """Generate .track3p input file from parameters."""
        mesh_filename = self.inputs.mesh.filename
        emission = params.get("emission", {})
        tracking = params.get("tracking", {})

        content = f"""ModelInfo : {{
  File: ./{mesh_filename}

  BoundaryCondition : {{
    Magnetic: {params.get('magnetic_bc', '1, 2')}
    Exterior: {params.get('exterior_bc', '6')}
  }}
}}

Particle : {{
  Type: {emission.get('particle_type', 'electron')}
  NumParticles: {emission.get('num_particles', 1000)}
  EmissionModel: {emission.get('model', 'Fowler-Nordheim')}
  BetaFN: {emission.get('beta_fn', 50.0)}
}}

Tracking : {{
  MaxSteps: {tracking.get('max_steps', 200)}
  TimeStep: {tracking.get('time_step', 1.0e-12)}
  MaxTime: {tracking.get('max_time', 1.0e-8)}
}}

RFField : {{
  ResultDir: ./omega3p_results
  ModeID: {params.get('mode_id', 0)}
  Gradient: {params.get('gradient', 2.0e7)}
}}

PostProcess : {{
  Toggle: on
  OutputDir: track3p_results
}}
"""
        return content
