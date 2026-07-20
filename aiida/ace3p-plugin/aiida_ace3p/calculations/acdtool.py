"""AiiDA CalcJob for ACE3P acdtool utility (mesh conversion, post-processing)."""

from aiida.common.datastructures import CalcInfo, CodeInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob
from aiida.orm import Dict, Str, SinglefileData, RemoteData


class AcdtoolCalculation(CalcJob):
    """CalcJob for acdtool operations: meshconvert, postprocess rf, etc.

    Supports multiple operation modes via the 'operation' input.
    """

    _OUTPUT_FILE = "acdtool.out"
    _ERROR_FILE = "acdtool.err"

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Inputs
        spec.input(
            "operation",
            valid_type=Str,
            help="Operation mode: 'meshconvert' or 'postprocess rf'",
        )
        spec.input(
            "input_file",
            valid_type=SinglefileData,
            help="Input file (.gen for meshconvert, .rfpost for postprocess)",
        )
        spec.input(
            "mode_fields",
            valid_type=RemoteData,
            required=False,
            help="Remote dir with mode files (required for postprocess)",
        )
        spec.input(
            "parameters",
            valid_type=Dict,
            required=False,
            help="Additional parameters for the operation",
        )

        # Outputs
        spec.output("output_file", valid_type=SinglefileData, required=False)
        spec.output("results", valid_type=Dict, required=False)

        # Resources (acdtool typically single-process)
        spec.input("metadata.options.resources", valid_type=dict, default={"num_machines": 1, "num_mpiprocs_per_machine": 1})
        spec.input("metadata.options.max_wallclock_seconds", valid_type=int, default=600)

        # Exit codes
        spec.exit_code(300, "ERROR_NO_OUTPUT", "Expected output not found")
        spec.exit_code(400, "ERROR_TOOL_FAILED", "acdtool reported an error")

    def prepare_for_submission(self, folder: Folder) -> CalcInfo:
        """Prepare acdtool command and input files."""
        operation = self.inputs.operation.value
        input_filename = self.inputs.input_file.filename

        folder.insert_path(self.inputs.input_file.get_file_abs_path(), input_filename)

        # Build command line
        if operation == "meshconvert":
            cmdline = ["meshconvert", input_filename]
        elif operation == "postprocess rf":
            cmdline = ["postprocess", "rf", input_filename]
        else:
            cmdline = [operation, input_filename]

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid
        codeinfo.cmdline_params = cmdline
        codeinfo.stdout_name = self._OUTPUT_FILE
        codeinfo.stderr_name = self._ERROR_FILE

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]

        # Symlink mode fields if doing postprocess
        if "mode_fields" in self.inputs:
            calcinfo.remote_symlink_list = [
                (self.inputs.mode_fields.computer.uuid,
                 self.inputs.mode_fields.get_remote_path(),
                 "omega3p_results"),
            ]

        # Retrieve outputs
        calcinfo.retrieve_list = [self._OUTPUT_FILE, self._ERROR_FILE]
        if operation == "meshconvert":
            calcinfo.retrieve_list.append("*.ncdf")
        elif "postprocess" in operation:
            calcinfo.retrieve_list.append("*.dat")

        return calcinfo
