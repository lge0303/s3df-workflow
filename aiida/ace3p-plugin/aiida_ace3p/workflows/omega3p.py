"""WorkGraph for full Omega3P pipeline: mesh-convert → solve → postprocess."""

from aiida import orm
from aiida.engine import WorkChain, ToContext, if_
from aiida.plugins import CalculationFactory

Omega3pCalculation = CalculationFactory("ace3p.omega3p")
AcdtoolCalculation = CalculationFactory("ace3p.acdtool")


class Omega3pWorkflow(WorkChain):
    """Complete Omega3P eigenmode workflow with provenance.

    Pipeline: mesh conversion → eigenmode solve → RF post-processing

    Every step is automatically recorded in the AiiDA provenance graph.
    Given any final output, the full lineage of inputs and calculations
    can be traced back.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        # Inputs
        spec.input("mesh_file", valid_type=orm.SinglefileData, help="Input mesh (.gen)")
        spec.input("solver_parameters", valid_type=orm.Dict, help="Omega3P solver config")
        spec.input("postprocess_file", valid_type=orm.SinglefileData, required=False, help=".rfpost file")
        spec.input("acdtool_code", valid_type=orm.AbstractCode, help="acdtool code")
        spec.input("omega3p_code", valid_type=orm.AbstractCode, help="omega3p code")
        spec.input("surface_material", valid_type=orm.Dict, required=False)

        # Workflow outline
        spec.outline(
            cls.convert_mesh,
            cls.run_omega3p,
            if_(cls.should_postprocess)(cls.run_postprocess),
            cls.collect_results,
        )

        # Outputs
        spec.output("eigenvalues", valid_type=orm.Dict)
        spec.output("mesh_ncdf", valid_type=orm.SinglefileData, required=False)
        spec.output("rf_results", valid_type=orm.Dict, required=False)

        # Exit codes
        spec.exit_code(301, "ERROR_MESH_CONVERSION", "Mesh conversion failed")
        spec.exit_code(302, "ERROR_SOLVER_FAILED", "Omega3P solver failed")
        spec.exit_code(303, "ERROR_POSTPROCESS_FAILED", "Post-processing failed")

    def convert_mesh(self):
        """Step 1: Convert .gen mesh to .ncdf format using acdtool."""
        self.report("Converting mesh to NetCDF format")

        inputs = {
            "code": self.inputs.acdtool_code,
            "operation": orm.Str("meshconvert"),
            "input_file": self.inputs.mesh_file,
            "metadata": {"options": {"resources": {"num_machines": 1, "num_mpiprocs_per_machine": 1}}},
        }
        calc = self.submit(AcdtoolCalculation, **inputs)
        return ToContext(mesh_convert=calc)

    def run_omega3p(self):
        """Step 2: Run Omega3P eigenmode solver."""
        self.report("Running Omega3P eigenmode solver")

        mesh_calc = self.ctx.mesh_convert
        if not mesh_calc.is_finished_ok:
            return self.exit_codes.ERROR_MESH_CONVERSION

        inputs = {
            "code": self.inputs.omega3p_code,
            "mesh": mesh_calc.outputs.output_file,
            "parameters": self.inputs.solver_parameters,
        }
        if "surface_material" in self.inputs:
            inputs["surface_material"] = self.inputs.surface_material

        calc = self.submit(Omega3pCalculation, **inputs)
        return ToContext(omega3p=calc)

    def should_postprocess(self):
        """Check if post-processing was requested."""
        return "postprocess_file" in self.inputs

    def run_postprocess(self):
        """Step 3: Extract RF parameters from mode fields."""
        self.report("Running RF post-processing")

        omega3p_calc = self.ctx.omega3p
        if not omega3p_calc.is_finished_ok:
            return self.exit_codes.ERROR_SOLVER_FAILED

        inputs = {
            "code": self.inputs.acdtool_code,
            "operation": orm.Str("postprocess rf"),
            "input_file": self.inputs.postprocess_file,
            "mode_fields": omega3p_calc.outputs.remote_results,
        }
        calc = self.submit(AcdtoolCalculation, **inputs)
        return ToContext(postprocess=calc)

    def collect_results(self):
        """Collect outputs from all steps."""
        omega3p_calc = self.ctx.omega3p
        if not omega3p_calc.is_finished_ok:
            return self.exit_codes.ERROR_SOLVER_FAILED

        self.out("eigenvalues", omega3p_calc.outputs.eigenvalues)

        if "postprocess" in self.ctx:
            pp_calc = self.ctx.postprocess
            if pp_calc.is_finished_ok and "results" in pp_calc.outputs:
                self.out("rf_results", pp_calc.outputs.results)

        self.report("Omega3P workflow complete")
