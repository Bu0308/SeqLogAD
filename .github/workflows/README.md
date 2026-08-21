# CI workflows

`ci.yml` is the minimal active workflow. It uses Python 3.12, installs the project with `requirements.lock` as constraints, runs `pip check`, and runs the full pytest suite. It does not download datasets, parse logs, execute experiments, or access TEST.
