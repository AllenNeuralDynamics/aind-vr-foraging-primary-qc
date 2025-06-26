from aind_behavior_vr_foraging import data_qc
from pathlib import Path
from qc_exporter import to_ads, QCCli

if __name__ == "__main__":
    path = Path("/root/capsule/data/behavior_789923_2025-05-13_16-16-16")
    parsed_args = QCCli(
        data_path=path, qc_json_path=Path("/results"), asset_path=Path("/results")
    )
    vr_dataset = data_qc.dataset(parsed_args.data_path)

    runner = data_qc.make_qc_runner(vr_dataset)
    results = runner.run_all_with_progress()
    qc_json = to_ads(results, parsed_args)
    if parsed_args.qc_json_path is not None:
        with open(parsed_args.qc_json_path, "w", encoding="utf-8") as f:
            f.write(qc_json.model_dump_json(indent=2))
