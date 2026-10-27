import typing as t
from pathlib import Path

import pydantic
from aind_behavior_vr_foraging import data_qc
from aind_contraqctor_to_schema_export import build_quality_control, results_to_metrics
from aind_data_schema.core.quality_control import QualityControl
from contraqctor import qc


def to_ads(
    results: t.Dict[str | None, t.List[qc.Result]], cli_args: "QCCli"
) -> QualityControl:
    """Convert contraqctor runner results into an aind-data-schema QualityControl.

    Conversion is shared with dynamic foraging via aind-contraqctor-to-schema-export:
    metrics are named "<test>:<group>" (plus ":<n>" for a test that yields several
    results), tagged {"type": "Harp QC Suite", "group": <group>}, keep any figure
    (saved under cli_args.asset_path) and context the test reports, and are all
    allowed to fail without failing the session.
    """
    asset_path = Path(cli_args.asset_path)
    asset_path.mkdir(parents=True, exist_ok=True)
    return build_quality_control(results_to_metrics(results, str(asset_path)))


class QCCli(data_qc.DataQcCli):
    qc_json_path: Path = pydantic.Field(
        default=Path("qc.json"),
        description="Path to export the QC results in ADS format. If not provided, results will not be exported.",
    )
    asset_path: Path = pydantic.Field(
        default=Path("."),
        description="Path to the asset root directory. If not provided, the current working directory will be used.",
    )
