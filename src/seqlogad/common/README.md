# Common

Shared contracts used by data and future scientific/delivery layers.

Input: configuration and domain records.

Output: validated schemas, configuration objects and common logging conventions.

Dependencies: Pydantic, PyYAML and standard library.

Implemented: `checksum.py`, `schemas/events.py`, and `schemas/sequences.py` contracts. Planned: shared config/logging helpers needed by approved core tasks.

Implementation status: checksum and schema contracts implemented; remaining helpers are placeholders.
