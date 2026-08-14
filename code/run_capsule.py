import json
import logging
import os

from aind_behavior_vr_foraging.data_qc import data_qc
from aind_behavior_vr_foraging.data_contract import dataset
from log_schema import setup_logging
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from qc_exporter import to_ads, QCCli


class VRForagingSettings(BaseSettings, cli_parse_args=True):
    """
    Settings for VR Foraging Primary Data NWB Packaging
    """

    input_directory: Path = Field(
        default=Path("/data/"), description="Directory where data is"
    )
    output_directory: Path = Field(
        default=Path("/results/"), description="Output directory"
    )

def run() -> None:
    """
    Entrypoint for executing
    """
    settings = VRForagingSettings()
    primary_data_path = tuple(settings.input_directory.glob("*"))
    if not primary_data_path:
        raise FileNotFoundError("No primary data asset attached")

    if len(primary_data_path) > 1:
        raise ValueError(
            "Multiple primary data assets attached. Only single asset needed"
        )

    with open(primary_data_path[0] / "data_description.json") as f:
        data_description = json.load(f)

    ### logging setup
    acquisition_name = data_description["name"]
    process_name = os.getenv("PROCESS_NAME", "primary-qc-vr-foraging")
    pipeline_name = os.getenv("PIPELINE_NAME", "")
    setup_logging(
        (Path(__file__).parent / "logging.yml").as_posix(),
        model={
            "acquisition_name": acquisition_name,
            "process_name": process_name,
            "pipeline_name": pipeline_name    
        },
    )
    logging.info("Begin processing...", extra={"event_type": "stage_start"})
    logging.info(f"Running qc on asset {acquisition_name}")
    # pull version from here - file always assumed to exist at that path
    task_input_logic_path = (
        primary_data_path[0] / "behavior" / "Logs" / "tasklogic_input.json"
    )
    if not task_input_logic_path.exists():
        raise FileNotFoundError(
            f"No task logic input file found at path {task_input_logic_path}"
        )

    with open(task_input_logic_path, "r") as f:
        task_input_logic = json.load(f)

    contract_version = task_input_logic["version"]
    logging.info(f"Using data contract version {contract_version}")
    parsed_args = QCCli(
        data_path=primary_data_path[0], qc_json_path=settings.output_directory, asset_path=settings.output_directory / "raw_qc"
    )
    vr_dataset = dataset(parsed_args.data_path)

    runner = data_qc.make_qc_runner(vr_dataset)
    results = runner.run_all_with_progress()
    qc_json = to_ads(results, parsed_args)
    if parsed_args.qc_json_path is not None:
        with open(parsed_args.qc_json_path / "quality_control.json", "w", encoding="utf-8") as f:
            f.write(qc_json.model_dump_json(indent=2))
    
    logging.info(f"Finished qc. Output saved to {settings.output_directory}")
    logging.info("Pipeline stage completed", extra={"event_type": "stage_complete"})

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.exception("Pipeline stage failed", extra={"event_type": "stage_error"})

