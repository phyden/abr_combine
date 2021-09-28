from setuptools import setup, find_packages
import os
from abr_combine.version import get_version

version_df = get_version(force=True)
version_df.to_csv("abr_combine/versions.csv", sep="\t", header=None, index=None)

files_resfinder = []
for dbfile in os.listdir("ext/db_resfinder"):
    if dbfile not in [".git",".gitignore","README.md","INSTALL.py","CHECK-entries.sh"]:
        files_resfinder.append(f"ext/db_resfinder/{dbfile}")

data_files = [("ext/db_resfinder", files_resfinder),
              ("abr_combine", ["abr_combine/versions.csv"])]

files_pointfinder = []
for dbfile in os.listdir("ext/db_pointfinder"):
    if dbfile in [".git", ".gitignore", "INSTALL.py", "README.md"]:
        continue
    if os.path.isdir(f"ext/db_pointfinder/{dbfile}"):
        data_files.append((f"ext/db_pointfinder/{dbfile}", [f"ext/db_pointfinder/{dbfile}/{db}" for db in os.listdir(f"ext/db_pointfinder/{dbfile}")]))
    else:
        files_pointfinder.append(f"ext/db_pointfinder/{dbfile}")

data_files.append(("ext/db_pointfinder", files_pointfinder))

print(data_files)

setup (
      name = "abr_combine",
      version = 0.1,
      description = "Combination of Antimicrobial Resistance Detection Tools",
      author = "Patrick Hyden",
      author_email = "patrick.hyden@ages.at",
      packages = ["abr_combine","ext","cge"],
      package_dir = {"cge": "ext/resfinder/cge"},
      package_data = {"cge": ["out/*", "output/*", "phenotype2genotype/*", "out/util/*"]},
      data_files = data_files,
      include_package_data=True,
      scripts = ["run_tools.py","ext/resfinder/run_resfinder.py","combine_reports.py", "combine_view_with_style.py"],
      long_description = """This tool provides a consensus prediction of up to three tools of the group [NCBIAMRFinder, CARD-RGI and CGE-ResFinder].""",
      license = "",
      platforms = "Linux, Mac OS X"
)
