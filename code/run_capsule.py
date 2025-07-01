import logging
from aind_behavior_vr_foraging import data_qc
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings
from qc_exporter import to_ads, QCCli

logger = logging.getLogger(__name__)

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

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    settings = VRForagingSettings()
    primary_data_path = tuple(settings.input_directory.glob("*"))
    if not primary_data_path:
        raise FileNotFoundError("No primary data asset attached")

    if len(primary_data_path) > 1:
        raise ValueError(
            "Multiple primary data assets attached. Only single asset needed"
        )

    logger.info(f"Running qc on primary data at path {primary_data_path[0]}")
    parsed_args = QCCli(
        data_path=primary_data_path[0], qc_json_path=settings.output_directory, asset_path=settings.output_directory
    )
    vr_dataset = data_qc.dataset(parsed_args.data_path)

    runner = data_qc.make_qc_runner(vr_dataset)
    results = runner.run_all_with_progress()
    qc_json = to_ads(results, parsed_args)
    if parsed_args.qc_json_path is not None:
        with open(parsed_args.qc_json_path / "quality_control.json", "w", encoding="utf-8") as f:
            f.write(qc_json.model_dump_json(indent=2))
    
    logger.info(f"Finished qc. Output saved to {settings.output_directory}")
