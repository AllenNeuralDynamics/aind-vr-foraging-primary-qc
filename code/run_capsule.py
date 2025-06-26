from aind_behavior_vr_foraging import data_qc, data_qc_ads_exporter
from pathlib import Path

if __name__ == '__main__':
    path = Path('/root/capsule/data/behavior_789923_2025-05-13_16-16-16')
    parsed_args = data_qc_ads_exporter._QCCli(data_path=path, qc_json_path=Path('/results'), asset_path=Path('/results'))
    vr_dataset = data_qc.dataset(parsed_args.data_path)

    runner = data_qc.make_qc_runner(vr_dataset)
    results = runner.run_all_with_progress()
    qc_json = data_qc_ads_exporter.to_ads(results, parsed_args)
    with open('/results/quality_control.json', 'w') as f:
        f.write(qc_json.model_dump_json(indent=2))