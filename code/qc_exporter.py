import itertools
import os
import numpy as np
import typing as t
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pydantic
from aind_data_schema.core.quality_control import (
    QCMetric,
    QCStatus,
    QualityControl,
    Stage,
    Status,
)
from aind_data_schema_models.modalities import Modality
from contraqctor import qc
from matplotlib.figure import Figure

from aind_behavior_vr_foraging import data_qc

EVALUATOR = "Automated"
NOW = datetime.now(timezone.utc)
s = QCStatus(evaluator=EVALUATOR, status=Status.PASS, timestamp=NOW)
sp = QCStatus(evaluator=EVALUATOR, status=Status.PENDING, timestamp=NOW)


status_converter = {
    qc.Status.PASSED: Status.PASS,
    qc.Status.SKIPPED: Status.PASS,
    qc.Status.WARNING: Status.PENDING,
    qc.Status.FAILED: Status.FAIL,
    qc.Status.ERROR: Status.FAIL,
}


def convert_numpy_to_python_data_type(obj):
    """
    Serializes numpy to python
    types for writing to json
    """
    if isinstance(obj, dict):
        return {k: convert_numpy_to_python_data_type(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_python_data_type(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

def result_to_qc_metric(
    result: qc.Result, name, create_assets: bool = False, asset_root: os.PathLike = Path(".")
) -> t.Optional[QCMetric]:
    status = QCStatus(
        evaluator=EVALUATOR, status=status_converter[result.status], timestamp=NOW
    )

    return QCMetric(
        name=f"{result.suite_name}::{result.test_name}",
        description=f"Test: {result.description} // Message: {result.message}",
        value=convert_numpy_to_python_data_type(result.result),
        status_history=[status],
        reference=_resolve_reference(result, asset_root) if create_assets else None,
        modality=Modality.BEHAVIOR,
        stage=Stage.PROCESSING,
        tags=[name]
    )


def _resolve_reference(
    result: qc.Result, asset_root: os.PathLike = Path(".")
) -> t.Optional[str]:
    if not isinstance(result.context, dict):
        return None
    asset = result.context.get("asset", None)
    if isinstance(asset, qc._context_extensions.ContextExportableObj):
        if isinstance(asset.asset, Figure):
            random_hash = uuid.uuid4().hex
            path = f"{result.suite_name}_{result.test_name}_{random_hash}.png"
            if not Path(asset_root).exists():
                Path(asset_root).mkdir()
            asset.asset.savefig(Path(asset_root) / path)
            return (Path(asset_root.stem) / path).as_posix()
    return None


def to_ads(
    results: t.Dict[str | None, t.List[qc.Result]], cli_args: "QCCli"
) -> QualityControl:
    qc_metrics = []
    for group_name, group in results.items():
        groupby_test_suite = itertools.groupby(group, lambda x: x.suite_name)
        for suite_name, test_results in groupby_test_suite:
            if not test_results:
                continue
            _test_results = list(test_results)
            name = f"{group_name if group_name else 'NoGroup'}::{suite_name}"
            metrics = [
                result_to_qc_metric(
                    r, name, create_assets=True, asset_root=cli_args.asset_path
                )
                for r in _test_results
            ]
            metrics = [m for m in metrics if m is not None]
            qc_metrics.extend(metrics)

    qc_tags = set()
    for metric in qc_metrics:
        for tag in metric.tags:
            qc_tags.add(tag)

    return QualityControl(metrics=qc_metrics, default_grouping=list(qc_tags))


class QCCli(data_qc.DataQcCli):
    qc_json_path: Path = pydantic.Field(
        default=Path("qc.json"),
        description="Path to export the QC results in ADS format. If not provided, results will not be exported.",
    )
    asset_path: Path = pydantic.Field(
        default=Path("."),
        description="Path to the asset root directory. If not provided, the current working directory will be used.",
    )
