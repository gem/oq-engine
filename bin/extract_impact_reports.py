import sys
import subprocess
import shutil
from pathlib import Path
from openquake.commonlib import datastore


def main(calc_id: int):
    dstore = datastore.read(calc_id)
    if "impact" not in dstore:
        raise RuntimeError("No 'impact' group found in datastore")
    impact_group = dstore["impact"]
    iso3_codes = list(impact_group.keys())
    if not iso3_codes:
        raise RuntimeError("No ISO3 reports found under 'impact/'")
    print(f"Found ISO3 reports: {iso3_codes}")
    for iso3 in iso3_codes:
        country_group = impact_group[iso3]
        for file_format in ("pdf", "png"):
            report_name = f"report_{file_format}"
            if report_name not in country_group:
                print(f"No {report_name} found for {iso3}")
                continue
            report_bytes = country_group[report_name][()]
            fname = Path(
                f"impact_report_{calc_id}_{iso3}.{file_format}")
            with open(fname, "wb") as f:
                f.write(report_bytes)
            print(f"Wrote {fname}")
            if shutil.which("xdg-open"):
                subprocess.Popen(["xdg-open", str(fname)])
    dstore.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: extract_impact_reports.py <calc_id>")
        sys.exit(1)

    main(int(sys.argv[1]))
